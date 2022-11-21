#!/usr/bin/env python
import logging

import click
import serial
import serial.tools.list_ports

from educube import __version__
from educube.connection import configure_connection
from educube.web import server as webserver
from educube.util import (configure_logging, verify_serial_connection, 
                          suggest_serial, suggest_baud) 
from educube.util.contextutils import context

logger = logging.getLogger(__name__)

DEFAULT_PORT = 18888

# ****************************************************************************
# COMMAND LINE INTERFACE
# ****************************************************************************

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
    print("EduCube client version: {v}".format(v=__version__))



@cli.command()
@click.option('-s', '--serial', default=suggest_serial, prompt=True)
@click.option('-b', '--baudrate', default=suggest_baud, prompt=True)
@click.option('-e', '--board', default='CDH')
@click.option('-p', '--port', default=DEFAULT_PORT)
@click.option('--fake', is_flag=True, default=False, help="Fake the serial")
def start(serial, baudrate, board, fake, port):
    """Starts the EduCube web interface""" 

    logger.info("""Running EduCube connection with settings:
        Serial: {serial}
        Baudrate: {baudrate}
        EduCube board: {board}
        Websocket Port : {port}
    """.format(serial=serial, baudrate=baudrate, board=board, port=port))

    if not fake:
        verify_serial_connection(serial, baudrate)

    connection_params = {
        "type"     : "serial",
        "port"     : serial,  # NOTE: SERIAL PORT, NOT WEBSOCKET PORT!!!
        "baudrate" : baudrate,
        "board"    : board,
        "fake"     : fake,
        }

    # create (don't start) the connection
    conn = configure_connection(**connection_params)

    telemetry_path = conn.output_filepath
    educube_url = f"http://localhost:{port}"
    
    click.secho(f"EduCube available at {educube_url}", fg='green')
    click.secho(f"Telemetry stored at {telemetry_path}", fg='green')
    click.prompt("Press any key to continue", default=True, show_default=False)
    
    with context(conn.start, conn.shutdown):
        webserver.run(conn, port)
            
    click.secho("EduCube Connection Closed.", fg='green')
    click.secho("Telemetry is saved to '{path}'"\
                .format(path=telemetry_path), fg='green')


##############################
# MAIN
##############################

def main():
    cli()

if __name__ == '__main__':
    main()
