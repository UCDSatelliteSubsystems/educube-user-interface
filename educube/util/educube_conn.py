import os
import copy
import time
import serial
import tempfile
from threading import Thread, Lock
from math import fabs

import logging
logger = logging.getLogger(__name__)

#from collections import namedtuple
#MagtorquerValues = namedtuple('MagtorquerValues', ['PLUS', 'OFF', 'MINUS'])
#MAG = MagtorquerValues(PLUS=1, OFF=0, MINUS=-1)

#connections = []

def millis():
    """Current system time in milliseconds."""
    return int(round(time.time() * 1000))


class EducubeError(Exception):
    """
    An exception to be raised if errors are encountered in communicating with
    the Educube.
    """

class EducubeConnectionThread(Thread):
    """Thread that records and requests telemetry on serial port."""
    def __init__(self, master):
        """."""
        self.master = master
        Thread.__init__(self)

    def run(self): 
        """."""
        while self.master.running:
            self.master.read_telem()
            if (time.time() - self.master.last_telem_request 
                    > self.master.telem_request_interval_s  ):
                self.master.send_request_telem()

        logger.info("EducubeConnectionThread.run has ended")


class EducubeConnection():
    """\
    Serial interface to send commands to and receive telemetry from an EduCube.

    """    
    syntax_command_start = '['
    syntax_command_end = ']'
    syntax_command = 'C'
    syntax_sep = '|'

    board_id_EPS = 'EPS'
    board_id_CDH = 'CDH'
    board_id_EXP = 'EXP'
    board_id_ADC = 'ADC'

    telem_request_command = 'T'

    last_telem_request = 0
    telemetry_buffer = []
    telem_raw_format = "{timestamp}\t{telemetry}\n"

    def __init__(self, conn_type, portname, board, baud=9600, fake=False,
                 output_path=None, read_interval_s=5, 
                 telem_request_interval_s=5):
        """
        Constructor

        Sets up the EducubeConnection object. 
        """
        self.conn_type = conn_type
        self.portname = portname
        self.baud = baud
        self.board_id = board
        self.timeout=.5

        if board not in [self.board_id_EPS, self.board_id_CDH, 
                         self.board_id_EXP, self.board_id_ADC ]:
            errmsg = 'Invalid board identifier {board}'.format(board=board)
            raise RuntimeError(errmsg)

        if output_path:
            self.output_path = output_path
        else:
            outfile = ("educube_telemetry_{type}_{time}.raw"\
                       .format(type=self.conn_type, time=millis()) )
            self.output_path = os.path.join( tempfile.gettempdir(), outfile )

        self.read_interval_s = read_interval_s
        self.telem_request_interval_s = telem_request_interval_s
        self.running = False

    ################
    # context manager
    ################

    def __enter__(self):
        self.setup_connections()
        self.start_thread()
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        self.stop_thread()
        self.teardown_connections()
        return False

    ################
    # setup/teardown
    ################

    def setup_connections(self):
        logger.info("Setting up Educube connections")

        self.output_file = open(self.output_path, 'a')
        logger.info("Telemetry will be saved to {path}"\
                    .format(path=self.output_path)       )

        self.connection = serial.Serial(self.portname, self.baud, timeout=3)
        logger.info("Serial connection: {ser}"\
                    .format(ser=repr(self.connection)))

    def teardown_connections(self):
        logger.info("Closing Educube connections")

        self.connection.close()
        logger.info("Closed Serial connection")
        self.output_file.close()
        logger.info("Closed telemetry save file {path}"\
                    .format(path=self.output_path))

    ################
    # thread management
    ################

    def start_thread(self):
        logger.debug("Starting EducubeConnectionThread")
        self.thread = EducubeConnectionThread(self)
        self.running = True
        self.thread.start()
        self.lock = Lock()

    def stop_thread(self):
        logger.debug("Stopping EducubeConnectionThread")
        self.running = False
        self.thread.join()

    ################
    # basic commands
    ################

    def read_telem(self):

        if self.connection.in_waiting:
            telem_data = self.connection.readline().strip()
            telem = (millis(), telem_data)
            self.telemetry_buffer.append(telem)
            logger.debug("Received telemetry: {time} : {data}"\
                         .format(time=telem[0],data=telem[1])  )
