"""
_connection.py

Provides interface between the browser app and EduCube via USB serial. 

"""
import logging
import os
import tempfile
import time

from math import fabs
from threading import Thread, Lock

import serial

from educube.util import millis
from educube.telemetry_parser import parse_educube_telemetry

logger = logging.getLogger(__name__)

class EduCubeConnectionError(Exception):
    """Exception to be raised for errors when communicating with EduCube."""


class EduCubeConnectionThread(Thread):
    """Thread that records and requests telemetry on serial port."""
    def __init__(self, master, eol=b'\r\n'):
        """
        Constructor

        Parameters
        ----------
        master : EduCubeConnection
            The controlling interface to the EduCube 
        eol : bytes
            Byte character sequence denoting end-of-line

        """
        self.master = master
        self.eol = eol

        super().__init__()

    def run(self): 
        """Thread loop to listen for messages from EduCube."""
        _buffer = bytearray()

        while self.master.running:
            # check whether there is any telemetry to pick up
            if self.master.connection.in_waiting:
                _buffer.extend(self.master.connection.read())
                # the line terminator can be a multi-character sequence. Check
                # the current buffer against this termination sequence, and
                # process the buffer if line is complete
                if _buffer.endswith(self.eol):
                    self._process_message(bytes(_buffer))
                    _buffer = bytearray()

            # check whether it is time to ask for more telemetry
            if (time.time() - self.master.last_telem_request 
                    > self.master.telem_request_interval_s  ):
                self.master.send_request_telem()

        logger.info("EduCubeConnectionThread.run has ended")

    def _process_message(self, msg):
        """Logs all received complete messages, and stores telemetry."""
        if is_telemetry(msg):
            time = millis()
            telem = (time, msg)

            self.master.telemetry_buffer.append(telem)
            logger.debug("Received telemetry: {time} : {data}"\
                         .format(time=time,data=msg)           )

        elif is_debug(msg):
            logmsg = ("Received {board} DEBUG message:\n"
                      "        ==> {msg}"
                      ).format(board=self.master.board_id,
                               msg=msg)
            logger.debug(logmsg)

        else:
            logmsg = ("Received unrecognised message\n"
                      "        ==> {msg}"
                      ).format(msg=msg)
            logger.warning(logmsg)
        

def is_telemetry(msg):
    return msg.lstrip().startswith(b'T|')

def is_debug(msg):
    return msg.lstrip().startswith(b'DEBUG|')



