"""
_connection.py

Provides interface between the browser app and EduCube via USB serial. 

"""
# standard library imports
import logging
import os
import tempfile

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


# create module-level global logger object
logger = logging.getLogger(__name__)


def is_telemetry(msg):
    return msg.lstrip().startswith(b'T|')

def is_debug(msg):
    return msg.lstrip().startswith(b'DEBUG|')

#TODO: should this be done by EduCube.command?
def format_command(cmd):
    """Return a formatted EduCube command string."""
    return f'[{cmd}]'

def initialise_serial(portname, baudrate, timeout):
    """Helper function to initialise a new (closed) serial port."""
    port = serial.Serial()

    # configuration
    port.port = portname
    port.baudrate = baudrate
    port.timeout = timeout
    return port


def send_request_telemetry(conn, educube, board='CDH'):
    """Assemble and send a request telemetry command."""
#    _cmd = educube.request_telemetry(board)
    return conn.send_command(board, 'T', None)


# functions to handle printing to file and stdout
def write_rx_message(msg, timestamp, file):
    _msg = f"{timestamp}\t>>>\t{msg}"
    print(_msg)
    return file.writeline(_msg)

def write_tx_message(msg, timestamp, file):
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
            self.callback(bytes(self._rx_buffer))
            self._rx_buffer = bytearray()

    def __call__(self, byte):
        return self.update(byte)

# ****************************************************************************

class EduCubeConnectionError(Exception):
    """Exception to be raised for errors when communicating with EduCube."""
    ...

class EduCubeConnection:
    """
    Serial interface to send commands to and receive telemetry from an EduCube.

    """
    _default_encoding = 'latin-1'
    _EOL = b'\r\n'
    
    _conn_type = 'data'    # this is probably unnecessary -- it is only
                           # included so that, in principle, fake connections
                           # can easily be given a different default name.

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
        self.port = initialise_serial(portname, baudrate, timeout)

        # check board is valid  
        if board not in self.educube.board_ids:
            raise EduCubeConnectionError(f'Invalid board identifier {board}')

        self.board_id = board

        #TODO: do this outside EduCubeConnection.
        #TODO: make file output optional.
        # file to save telemetry
        if output_path is None:
            _type, _time = self._conn_type, millis()
            _filename = f"educube_telemetry_{_type}_{_time}.raw"
            output_path = os.path.join( tempfile.gettempdir(), _filename )

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
            consumer = RXHandler(self._process_message, self._EOL),
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

        
    def _process_message(self, msg, encoding=None):
        """Logs all received complete messages, and stores telemetry."""

        _encoding = self._default_encoding if encoding is None else encoding 

        _msgbytes = msg.strip(self._EOL)

        if _msgbytes:
            if is_telemetry(msg):
                # decode packet and add timestamp
                timestamp = millis()
                try:
                    telemetry_str = msg.decode(encoding=_encoding).strip()
                except:
                    logger.exception(f"Error decoding: {msg!r}", exc_info=True)
                else:
                    # write the received telemetry to file and output stream
                    write_rx_message(
                        msg       = telemetry_str,
                        timestamp = timestamp,
                        file      = self.output_file,
                    )
                    
                    # parse and store the received packet
                    self.educube.update_telemetry(telemetry_str, timestamp)
                    logger.debug(f"Received telemetry: {timestamp} : {msg}")
            
            elif is_debug(msg):
                logger.debug(f"Received DEBUG message: {msg!r}")
            
            else:
                logger.warning(f"Received unrecognised message: {msg!r}")
            
    def _send_request_telemetry(self):
        """Assemble and send a telemetry request to the connected board."""
        return send_request_telemetry(self, self.educube, self.board_id)

        
    ################
    # context manager
    ################

    def start(self):
        logger.info("STARTUP starting EduCubeConnection")
        self.setup_connections()
        self.start_threads()
        logger.info("STARTUP starting EduCubeConnection COMPLETE")
        return self

    def shutdown(self):
        logger.info("SHUTDOWN stopping EduCubeConnection")
        self.stop_threads()
        self.teardown_connections()
        logger.info("SHUTDOWN stopping EduCubeConnection COMPLETE")
    
    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, traceback):
        self.shutdown()
        return False

    ################
    # setup/teardown
    ################

    def setup_connections(self):
        logger.info("STARTUP setting up EduCube connections")

        self.output_file.open()
        logger.info(f"STARTUP opened telemetry savefile {self.output_filepath}"
        )

        self.port.open()
        logger.info(f"STARTUP opened Serial connection: {self.port!r}")

    def teardown_connections(self):
        logger.info("SHUTDOWN closing EduCube connections")

        self.port.close()
        logger.info("SHUTDOWN closed Serial connection")

        self.output_file.close()
        logger.info(
            f"SHUTDOWN closed telemetry savefile {self.output_filepath}"
        )

    ################
    # thread management
    ################

    #TODO: separate logging for each thread?
    def start_threads(self):
        logger.debug("STARTUP starting EduCubeConnection threadpool")
        self._threads.start()

    def stop_threads(self):
        logger.debug("SHUTDOWN stopping EduCubeConnection threadpool")
        self._threads.stop()

    ################
    # basic commands
    ################
    
    def send(self, msg, encoding=None):
        """Encode and transmit a message over Serial connection.

        For thread protection, calling the command actually queues the
        message, so it can be transmitted as soon as possible.

        """
        #TODO: logging?

        _encoding = self._default_encoding if encoding is None else encoding 
        
        # encode text to bytes
        _msg_bytes = msg.encode(encoding=_encoding)

        # add message to queue for transmission
        self._tx_queue.put(_msg_bytes)
    
    def send_command(self, board, command, settings):
        """
        Formats and transmits a command to EduCube

        The assembled command looks like [C|CDH|T]
        
        Parameters
        ----------
        board : str

        command : str

        settings : dict

        """
        # assemble the command
        _cmd = format_command(self.educube.command(board, command, settings))
        logger.info(f"Writing command: '{_cmd}'")

        # transmit the command to EduCube
        try:
            self.send(_cmd)
        except:
            errmsg = f"Encountered Error while sending command {_cmd}", 
            logger.exception(errmsg, exc_info=True)

        # record the command to file and output stream
        #TODO: this try...except... isn't necessary if using OutputFile?
        try:
            write_tx_message(_cmd, millis(), self.output_file)
        except:
            errmsg = f"Encountered Error while logging {_cmd} to file"
            logger.exception(errmsg, exc_info=True)

 

##############################################################################

#class FakeEduCubeConnection(EduCubeConnection):
#
#    def setup_connections(self):
#        logger.info("Setting up FAKE EduCube connections")
#
#        self.output_file = open(self.output_path, 'a')
#        fd, filename = tempfile.mkstemp()
#        self.connection = os.fdopen(fd, "w")
#        logger.debug(f"Using fake serial connection to: {filename}")
#
#    def teardown_connections(self):
#        logger.info("Tearing down FAKE EduCube connections")
#
#    def send_request_telem(self):
#        logger.info("Fake connection: ignoring telem request")

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

