"""
educube.py


"""
import os
import copy
import time
import serial
import tempfile
from threading import Thread, Lock
from math import fabs

import logging
logger = logging.getLogger(__name__)

from educube.util.telemetry_parser import TelemetryParser
parser = TelemetryParser()   # should this be a) replaced by a function or b)
                             # an object attribute of the EducubeConnection
                             # object?

def millis():
    """Current system time in milliseconds."""
    return int(round(time.time() * 1000))


class EducubeConnectionError(Exception):
    """Exception to be raised for errors when communicating with EduCube."""


class EducubeConnectionThread(Thread):
    """Thread that records and requests telemetry on serial port."""
    def __init__(self, master, eol=b'\r\n'):
        """
        Constructor

        Parameters
        ----------
        master : EducubeConnection
            The controlling interface to the EduCube 
        eol : bytes

        """
        self.master = master
        self.eol = eol
        Thread.__init__(self)

    def run(self): 
        """. """
        _buffer = bytearray()

        while self.master.running:
            # check whether there is any telemetry to pick up
            if self.master.connection.in_waiting:
#                _buffer = self.master.connection.readline()
#                telem = (millis(), bytes(_buffer))
#                self.master.telemetry_buffer.append(telem)
#                logger.debug("Received telemetry: {time} : {data}"\
#                             .format(time=telem[0],data=telem[1])  )

                _buffer.extend(self.master.connection.read())
                if _buffer.endswith(self.eol):
                    if is_telemetry(_buffer):
                        telem = (millis(), bytes(_buffer))
                        self.master.telemetry_buffer.append(telem)
                        logger.debug("Received telemetry: {time} : {data}"\
                                     .format(time=telem[0],data=telem[1])  )
                    elif is_debug(_buffer):
                        logmsg = ("Received {board} DEBUG message:\n"
                                  "        ==> {buffer}"
                                  ).format(board=self.master.board_id,
                                           buffer=_buffer)
                        logger.debug(logmsg)
                    else:
                        logmsg = ("Received unrecognised message\n"
                                  "        ==> {buffer}"
                                  ).format(buffer=_buffer)
                        logger.warning(logmsg)

                    _buffer = bytearray()

            # check whether it is time to ask for more telemetry
            if (time.time() - self.master.last_telem_request 
                    > self.master.telem_request_interval_s  ):
                self.master.send_request_telem()

        logger.info("EducubeConnectionThread.run has ended")

def is_telemetry(buffer):
    return buffer.lstrip().startswith(b'T|')

def is_debug(buffer):
    return buffer.lstrip().startswith(b'DEBUG|')

