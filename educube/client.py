#!/usr/bin/env python
import click
import serial
import pkg_resources
import serial.tools.list_ports

from educube.web import server as webserver
from educube.util.logging_utils import configure_logging

import logging
logger = logging.getLogger(__name__)


#def configure_logging(verbose):
#    loglevels = {
#        0: logging.ERROR,
#        1: logging.WARNING,
#        2: logging.INFO,
#        3: logging.DEBUG,
#    }
#    logging.basicConfig(level=loglevels[verbose])


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

##############################
# COMMANDS
##############################

def get_serial():
    ports = serial.tools.list_ports.comports()
    suggested_educube_port = ports[-1]
    return suggested_educube_port.device

def get_baud():
    ports = serial.tools.list_ports.comports()
    suggested_educube_port = ports[-1]
    if suggested_educube_port.description in ['BASE', 'Base Station']:
        return 9600
    else:
        return 115200

##############################
# COMMAND LINE INTERFACE
##############################

@click.group()
@click.option('-v', '--verbose', count=True,
               help="Set the log verbosity level (-v, -vv, -vvv)")
@click.pass_context
def cli(ctx, verbose):
    """Educube Client"""
    configure_logging(verbose)

@cli.command()
def version():
    """Prints the EduCube client version"""
    print(pkg_resources.require("educube")[0].version)

@cli.command()
@click.option('-s', '--serial', default=get_serial, prompt=True)
@click.option('-b', '--baud', default=get_baud, prompt=True)
@click.option('-e', '--board', default='CDH')
@click.option('--fake', is_flag=True, default=False, help="Fake the serial")
@click.option('--json', is_flag=True, default=False, help="Outputs mostly JSON instead")
@click.pass_context
def start(ctx, serial, baud, board, fake, json):
    """Starts the EduCube web interface""" 

    logger.info("""Running with settings:
        Serial: {serial}
        Baudrate: {baud}
        EduCube board: {board}
    """.format(serial=serial, baud=baud, board=board))

    ctx.obj['connection'] = {
        "type": "serial",
        "port": serial,
        "baud": baud,
        "board": board,
        "fake": fake,
    }
    if not fake:
        verify_serial_connection(serial, baud)

    webserver.start_webserver(
        connection=ctx.obj.get('connection')
    )

##############################
# MAIN
##############################

def main():
    cli(obj={})

if __name__ == '__main__':
    main()