class EduCubeConnection():
    """
    Serial interface to send commands to and receive telemetry from an EduCube.

    """
    syntax_command_start = '['
    syntax_command_end = ']'
    syntax_command = 'C'
    syntax_sep = '|'

    board_ids = ('EPS', 'CDH', 'EXP', 'ADC')

    telem_request_command = 'T'

    last_telem_request = 0
    telem_log_format = "{timestamp}\t{telemetry}\n"

    telemetry_buffer = []

    _conn_type = 'data'    # this is almost unnecessary -- it is only included
                           # so that, in principle, fake connections can
                           # easily be given a different default name.

    def __init__(self, portname, board, baud=9600, timeout=5,
                 output_path=None, telem_request_interval_s=5):
        """
        Constructor. Sets up the EduCubeConnection object. 

        Parameters
        ----------
        portname : str
            The serial port that EduCube is connected to.
        board : str
            The EduCube board 
        baud : int
            The baud rate for serial communications
        timeout : int
            The serial port timeout (in seconds)
        output_path : str
            Filepath to be used to save telemetry and command logs
        telem_request_interval_s : int 
            Time in seconds between requests for telemetry updates 


        """
        self.portname = portname
        self.baud = baud
        self.serial_timeout = timeout

        if board in self.board_ids:
            self.board_id = board
        else:
            errmsg = 'Invalid board identifier {board}'.format(board=board)
            raise EduCubeConnectionError(errmsg)


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
        logger.info("STARTUP : Setting up EduCube connections")

        self.output_file = open(self.output_path, 'a')
        logger.info("STARTUP : Telemetry will be saved to {path}"\
                    .format(path=self.output_path)                )

        self.connection = serial.Serial(self.portname, self.baud, 
                                        timeout=self.serial_timeout)
        logger.info("STARTUP : Opened Serial connection: {ser}"\
                    .format(ser=repr(self.connection))   )

    def teardown_connections(self):
        logger.info("SHUTDOWN : Closing EduCube connections")

        self.connection.close()
        logger.info("SHUTDOWN : Closed Serial connection")
        self.output_file.close()
        logger.info("SHUTDOWN : Closed telemetry save file {path}"\
                    .format(path=self.output_path))

    ################
    # thread management
    ################

    def start_thread(self):
        logger.debug("STARTUP : Starting EduCubeConnectionThread")
        self.thread = EduCubeConnectionThread(self)
        self.running = True
        self.thread.start()
        self.lock = Lock()

    def stop_thread(self):
        logger.debug("SHUTDOWN : Stopping EduCubeConnectionThread")
        self.running = False
        self.thread.join()

    # ******************************
    # Telemetry & command callbacks
    # ******************************
    # ultimately, the arguments here should probably be changed to something
    # more flexible.  We would then be able to send user input from the UI to
    # do things like change playback rate???
    def process_command(self, board=None, command=None, settings=None):
        """."""
        if command == 'T':
            self.send_request_telem(board=board)
    
        elif board == 'ADC' and command == 'MAG':
            self.send_set_magtorquer(**settings)
    
        elif board == 'ADC' and command == 'REACT':
            self.send_set_reaction_wheel(**settings)
    
        elif board == 'EXP' and command =='HEAT':
            self.send_set_thermal_panel(**settings)
    
        elif board == 'EPS' and command =='PWR_ON':
            self.send_set_chip_power_on(**settings)
    
        elif board == 'EPS' and command =='PWR_OFF':
            self.send_set_chip_power_off(**settings)



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

        _cmd_string = self.telem_log_format\
            .format(timestamp=millis(),
                    telemetry="COMMAND_SENT: {cmd}".format(cmd=cmd_structure))
        try:
            self.output_file.write(_cmd_string)
            print(_cmd_string)
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

        if board not in self.board_ids:
            errmsg = 'Invalid board identifier {board}'.format(board=board)
            raise EduCubeConnectionError(errmsg)

        logger.debug("Requesting telemetry from board {id}".format(id=board))

        cmd = 'C|{board}|T'.format(board=board)
        self.send_command(cmd)

        # update last_telem_request time
        self.last_telem_request = time.time()

    def send_set_blinky(self):
        """
        Light EduCube up like a Christmas Tree!
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
            raise EduCubeConnectionError(errmsg)

        if sign in (0, '0'):
            sign = '0'
        elif sign in (1, '+'):
            sign = '+'
        elif sign in (-1, '-'):
            sign = '-'
        else:
            errmsg = ('Invalid input for {axis} magnetorquer: {sign}'\
                      .format(axis=axis.upper(), sign=sign)           )
            raise EduCubeConnectionError(errmsg)

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
            raise EduCubeConnectionError(errmsg)

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
            raise EduCubeConnectionError(errmsg)

        if val < 0 or val > 100:
            errmsg = ('Invalid input for thermal experiment val {val} '
                      +'(val should be between 0 and 100)'.format(val=val))
            raise EduCubeConnectionError(errmsg)

        cmd = 'C|EXP|HEAT|{panel}|{val}'.format(panel=panel, val=val)
        self.send_command(cmd)

    def send_set_chip_power_on(self, command_id):
        """
        Send command to turn on chip

        Parameters
        ----------
        command_id : 
            

        """
        cmd = 'C|EPS|PWR_ON|{command_id}'.format(command_id=command_id)
        self.send_command(cmd)

    def send_set_chip_power_off(self, command_id):
        """
        Send command to turn off chip

        Parameters
        ----------
        command_id : 


        """
        cmd = 'C|EPS|PWR_OFF|{command_id}'.format(command_id=command_id)
        self.send_command(cmd)


    ################
    # methods to return telemetry
    ################

    def read_telemetry_buffer(self):
        """."""

        with self.lock:   # is this lock needed???
            raw_telemetry = self.telemetry_buffer[:]
            self.telemetry_buffer = []

        self._write_telemetry_to_file(raw_telemetry)
        return raw_telemetry

    # NEED TO HANDLE DECODING ERRORS ROBUSTLY???       
    def _write_telemetry_to_file(self, telemetry_buffer):
        """."""
        for _timestamp, _telemetry_bytes in telemetry_buffer:
            _telemetry_str = self.telem_log_format.format(
                timestamp = _timestamp                              ,
                telemetry = _telemetry_bytes.decode('utf-8').strip() 
            )

            self.output_file.write(_telemetry_str)
            print(_telemetry_str) # THIS IS A TEMPORARY MEASURE TO ALLOW
                                  # IMMEDIATE VIEWING.

    # WHAT ABOUT UNCAUGHT PARSING ERRORS???
    def parse_telemetry(self):
        """."""
        _raw_telemetry = self.read_telemetry_buffer()

        parsed_telemetry = [
            parse_educube_telemetry(_timestamp                      , 
                                    _telemetry_bytes.decode('utf-8') ) 
            for _timestamp, _telemetry_bytes in _raw_telemetry        ]
 
        return parsed_telemetry

 

##############################################################################

class FakeEduCubeConnection(EduCubeConnection):

    def setup_connections(self):
        logger.info("Setting up FAKE EduCube connections")

        self.output_file = open(self.output_path, 'a')
        fd, filename = tempfile.mkstemp()
        self.connection = os.fdopen(fd, "w")
        logger.debug("Using fake serial connection to: %s" % filename)

    def teardown_connections(self):
        logger.info("Tearing down FAKE EduCube connections")

    def send_request_telem(self):
        logger.info("Fake connection: ignoring telem request")


##############################################################################

#def get_connection(connection_params):
#    logger.info("Creating educube connection")
#    if connection_params['fake']:
#        educube_connection = FakeEduCubeConnection(
#            connection_params['port'],
#            connection_params['board'],
#            baud=connection_params['baud']
#        )
#    else:
#        educube_connection = EduCubeConnection(
#            connection_params['port'],
#            connection_params['board'],
#            baud=connection_params['baud'],
#        )
#    return educube_connection

