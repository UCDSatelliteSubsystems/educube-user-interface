#!/usr/bin/env python
import click
import serial
import pkg_resources
import serial.tools.list_ports

from educube.web import server as webserver
from educube import educube_conn as educonn
from educube.util import (configure_logging, verify_serial_connection, 
                          suggest_serial, suggest_baud) 

import logging
logger = logging.getLogger(__name__)

##############################
# COMMAND LINE INTERFACE
##############################

@click.group()
@click.option('-v', '--verbose', count=True,
               help="Set the log verbosity level (-v, -vv, -vvv)")
@click.pass_context
def cli(ctx, verbose):
    """EduCube Client"""
    configure_logging(verbose)

@cli.command()
def version():
    """Prints the EduCube client version"""
    print(pkg_resources.require("educube")[0].version)

@cli.command()
@click.option('-s', '--serial', default=suggest_serial, prompt=True)
@click.option('-b', '--baud', default=suggest_baud, prompt=True)
@click.option('-e', '--board', default='CDH')
@click.option('--fake', is_flag=True, default=False, help="Fake the serial")
def start(serial, baud, board, fake, port=18888):
    """Starts the EduCube web interface""" 

    logger.info("""Running EduCube connection with settings:
        Serial: {serial}
        Baudrate: {baud}
        EduCube board: {board}
    """.format(serial=serial, baud=baud, board=board))

    if not fake:
        verify_serial_connection(serial, baud)

    conn_params = {"type": "serial",
                   "port": serial,  # NOTE: SERIAL PORT, NOT WEBSOCKET PORT!!!
                   "baud": baud,
                   "board": board,
                   "fake": fake,
                   }

    with educonn.get_connection(conn_params) as conn:
        edu_url = "http://localhost:{port}".format(port=port)
        click.secho("EduCube will be available at {url}".format(url=edu_url), 
                    fg='green')
        click.secho("Your telemetry will be stored at '{path}'"\
                    .format(path=conn.output_path), fg='green')
        click.prompt("Press any key to continue",
                     default=True, show_default=False)

        webserver.run(conn, port)


##############################
# MAIN
##############################

def main():
    cli()

if __name__ == '__main__':
    main()
