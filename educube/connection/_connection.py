"""
_connection.py

Provides interface between the browser app and EduCube via USB serial. 

"""
# standard library imports
import logging
import os
import tempfile
#import time

from queue import Queue
#from math import fabs
#from threading import Thread, Lock

# third party imports
import serial

# local imports
from educube.util import millis
#from educube.telemetry_parser import parse_educube_telemetry
from educube.util.threadutils import SchedulerThread
from educube.util.threadutils import ConsumerThread, ProducerConsumerThread
from educube.util.threadutils import ThreadPool
from educube.educube import EduCube
from educube.util.fileutils import OutputFile

logger = logging.getLogger(__name__)

class EduCubeConnectionError(Exception):
    """Exception to be raised for errors when communicating with EduCube."""


#class EduCubeConnectionThread(Thread):
#    """Thread that records and requests telemetry on serial port."""
#    def __init__(self, master, eol=b'\r\n'):
#        """
#        Constructor
#
#        Parameters
#        ----------
#        master : EduCubeConnection
#            The controlling interface to the EduCube 
#        eol : bytes
#            Byte character sequence denoting end-of-line
#
#        """
#        self.master = master
#        self.eol = eol
#
#        super().__init__()
#
#    def run(self): 
#        """Thread loop to listen for messages from EduCube."""
#        _buffer = bytearray()
#
#        while self.master.running:
#            # check whether there is any telemetry to pick up
#            if self.master.connection.in_waiting:
#                _buffer.extend(self.master.connection.read())
#                # the line terminator can be a multi-character sequence. Check
#                # the current buffer against this termination sequence, and
#                # process the buffer if line is complete
#                if _buffer.endswith(self.eol):
#                    self._process_message(bytes(_buffer))
#                    _buffer = bytearray()
#
#            # check whether it is time to ask for more telemetry
#            if (time.time() - self.master.last_telem_request 
#                    > self.master.telem_request_interval_s  ):
#                self.master.send_request_telem()
#
#        logger.info("EduCubeConnectionThread.run has ended")
#
#    def _process_message(self, msg):
#        """Logs all received complete messages, and stores telemetry."""
#        if is_telemetry(msg):
#            time = millis()
#            telem = (time, msg)
#
#            self.master.telemetry_buffer.append(telem)
#            logger.debug(f"Received telemetry: {time} : {msg}")
#
#        elif is_debug(msg):
#            logmsg = ("Received {board} DEBUG message:\n"
#                      "        ==> {msg}"
#                      ).format(board=self.master.board_id,
#                               msg=msg)
#            logger.debug(logmsg)
#
#        else:
#            logmsg = ("Received unrecognised message\n"
#                      "        ==> {msg}"
#                      ).format(msg=msg)
#            logger.warning(logmsg)
        

def is_telemetry(msg):
    return msg.lstrip().startswith(b'T|')

def is_debug(msg):
    return msg.lstrip().startswith(b'DEBUG|')

def format_command(cmd):
    """Return a formatted EduCube command string."""
    return f'[{cmd}]'

def init_serial(portname, baudrate, timeout):
    """Helper function to initialise a new (closed) serial port."""
    port = serial.Serial()

    # configuration
    port.port = portname
    port.baudrate = baudrate
    port.timeout = timeout
    return port


def send_request_telemetry(conn, educube, board='CDH'):
    """Assemble and send a request telemetry command."""
    _cmd = educube.request_telemetry(board)
    return conn.send_command(_cmd)


# functions to handle printing to file and stdout
def write_rx_message(msg, file):
    _msg = f"{timestamp}\t>>>\t{msg}"
    print(_msg)
    return file.writeline(_msg)

def write_tx_message(msg, file):
    _msg = f"{timestamp}\t<<<\t{msg}"
    print(_msg)
    return file.writeline(_msg)


class RXHandler:
    def __init__(self, callback, eol):
        """Initialiser.

        Parameters
        ----------
        callback : callable
            Function applied to the received bytes when line complete
        eol : bytes
            Byte character sequence denoting end-of-line

        """
        
        self.callback = callback
        self.eol = eol
        
        # buffer to store received bytes
        self._rx_buffer = bytearray()

    def update(self, byte):
        """Handle new byte."""
        self._rx_buffer.extend(byte)

        if self._rx_buffer.endswith(self.eol):
            self._callback(bytes(self._rx_buffer))
            self._rx_buffer = bytearray()

    def __call__(self, byte):
        return self.update(byte)

