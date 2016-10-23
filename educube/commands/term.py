import os
import json
import time
import click

from tabulate import tabulate
import util.display as display
import util.educube_conn as educonn
import lib.term as term_commands

import logging
logger = logging.getLogger(__name__)

COMMANDS = {
    # command name : function_name in lib/telem.py
    "read_telem": "read_telemetry", 
    "write_cmd": "write_command",
}

@click.group()
def cli():
    logger.info("Setting up commands")
    for cmd_name, func_name in COMMANDS.items():
        if hasattr(term_commands, func_name):
            COMMANDS[cmd_name] = getattr(term_commands, func_name)
        else:
            logger.warning("Command not found in lib/term.py (%s)" % cmd_name)
            del COMMANDS[cmd_name]
    pass


@cli.command()
@click.pass_context
def start(ctx):
    """
    Starts an interactive CLI session with the satellite
    """
    info_banner("Starting up EduCube CLI session")
    connection=ctx.obj.get('connection')
    educube_connection = educonn.get_connection(connection)

    try:
        while True:
            show_menu()
            cmd_name = read_command()
            process_command(cmd_name, educube_connection)
            click.pause()
    except KeyboardInterrupt:
        print "Exiting.."
    except click.Abort as e:
        print "Exiting.."
    except Exception:
        logger.exception("Unexpected error!")
    educonn.shutdown_all_connections()


######################################
# Util
######################################
def info_msg(txt):
    msg(txt, logging.INFO)

def info_banner(txt):
    msg(txt, logging.INFO, banner="#")

def msg(txt, level=None, banner="", banner_width=80, color=None):
    """
    Decorative text feedback
    """
    if not color and not level:
        color='white'
    elif level and not color:
        if level == logging.DEBUG:
            color='cyan'
        if level == logging.INFO:
            color='blue'
        if level == logging.WARNING:
            color='yellow'
    if len(banner) > 0:
        click.secho(banner*banner_width, fg=color)
    click.secho(banner + " " + txt, fg=color)
    if len(banner) > 0:
        click.secho(banner*banner_width, fg=color)


######################################
# Terminal Interactive CLI
######################################

def show_menu():
    click.clear()
    msg("EduCube CLI menu", level=logging.INFO, banner="#", color='green')
    command_table = []
    for cmd_name, command in COMMANDS.items():
        command_table.append([
            cmd_name, command.__doc__
        ])
    print tabulate(command_table, 
        headers=["Command name","Description"], 
        tablefmt="fancy_grid"
    )


def read_command():
    cmd_name = None
    while cmd_name not in COMMANDS.keys():
        if cmd_name: 
            msg("Bad command. Pick from (%s)" % COMMANDS.keys(), level=logging.WARNING)
        cmd_name = click.prompt("Enter a command from the CLI menu table: ")
    return cmd_name


def process_command(cmd, educube_connection):
    func = COMMANDS.get(cmd)
    func(educube_connection)
