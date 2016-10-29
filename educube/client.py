#!/usr/bin/env python
import os
import sys
import json
import click
import serial
import logging.config
# import educube.util.display as display
# import educube.util.api_manager as api_manager

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


class EduCubeCLI(click.MultiCommand):

    def list_commands(self, ctx):
        commands = []
        for filename in os.listdir(plugin_folder):
            if filename.endswith('.py') and not filename.startswith("__init__") and not filename.startswith("cmd"):
                commands.append(filename[:-3])
        commands = sorted(set(commands))
        return commands

    def get_command(self, ctx, name):
        ns = {}
        ns_cli = None
        fn = os.path.join(plugin_folder, name + '.py')
        if os.path.exists(fn):
            with open(fn) as f:
                code = compile(f.read(), fn, 'exec')
                eval(code, ns, ns)
            ns_cli = ns['cli']
        if ns_cli:
            return ns_cli 
        else:
            print "The '%s' command does not exist, please choose one of: %s" % (name, self.list_commands(ctx))
            sys.exit(0)



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


@click.command(cls=EduCubeCLI)
@click.argument('serial')
@click.option('-v', '--verbose', count=True)
@click.option('-b', '--baud', default=9600)
@click.option('-e', '--board', default='CDH')
@click.option('--json', is_flag=True, default=False, help="Outputs mostly JSON instead")
@click.pass_context
def cli(ctx, serial, baud, board, json, verbose):
    """
    EduCube

    This software provides both the command line and web interface
    to the EduCube toolkit.

    """
    configure_logging(verbose)
    logger.debug("""Running with settings:
        Verbosity: %s
        Serial: %s
        Baudrate: %s
        EduCube board: %s
    """ % (verbose, serial, baud, board))

    ctx.obj['connection'] = {
        "type": "serial",
        "port": serial,
        "baud": baud,
        "board": board,
    }
    verify_serial_connection(serial, baud)

def main():
    cli(obj={}, standalone_mode=False)

if __name__ == '__main__':
    main()