# ****************************************************************************

class EduCubeConnection:
    """
    Serial interface to send commands to and receive telemetry from an EduCube.

    """

#    last_telem_request = 0
    telem_log_format = "{timestamp}\t{telemetry}\n"

#    telemetry_buffer = []

    _conn_type = 'data'    # this is almost unnecessary -- it is only included
                           # so that, in principle, fake connections can
                           # easily be given a different default name.

    def __init__(self, portname, board, baudrate=9600, timeout=5,
                 output_path=None, telemetry_request_interval_s=5):
        """
        Constructor. Sets up the EduCubeConnection object. 

        Parameters
        ----------
        portname : str
            The serial port that EduCube is connected to.
        board : str
            The EduCube board 
        baudrate : int
            The baud rate for serial communications
        timeout : int
            The serial port timeout (in seconds)
        output_path : str
            Filepath to be used to save telemetry and command logs
        telem_request_interval_s : int 
            Time in seconds between requests for telemetry updates 

        """

        # internal EduCube object for command and telemetry parsing
        self.educube = EduCube()
        
        # create but don't open the serial interface 
        self.port = init_serial(portname, baudrate, timeout)

        # check board is valid  
        if board not in self.educube.board_ids:
            raise EduCubeConnectionError(f'Invalid board identifier {board}')

        self.board_id = board

        # file to save telemetry
        if output_path is None:
            _type, _time = self._conn_type, millis()
            _filename = f"educube_telemetry_{_type}_{_time}.raw"
            output_path = os.path.join( tempfile.gettempdir(), _outfile )

        self.output_filepath = output_path
        self.output_file = OutputFile(output_path, 'a')
        
        # thread to send commands
        # optional if we accept blocking transmissions? But potentially
        # necessary if request telemetry is in its own thread?
        self._tx_queue = Queue()
        self._tx_thread = ConsumerThread(
            queue    = self._tx_queue,
            consumer = self.port.write,
            timeout  = 1,
        )

        # thread to receive telemetry. Reads bytes from serial port and
        # handles them by buffering them and then parsing
        self._rx_thread = ProducerConsumerThread(
            producer = self.port.read,
            consumer = RXHandler(self._process_message, b'\r\n'),
        )

        # thread to request telemetry
        self._request_telemetry_thread = SchedulerThread(
            loop     = self._send_request_telemetry,
            interval = telemetry_request_interval_s,
        )

        # thread control
        self._threads = ThreadPool([
            self._tx_thread,
            self._rx_thread,
            self._request_telemetry_thread,
        ])

        
    def _process_message(self, msg):
        """Logs all received complete messages, and stores telemetry."""

        if is_telemetry(msg):
            # decode packet and add timestamp
            timestamp = millis()
            try:
                telemetry_str = msg.decode(encoding=self.encoding).strip()
            except:
                logger.exception(f"Error decoding: {msg!r}", exc_info=True)
            else:
                # write the received telemetry to file and output stream
                write_rx_message(telemetry_str, timestamp, self.output_file)
                
                # parse and store the received packet
                self.educube.update_telemetry(telemetry_str, timestamp)
                logger.debug(f"Received telemetry: {timestamp} : {msg}")

        elif is_debug(msg):
            logger.debug(f"Received {self.board_id} DEBUG message: {msg!r}")

        else:
            logger.warning(f"Received unrecognised message: {msg!r}")
            
    def _send_request_telemetry(self):
        """Assemble and send a telemetry request to the connected board."""
        return send_request_telemetry(self, self.educube, self.board_id)

        
    ################
    # context manager
    ################

    def __enter__(self):
        self.setup_connections()
        self.start_threads()
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        self.stop_threads()
        self.teardown_connections()
        return False

    ################
    # setup/teardown
    ################

    def setup_connections(self):
        logger.info("STARTUP : Setting up EduCube connections")

        self.output_file.open()
        logger.info(
            f"STARTUP : Telemetry will be saved to {self.output_filepath}"
        )

        self.port.open()
        logger.info(f"STARTUP : Opened Serial connection: {self.port!r}")

    def teardown_connections(self):
        logger.info("SHUTDOWN : Closing EduCube connections")

        self.port.close()
        logger.info("SHUTDOWN : Closed Serial connection")

        self.output_file.close()
        logger.info(
            f"SHUTDOWN : Closed telemetry save file {self.output_path}"
        )

    ################
    # thread management
    ################

    def start_threads(self):
        logger.debug("STARTUP : Starting EduCubeConnectionThread")
        self._threads.start()

    def stop_threads(self):
        logger.debug("SHUTDOWN : Stopping EduCubeConnectionThread")
        self._threads.stop()

