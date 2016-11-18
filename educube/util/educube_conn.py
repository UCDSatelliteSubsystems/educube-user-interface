import os
import copy
import time
import serial
import tempfile
from threading import Thread

import logging
logger = logging.getLogger(__name__)

connections = []


class EducubeConnection(Thread):
    
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
    telem_raw_format = "{datestamp}\t{telem}\n"

    def __init__(self, 
        conn_type, port, board,
        baud=9600, fake=False,
        output_path=None,
        read_interval_s=5,
        telem_request_interval_s=5):
        ''' Constructor '''
        Thread.__init__(self)
        self.conn_type = conn_type
        self.port = port
        self.baud = baud
        self.board_id = board
        self.timeout=.5

        assert(board in [self.board_id_EPS, self.board_id_CDH, self.board_id_EXP, self.board_id_ADC])

        if output_path:
            self.output_path = output_path
        else:
            self.output_path = os.path.join(
                tempfile.gettempdir(),
                "educube_telemetry_%s.raw" % self.conn_type
            )
        self.read_interval_s = read_interval_s
        self.telem_request_interval_s = telem_request_interval_s
        self.setup_connection()
        self.running = True
        logger.info("Telemetry will be stored to %s" % self.output_path)
    
    def read_telem(self):
        while self.connection.inWaiting() > 0:
            logger.debug("EduCube connection has data")
            telem_data = self.connection.readline().strip()
            telem = {"time": time.time() * 1000, "data": telem_data}
            self.telemetry_buffer.append(telem)
            logger.debug("Received telemetry: %s" % telem)

    def request_telem(self,):
        if (time.time() - self.last_telem_request) > self.telem_request_interval_s:
            self.last_telem_request = time.time()
            logger.debug("Requesting telemetry from board %s" % self.board_id)
            command = self.format_command(self.telem_request_command)
            self.send_command(command)

    def setup_connection(self):
        logger.info("Setting up connection")
        self.output_file = open(self.output_path, 'a')
        self.connection = serial.Serial(
            self.port, self.baud, timeout=3
        )
    
    def run(self):
        while self.running:
            self.read_telem()
            self.request_telem()
            for i in range(int(self.read_interval_s/.5)):
                if self.running:
                    time.sleep(.5)
        self.close_connections()
        logger.info("Stopped")

    def get_telemetry(self):
        telemetry = copy.deepcopy(self.telemetry_buffer)
        self.write_buffer_to_log()
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

    def send_command(self, command):
        command_structure = '{command_start}{command}{command_end}'.format(
            command_start=str(self.syntax_command_start),
            command_end=str(self.syntax_command_end),
            command=str(command)
        )
        logger.info("Writing command: '%s' (%s)" % (command, command_structure))
        try:
            self.connection.write(str.encode(command_structure))
            self.connection.flush()
        except:
            logger.exception("Error sending data")
 
    def write_buffer_to_log(self):
        for telem in self.telemetry_buffer:
            self.output_file.write(self.telem_raw_format.format(
                datestamp=int(telem['time']),
                telem=telem['data']
            ))
        self.telemetry_buffer = []

    def close_connections(self):
        logger.debug("Closing connection")
        self.connection.close()
        logger.debug("Closing file")
        self.output_file.close()

    def shutdown(self):
        logger.debug("Stopping educube connection")
        self.running = False
 

class FakeEducubeConnection(EducubeConnection):

    def setup_connection(self):
        self.output_file = open(self.output_path, 'a')
        fd, filename = tempfile.mkstemp()
        self.connection = os.fdopen(fd, "w")
        logger.debug("Using fake serial connection to: %s" % filename)

    def read_telem(self):
        logger.info("Fake connection: ignoring telem request")


def shutdown_all_connections():
    for conn in connections:
        conn.shutdown()
        conn.join()


def get_connection(connection):
    global connections
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
    educube_connection.start()
    connections.append(educube_connection)
    return educube_connection