#        while self.connection.inWaiting() > 0:
#            telem_data = self.connection.readline().strip()
#            telem = (millis(), telem_data)
#            self.telemetry_buffer.append(telem)
#            logger.debug("Received telemetry: {time} : {data}"\
#                         .format(time=telem[0],data=telem[1])  )

    def send_request_telem(self, board=None):
        """
        Send the telemetry request command [C|CDH|T]

        """
        logger.debug("Requesting telemetry from board {id}"\
                     .format(id=self.board_id)              )
        command = self.format_command(self.telem_request_command)
        self.send_command(command)
        # update last_telem_request time
        self.last_telem_request = time.time()


    def send_command(self, cmd):
        cmd_structure = ('{cmd_start}{cmd}{cmd_end}'\
                         .format(cmd_start=str(self.syntax_command_start),
                                 cmd_end=str(self.syntax_command_end)    ,
                                 cmd=str(cmd)                             ))

        logger.info("Writing command: '{cmd}'".format(cmd=cmd_structure))

        try:
            self.connection.write(str.encode(cmd_structure))
            self.connection.flush()
        except:
            errmsg = "Encountered Error while sending command", 
            logger.exception(errmsg, exc_info=True)

        cmd_string = self.telem_raw_format\
            .format(timestamp=millis(),
                    telemetry="COMMAND_SENT: {cmd}".format(cmd=cmd_structure))
        try:
            self.output_file.write(cmd_string)
        except:
            errmsg = "Encountered Error while logging sent command to file"
            logger.exception(errmsg, exc_info=True)

    ################
    # specific commands
    ################

    def send_set_blinky(self):
        """\
        Light Educube up like a Christmas Tree!
        """
        cmd = 'C|CDH|BLINKY'
        self.send_command(cmd)

    def send_set_magtorquer(self, axis, sign):
        """\
        Send command to turn magnetorquer on/off.
        
        """
        if axis.upper() not in ('X', 'Y'):
            errmsg = ('Invalid axis input for magnetorquer: '
                      +'{axis} not in (\'X\', \'Y\')'.format(axis=axis))
            raise EducubeError(errmsg)

        if sign in (0, '0'):
            sign = '0'
        elif sign in (1, '+'):
            sign = '+'
        elif sign in (-1, '-'):
            sign = '-'
        else:
            errmsg = ('Invalid input for {axis} magnetorquer: {sign}'\
                      .format(axis=axis.upper(), sign=sign)           )
            raise EducubeError(errmsg)

        cmd = 'C|ADC|MAG|{axis}|{sign}'.format(axis=axis.upper(),sign=sign)
        self.send_command(cmd)

    def send_set_reaction_wheel(self, val):
        """\
        Send command to set reaction wheel.

        """
        if val < -100 or val > 100:
            errmsg = ('Invalid input for reaction wheel {val} '
                      +'(should be -100 <= val <= 100)'.format(val=val))
            raise EducubeError(errmsg)

        cmd = ('C|ADC|REACT|{sgn}|{mag}'\
               .format(sgn=('+' if val >= 0 else '-'),
                       mag=int(fabs(val))             ))
        self.send_command(cmd)

    def send_set_thermal_panel(self, panel, val):
        """\
        Send command to set thermal panel.
        """
        if panel not in (1,2):
            errmsg = ('Invalid input for thermal experiment: panel {panel} '
                      +'(panel must be in [1,2])'.format(panel=panel))
            raise EducubeError(errmsg)

        if val < 0 or val > 100:
            errmsg = ('Invalid input for thermal experiment val {val} '
                      +'(val should be between 0 and 100)'.format(val=val))
            raise EducubeError(errmsg)

        cmd = 'C|EXP|HEAT|{panel}|{val}'.format(panel=panel, val=val)
        self.send_command(cmd)


    ################
    # convenience methods
    ################

    def get_telemetry(self):
        with self.lock:   # is this lock needed???
            telemetry = copy.deepcopy(self.telemetry_buffer)
            self.telemetry_buffer = []
            self.write_telemetry_to_log(telemetry)
        return telemetry

    def format_command(self, cmd, board=None):
        if not board:
            board=self.board_id
            
        formatted_command = '{command_start}{sep}{board}{sep}{command}'.format(
            command_start=str(self.syntax_command),
            sep=str(self.syntax_sep),
            board=str(board),
            command=str(cmd)
            )
        return formatted_command
        
    def write_telemetry_to_log(self, telemetry_buffer):
        for timestamp, telemetry in telemetry_buffer:
            self.output_file.write(self.telem_raw_format.format(
                timestamp = timestamp,
                telemetry = telemetry ))

 

class FakeEducubeConnection(EducubeConnection):

    def setup_connections(self):
        logger.info("Setting up FAKE Educube connections")

        self.output_file = open(self.output_path, 'a')
        fd, filename = tempfile.mkstemp()
        self.connection = os.fdopen(fd, "w")
        logger.debug("Using fake serial connection to: %s" % filename)

    def teardown_connections(self):
        logger.info("Tearing down FAKE Educube connections")

    def send_request_telem(self):
        logger.info("Fake connection: ignoring telem request")



def get_connection(connection):
    logger.info("Starting educube connection")
    if connection['fake']:
        educube_connection = FakeEducubeConnection(
            connection['type'],
            connection['port'],
            connection['board'],
            baud=connection['baud']
        )
    else:
        educube_connection = EducubeConnection(
            connection['type'],
            connection['port'],
            connection['board'],
            baud=connection['baud'],
        )
    return educube_connection



#def get_connection(connection):
#    global connections
#    logger.info("Starting educube connection")
#    if connection['fake']:
#        educube_connection = FakeEducubeConnection(
#            connection['type'],
#            connection['port'],
#            connection['board'],
#            baud=connection['baud']
#        )
#    else:
#        educube_connection = EducubeConnection(
#            connection['type'],
#            connection['port'],
#            connection['board'],
#            baud=connection['baud'],
#        )
#    educube_connection.start()
#    connections.append(educube_connection)
#    return educube_connection