#    # ******************************
#    # Telemetry & command callbacks
#    # ******************************
#    # ultimately, the arguments here should probably be changed to something
#    # more flexible.  We would then be able to send user input from the UI to
#    # do things like change playback rate???
#    def process_command(self, board=None, command=None, settings=None):
#        """."""
#        if command == 'T':
#            return self.send_request_telem(board=board)
#    
#        if board == 'ADC':
#            if command == 'MAG':
#                return self.send_set_magtorquer(**settings)
#
#            if command == 'REACT':
#                return self.send_set_reaction_wheel(**settings)
#
#        if board == 'EXP':
#            if command =='HEAT':
#                return self.send_set_thermal_panel(**settings)
#    
#        if board == 'EPS':
#            if command =='PWR_ON':
#                return self.send_set_chip_power_on(**settings)
#    
#            if command =='PWR_OFF':
#                return self.send_set_chip_power_off(**settings)

    ################
    # basic commands
    ################
    
    def send(self, msg, encoding='utf-8'):
        """Encode and transmit a message over Serial connection.

        For thread protection, calling the command actually queues the
        message, so it can be transmitted as soon as possible.

        """
        #TODO: logging?

        # encode text to bytes
        _msg_bytes = msg.encode(encoding=encoding)

        # add message to queue for transmission
        self._tx.queue.put(_msg_bytes)
    
    def send_command(self, cmd):
        """
        Formats and transmits a command to EduCube

        Parameters
        ----------
        cmd : str
            The command to be sent (e.g., C|CDH|T)

        """
        _cmd = format_command(cmd)
               
        logger.info(f"Writing command: '{_cmd}'")

        try:
            self.send(_cmd)
        except:
            errmsg = f"Encountered Error while sending command {_cmd}", 
            logger.exception(errmsg, exc_info=True)

#        _cmd_string = self.telem_log_format.format(
#            timestamp = millis(),
#            telemetry = f"COMMAND_SENT: {_cmd}"
#        )
        #TODO: this try...except... isn't necessary if using OutputFile?
        try:
            write_tx_message(_cmd, millis(), self.output_file)
#            self.output_file.write(_cmd_string)
#            print(_cmd_string)
        except:
            errmsg = f"Encountered Error while logging {_cmd} to file"
            logger.exception(errmsg, exc_info=True)

