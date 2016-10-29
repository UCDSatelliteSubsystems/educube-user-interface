import os
import json
import time
import click

import tornado
import tornado.web
import tornado.httpserver
from educube.web import server as webserver


@click.group()
def cli():
    pass


@cli.command()
@click.pass_context
def start(ctx):
    """
    Starts the web interface
    """
    webserver.start_webserver(
        connection=ctx.obj.get('connection')
    )