class EducubeConnection():
    """
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
    telem_log_format = "{timestamp}\t{telemetry}\n"

    _conn_type = 'data'    # this is almost unnecessary -- it is only included
                           # so that, in principle, fake connections can
                           # easily be given a different default name.

    def __init__(self, portname, board, baud=9600, timeout=5,
                 output_path=None, telem_request_interval_s=5):
        """
        Constructor. Sets up the EducubeConnection object. 

        Parameters
        ----------
        portname : str
            
        board : str
            
        baud : int
            
        output_path : str

        """

        self.portname = portname
        self.baud = baud
        self.serial_timeout = timeout

        self.board_id = board


        if board not in (self.board_id_EPS, self.board_id_CDH, 
                         self.board_id_EXP, self.board_id_ADC ):
            errmsg = 'Invalid board identifier {board}'.format(board=board)
            raise EducubeConnectionError(errmsg)

        # file to save telemetry
        if output_path:
            self.output_path = output_path
        else:
            outfile = ("educube_telemetry_{type}_{time}.raw"\
                       .format(type=self._conn_type, time=millis()))
            self.output_path = os.path.join( tempfile.gettempdir(), outfile )

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
        logger.info("STARTUP : Setting up Educube connections")

        self.output_file = open(self.output_path, 'a')
        logger.info("STARTUP : Telemetry will be saved to {path}"\
                    .format(path=self.output_path)                )

        self.connection = serial.Serial(self.portname, self.baud, 
                                        timeout=self.serial_timeout)
        logger.info("STARTUP : Opened Serial connection: {ser}"\
                    .format(ser=repr(self.connection))   )

    def teardown_connections(self):
        logger.info("SHUTDOWN : Closing Educube connections")

        self.connection.close()
        logger.info("SHUTDOWN : Closed Serial connection")
        self.output_file.close()
        logger.info("SHUTDOWN : Closed telemetry save file {path}"\
                    .format(path=self.output_path))

    ################
    # thread management
    ################

    def start_thread(self):
        logger.debug("STARTUP : Starting EducubeConnectionThread")
        self.thread = EducubeConnectionThread(self)
        self.running = True
        self.thread.start()
        self.lock = Lock()

    def stop_thread(self):
        logger.debug("SHUTDOWN : Stopping EducubeConnectionThread")
        self.running = False
        self.thread.join()

    ################
    # basic commands
    ################

    def send_command(self, cmd):
        """
        Formats and transmits a command to EduCube

        Parameters
        ----------
        cmd : str
            The command to be sent (e.g., C|CDH|T)

        """
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

        cmd_string = self.telem_log_format\
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

    def send_request_telem(self, board=None):
        """
        Send the telemetry request command 

        Parameters
        ----------
        board : str
            The board identifier (CDH, ADC, EPS or EXP)

        """
        if board is None:
            board = self.board_id

        if board not in [self.board_id_EPS, self.board_id_CDH,
                         self.board_id_EXP, self.board_id_ADC ]:
            errmsg = 'Invalid board identifier {board}'.format(board=board)
            raise EducubeConnectionError(errmsg)

        logger.debug("Requesting telemetry from board {id}".format(id=board))

        cmd = 'C|{board}|T'.format(board=board)
        self.send_command(cmd)

        # update last_telem_request time
        self.last_telem_request = time.time()

    def send_set_blinky(self):
        """
        Light Educube up like a Christmas Tree!
        """
        cmd = 'C|CDH|BLINKY'
        self.send_command(cmd)

    def send_set_magtorquer(self, axis, sign):
        """
        Send command to turn magnetorquer on/off.

        Parameters
        ----------
        axis : str
            Sets the magnetorquer axis ('X' or 'Y')
        sign : int or str
            Sets final status of magnetorquer. Allowed values are 
            ('-', '0', '+') or (-1, 0, 1)

        """
        if axis.upper() not in ('X', 'Y'):
            errmsg = ('Invalid axis input for magnetorquer: '
                      +'{axis} not in (\'X\', \'Y\')'.format(axis=axis))
            raise EducubeConnectionError(errmsg)

        if sign in (0, '0'):
            sign = '0'
        elif sign in (1, '+'):
            sign = '+'
        elif sign in (-1, '-'):
            sign = '-'
        else:
            errmsg = ('Invalid input for {axis} magnetorquer: {sign}'\
                      .format(axis=axis.upper(), sign=sign)           )
            raise EducubeConnectionError(errmsg)

        cmd = 'C|ADC|MAG|{axis}|{sign}'.format(axis=axis.upper(),sign=sign)
        self.send_command(cmd)

    def send_set_reaction_wheel(self, val):
        """
        Send command to set reaction wheel.

        Parameters
        ----------
        val : int
            Reaction wheel power value as a percentage

        """
        if val < -100 or val > 100:
            errmsg = ('Invalid input for reaction wheel {val} '
                      +'(should be -100 <= val <= 100)'.format(val=val))
            raise EducubeConnectionError(errmsg)

        cmd = ('C|ADC|REACT|{sgn}|{mag}'\
               .format(sgn=('+' if val >= 0 else '-'),
                       mag=int(fabs(val))             ))
        self.send_command(cmd)

    def send_set_thermal_panel(self, panel, val):
        """
        Send command to set thermal panel.

        Parameters
        ----------
        panel : int
            Thermal panel number 
        val : int
            Thermal panel power value as a percentage

        """
        if panel not in (1,2):
            errmsg = ('Invalid input for thermal experiment: panel {panel} '
                      +'(panel must be in [1,2])'.format(panel=panel))
            raise EducubeConnectionError(errmsg)

        if val < 0 or val > 100:
            errmsg = ('Invalid input for thermal experiment val {val} '
                      +'(val should be between 0 and 100)'.format(val=val))
            raise EducubeConnectionError(errmsg)

        cmd = 'C|EXP|HEAT|{panel}|{val}'.format(panel=panel, val=val)
        self.send_command(cmd)


    ################
    # methods to return telemetry
    ################

    def read_telemetry_buffer(self):
        """."""
        with self.lock:   # is this lock needed???
            raw_telemetry = copy.deepcopy(self.telemetry_buffer)
            self.telemetry_buffer = []
        self._write_telemetry_to_file(raw_telemetry)
        return raw_telemetry

    # NEED TO HANDLE DECODING ERRORS ROBUSTLY???       
    def _write_telemetry_to_file(self, telemetry_buffer):
        """."""
        for _timestamp, _telemetry_bytes in telemetry_buffer:
            self.output_file.write(self.telem_log_format.format(
                timestamp = _timestamp                              ,
                telemetry = _telemetry_bytes.decode('utf-8').strip() ))

    # WHAT ABOUT UNCAUGHT PARSING ERRORS???
    def parse_telemetry(self):
        """."""
        _raw_telemetry = self.read_telemetry_buffer()

        parsed_telemetry = [
            parser.parse_telemetry(_timestamp                      , 
                                   _telemetry_bytes.decode('utf-8') ) 
            for _timestamp, _telemetry_bytes in _raw_telemetry       ]
 
        return parsed_telemetry

 

##############################################################################

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


##############################################################################

def get_connection(connection_params):
    logger.info("Creating educube connection")
    if connection_params['fake']:
        educube_connection = FakeEducubeConnection(
            connection_params['port'],
            connection_params['board'],
            baud=connection_params['baud']
        )
    else:
        educube_connection = EducubeConnection(
            connection_params['port'],
            connection_params['board'],
            baud=connection_params['baud'],
        )
    return educube_connection

