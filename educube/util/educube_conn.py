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
    
    syntax_command_start = b'['
    syntax_command_end = b']'
    syntax_command = b'C'
    syntax_sep = b'|'

    board_id_EPS = b'EPS'
    board_id_CDH = b'CDH'
    board_id_EXP = b'EXP'
    board_id_ADC = b'ADC'

    telem_request_command = b'T'

    last_telem_request = 0
    telemetry_buffer = []
    telem_raw_format = "{datestamp}\t{telem}\n"

    def __init__(self, 
        conn_type, port, 
        baud=115200, output_path=None,
        read_interval_ms=500,
        telem_request_interval_s=5):
        ''' Constructor '''
        Thread.__init__(self)
        self.conn_type = conn_type
        self.port = port
        self.baud = baud
        self.timeout=.5
        assert(conn_type in ['serial', 'xbee'])
        if output_path:
            self.output_path = output_path
        else:
            self.output_path = os.path.join(
                tempfile.gettempdir(),
                "educube_telemetry_%s.raw" % self.conn_type
            )
        self.read_interval_ms = read_interval_ms
        self.telem_request_interval_s = telem_request_interval_s
        self.setup_connection()
        self.running = True
        logger.info("Telemetry will be stored to %s" % self.output_path)
    
    def  _start_serial_conn(self):
        self.connection = serial.Serial(
            self.port, self.baud, timeout=.5
        )

    def  _start_xbee_conn(self):
        pass

    def _write(self, bytes):
        if self.conn_type == "serial":
            self.connection.write(bytes)

    def _read_telem_serial(self):
        while self.connection.inWaiting() > 0:
            telem_data = self.connection.readline().strip()
            telem = {"time": time.time() * 1000, "data": telem_data}
            self.telemetry_buffer.append(telem)
            logger.debug("received: %s" % telem)

    def read_telem(self):
        if self.conn_type == "serial":
            self._read_telem_serial()

    def request_telem(self):
        if (time.time() - self.last_telem_request) > self.telem_request_interval_s:
            self.last_telem_request = time.time()
            logger.debug("Requesting telemetry")
            command = self.format_command(
                self.board_id_CDH, 
                self.telem_request_command
            )
            self.send_command(command)

    def setup_connection(self):
        self.output_file = open(self.output_path, 'a')
        if self.conn_type == "serial":
            self._start_serial_conn()
        if self.conn_type == "xbee":
            self._start_xbee_conn()
    
    def run(self):
        while self.running:
            self.read_telem()
            self.request_telem()
            time.sleep(self.read_interval_ms/1000.0)
        self.close_connections()
        logger.info("Stopped")

    def get_telemetry(self):
        telemetry = copy.deepcopy(self.telemetry_buffer)
        self.write_buffer_to_log()
        return telemetry

    def format_command(self, board, cmd):
        formatted_command = '{command_start}{sep}{board}{sep}{command}'.format(
            command_start=self.syntax_command,
            sep=self.syntax_sep,
            board=board,
            command=cmd
        )
        return formatted_command

    def send_command(self, command):
        command_structure = '{command_start}{command}{command_end}'.format(
            command_start=self.syntax_command_start,
            command_end=self.syntax_command_end,
            command=command
        )
        logger.info("Writing command: '%s' (%s)" % (command, command_structure))
        self._write(command_structure)
 
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
 

def shutdown_all_connections():
    for conn in connections:
        conn.shutdown()
        conn.join()


def get_connection(connection):
    global connections
    logger.info("Starting educube connection")
    educube_connection = EducubeConnection(
        connection['type'],
        connection['port'],
    )
    educube_connection.start()
    connections.append(educube_connection)
    return educube_connection

