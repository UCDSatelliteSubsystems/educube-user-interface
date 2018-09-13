import serial
import click

import logging
logger = logging.getLogger(__name__)

def verify_serial_connection(port, baud):
    try:
        ser = serial.Serial(port, baud, timeout=1)
        a = ser.read()
        if a:
            logger.debug('Serial open: {port}'.format(port=port))
        else:
            msg = ('Serial exists but is not readable '
                   +'(permissions?): {port}'.format(port=port))
            logger.debug(msg)
        ser.close()
    except serial.serialutil.SerialException as e:
        raise click.BadParameter("Serial not readable: {exc}".format(exc=e))

def suggest_serial():
    ports = serial.tools.list_ports.comports()

    try:
        suggested_educube_port = ports[-1]
    except IndexError:
        return 'No serial port suggestion available'

    return suggested_educube_port.device


def suggest_baud():
    ports = serial.tools.list_ports.comports()
    try: 
        suggested_educube_port = ports[-1]
    except:
        return 'No bard rate suggestion available'

    if suggested_educube_port.description in ('BASE', 'Base Station'):
        return 9600
    else:
        return 115200
