"""
_connection.py

Provides interface between the browser app and EduCube via USB serial. 

"""
# standard library imports
import sys
import logging
import os
import tempfile
from queue import Queue

# third party imports
import serial

# local imports
from educube.educube import EduCube
from educube.util import millis
from educube.util.threadutils import SchedulerThread
from educube.util.threadutils import ConsumerThread, ProducerConsumerThread
from educube.util.threadutils import ThreadPool
from educube.util.fileutils import OutputFile
from educube.util.fileutils import writeline

# create module-level global logger object
logger = logging.getLogger(__name__)

# miscellaneous helper functions
def is_telemetry(msg):
    return msg.lstrip().startswith(b'T|')

def is_debug(msg):
    return msg.lstrip().startswith(b'DEBUG|')

def initialise_serial(portname, baudrate, timeout):
    """Helper function to initialise a new (closed) serial port."""
    port = serial.Serial()

    # configuration
    port.port = portname
    port.baudrate = baudrate
    port.timeout = timeout
    return port

def send_request_telemetry(connection, educube, board='CDH'):
    """Assemble and send a request telemetry command."""
    return connection.send_command(board, 'T', None)

# functions to handle printing to file and stdout
def writeline_to_streams(streams, line):
    return [writeline(stream, line) for stream in streams]

def write_rx_message(streams, msg, timestamp):
    _msg = f"{timestamp}\t>>>\t{msg}"
    return writeline_to_streams(streams, _msg)

def write_tx_message(streams, msg, timestamp):
    _msg = f"{timestamp}\t<<<\t{msg}"
    return writeline_to_streams(streams, _msg)


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
            _filename = f"educube_telemetry_{_type}_{_time}.dat"
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

        # output streams
        #TODO: make stdout optional?
        self._streams = [
            self.output_file,
            sys.stdout
        ]
        
    def _process_message(self, msg, encoding=None):
        """Logs all received complete messages, and stores telemetry."""

        _encoding = self._default_encoding if encoding is None else encoding 

        # remove trailing newline characters
        _msgbytes = msg.rstrip(self._EOL)

        if _msgbytes:
            if is_telemetry(msg):
                self._process_telemetry_message(msg, _encoding)

            elif is_debug(msg):
                logger.debug(f"Received DEBUG message: {msg!r}")
            
            else:
                logger.warning(f"Received unrecognised message: {msg!r}")

    def _process_telemetry_message(self, msg, encoding=None):
        """Decode telemetry packet and add timestamp."""
        # timestamp (milliseconds since epoch)
        timestamp = millis()

        # decode telemetry, write to file and update stored values
        try:
            telemetry_str = msg.decode(encoding=encoding).strip()
        except Exception:
            logger.exception(f"Error decoding: {msg!r}", exc_info=True)
            telemetry_str = None
        else:
            # write the received telemetry to file and output stream
            write_rx_message(
                streams   = self._streams,
                msg       = telemetry_str,
                timestamp = timestamp,
            )
            
            # parse and store the received packet
            self.educube.update_telemetry(telemetry_str, timestamp)
            logger.info(
                f"Received telemetry: ({timestamp}, {telemetry_str!r})"
            )
        return timestamp, telemetry_str
    
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

        For thread protection, calling this command actually queues the
        message, to be transmitted as soon as possible.

        """
        
        _encoding = self._default_encoding if encoding is None else encoding 

        #TODO: improve logging step here?
        
        # encode text to bytes
        _msg_bytes = msg.encode(encoding=_encoding)

        # add message to queue for transmission
        self._tx_queue.put(_msg_bytes)

        # write to stdout and output file
        #TODO: is error checking needed here?
        write_tx_message(
            streams   = self._streams,
            msg       = msg,
            timestamp = millis(),
        )
    
    def send_command(self, board, command, settings):
        """
        Formats and transmits a command to EduCube

        The assembled command looks like [C|CDH|T]
        
        Parameters
        ----------
        board : str
            the board (subsystem) to which the command will be sent
        command : str
            the command string
        settings : mapping
            any arguments needed by the command
        
        """
        # assemble the command
        _cmd = self.educube.command(board, command, settings)

        # transmit the command to EduCube
        try:
            self.send(_cmd)
            logger.info(f"Sent command: '{_cmd}'")
        except Exception:
            errmsg = f"Encountered Error while sending command {_cmd}", 
            logger.exception(errmsg, exc_info=True)