#    ################
#    # specific commands
#    ################
#
#    def send_request_telem(self, board=None):
#        """
#        Send the telemetry request command 
#
#        Parameters
#        ----------
#        board : str
#            The board identifier (CDH, ADC, EPS or EXP)
#
#        """
#        if board is None:
#            board = self.board_id
#
#        if board not in self.board_ids:
#            errmsg = f'Invalid board identifier {board}'
#            raise EduCubeConnectionError(errmsg)
#
#        logger.debug(f"Requesting telemetry from board {board}")
#
#        cmd = f'C|{board}|T'
#        self.send_command(cmd)
#
#        # update last_telem_request time
#        self.last_telem_request = time.time()
#
#    def send_set_blinky(self):
#        """
#        Light EduCube up like a Christmas Tree!
#        """
#        cmd = 'C|CDH|BLINKY'
#        self.send_command(cmd)
#
#    def send_set_magtorquer(self, axis, sign):
#        """
#        Send command to turn magnetorquer on/off.
#
#        Parameters
#        ----------
#        axis : str
#            Sets the magnetorquer axis ('X' or 'Y')
#        sign : int or str
#            Sets final status of magnetorquer. Allowed values are 
#            ('-', '0', '+') or (-1, 0, 1)
#
#        """
#        if axis.upper() not in ('X', 'Y'):
#            errmsg = (
#                'Invalid axis input for magnetorquer: '
#                f'{axis} not in (\'X\', \'Y\')'
#            )
#            raise EduCubeConnectionError(errmsg)
#
#        if sign in (0, '0'):
#            sign = '0'
#        elif sign in (1, '+'):
#            sign = '+'
#        elif sign in (-1, '-'):
#            sign = '-'
#        else:
#            errmsg = ('Invalid input for {axis} magnetorquer: {sign}'\
#                      .format(axis=axis.upper(), sign=sign)           )
#            raise EduCubeConnectionError(errmsg)
#
#        cmd = 'C|ADC|MAG|{axis}|{sign}'.format(axis=axis.upper(),sign=sign)
#        self.send_command(cmd)
#
#    def send_set_reaction_wheel(self, val):
#        """
#        Send command to set reaction wheel.
#
#        Parameters
#        ----------
#        val : int
#            Reaction wheel power value as a percentage
#
#        """
#        if val < -100 or val > 100:
#            errmsg = f'Invalid value {val} for reaction wheel'
#            raise EduCubeConnectionError(errmsg)
#
#        _sgn = '+' if val >= 0 else '-'
#        _mag = int(abs(val))
#
#        cmd = f'C|ADC|REACT|{_sgn}|{_mag}'
#        self.send_command(cmd)
#
#    def send_set_thermal_panel(self, panel, val):
#        """
#        Send command to set thermal panel.
#
#        Parameters
#        ----------
#        panel : int
#            Thermal panel number 
#        val : int
#            Thermal panel power value as a percentage
#
#        """
#        if panel not in (1,2):
#            errmsg = (
#                f'Invalid input for thermal experiment: panel {panel} '
#                +'(panel must be in [1,2])'
#            )
#            raise EduCubeConnectionError(errmsg)
#
#        if val < 0 or val > 100:
#            errmsg = (
#                f'Invalid input for thermal experiment val {val} '
#                +'(val should be between 0 and 100)'
#            )
#            raise EduCubeConnectionError(errmsg)
#
#        cmd = f'C|EXP|HEAT|{panel}|{val}'
#        self.send_command(cmd)
#
#    def send_set_chip_power_on(self, command_id):
#        """
#        Send command to turn on chip
#
#        Parameters
#        ----------
#        command_id : 
#            
#
#        """
#        cmd = f'C|EPS|PWR_ON|{command_id}'
#        self.send_command(cmd)
#
#    def send_set_chip_power_off(self, command_id):
#        """
#        Send command to turn off chip
#
#        Parameters
#        ----------
#        command_id : 
#
#
#        """
#        cmd = f'C|EPS|PWR_OFF|{command_id}'
#        self.send_command(cmd)


#    ################
#    # methods to return telemetry
#    ################
#
#    def read_telemetry_buffer(self):
#        """."""
#
#        with self.lock:   # is this lock needed???
#            raw_telemetry = self.telemetry_buffer[:]
#            self.telemetry_buffer = []
#
#        self._write_telemetry_to_file(raw_telemetry)
#        return raw_telemetry
#
#    # NEED TO HANDLE DECODING ERRORS ROBUSTLY???       
#    def _write_telemetry_to_file(self, telemetry_buffer):
#        """."""
#        for _timestamp, _telemetry_bytes in telemetry_buffer:
#            _telemetry_str = self.telem_log_format.format(
#                timestamp = _timestamp                              ,
#                telemetry = _telemetry_bytes.decode('utf-8').strip() 
#            )
#
#            self.output_file.write(_telemetry_str)
#            print(_telemetry_str) # THIS IS A TEMPORARY MEASURE TO ALLOW
#                                  # IMMEDIATE VIEWING.
#
#    # WHAT ABOUT UNCAUGHT PARSING ERRORS???
#    def parse_telemetry(self):
#        """."""
#        _raw_telemetry = self.read_telemetry_buffer()
#
#        parsed_telemetry = [
#            parse_educube_telemetry(
#                _timestamp                      ,
#                _telemetry_bytes.decode('utf-8')
#            )
#            for _timestamp, _telemetry_bytes in _raw_telemetry
#        ]
# 
#        return parsed_telemetry

 

##############################################################################

class FakeEduCubeConnection(EduCubeConnection):

    def setup_connections(self):
        logger.info("Setting up FAKE EduCube connections")

        self.output_file = open(self.output_path, 'a')
        fd, filename = tempfile.mkstemp()
        self.connection = os.fdopen(fd, "w")
        logger.debug(f"Using fake serial connection to: {filename}")

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

