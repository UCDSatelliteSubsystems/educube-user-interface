#!/usr/bin/env python
import os
import sys
import json
import click
import serial
import logging.config

from educube.web import server as webserver

import logging
logger = logging.getLogger(__name__)

plugin_folder = os.path.join(os.path.dirname(__file__), 'commands')


def configure_logging(verbose):
    loglevels = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
    }
    logging.basicConfig(level=loglevels[verbose])


def verify_serial_connection(port, baud):
    try:
        ser = serial.Serial(port, baud, timeout=1)
        a = ser.read()
        if a:
            logger.debug('Serial open: %s' % port)
        else:
            logger.debug('Serial exists but is not readable (permissions?): %s' % port)
        ser.close()
    except serial.serialutil.SerialException as e:
        raise click.BadParameter("Serial not readable: %s" % e)

##############################
# COMMANDS
##############################

@click.group()
@click.option('-v', '--verbose', count=True)
@click.pass_context
def cli(ctx, verbose):
    configure_logging(verbose)


@cli.command()
@click.option('-s', '--serial', prompt=True)
@click.option('-b', '--baud', default=9600, prompt=True)
@click.option('-e', '--board', default='CDH')
@click.option('--fake', is_flag=True, default=False, help="Fake the serial")
@click.option('--json', is_flag=True, default=False, help="Outputs mostly JSON instead")
@click.pass_context
def start(ctx, serial, baud, board, fake, json):
    """
    Starts the EduCube web interface
    """
    logger.debug("""Running with settings:
        Serial: %s
        Baudrate: %s
        EduCube board: %s
    """ % (serial, baud, board))

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


def main():
    cli(obj={})

if __name__ == '__main__':
    main()