import os
import json
import time
import click
# import educube.util.web as web
# import educube.util.display as display
# import educube.lib.avi_interface as avilib
import tornado
import tornado.web
import tornado.httpserver
import educube.web.server as webserver


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
