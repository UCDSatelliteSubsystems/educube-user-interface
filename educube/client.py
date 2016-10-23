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


def validate_satellite_connection(ctx, param, value):
    """
    Todo:
    Scan for serial connections and automatically start them up
    """

    def _test_serial_readable(port):
        try:
            ser = serial.Serial(value, 9600, timeout=1)
            if ser.read():
                logger.debug('Serial open: %s' % value)
            logger.debug('Serial closed: %s' % value)
            ser.close()
        except serial.serialutil.SerialException as e:
            raise click.BadParameter("Serial not readable: %s" % e)

    if param.name == "xbee":
        pass 
    if param.name == "serial":
        _test_serial_readable(value)
        return value


@click.command(cls=EduCubeCLI)
@click.option('-v', '--verbose', count=True)
@click.option('--json', is_flag=True, default=False, help="Outputs mostly JSON instead")
@click.option('-x', '--xbee', callback=validate_satellite_connection)
@click.option('-s', '--serial', callback=validate_satellite_connection)
@click.pass_context
def cli(ctx, serial, xbee, json, verbose):
    """
    EduCube

    This software provides both the command line and web interface
    to the EduCube toolkit.

    """
    if not (xbee or serial):
        raise Exception("Either Xbee or Serial must be provided")
    if xbee and serial:
        raise Exception("Only Xbee OR Serial must be provided")
    
    if xbee:
        ctx.obj['connection'] = {
            "type": "xbee",
            "port": xbee
        }
    if serial:
        ctx.obj['connection'] = {
            "type": "serial",
            "port": serial
        }
    configure_logging(verbose)


if __name__ == '__main__':
    cli(obj={}, standalone_mode=False)
