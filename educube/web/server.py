import os
import json
import time
import click
import webbrowser
import tornado.web
import tornado.ioloop
import tornado.httpserver
from tornado import websocket

from educube.util import display as display
from educube.util import educube_conn as educonn

from educube.util.telemetry_parser import TelemetryParser

import logging
logger = logging.getLogger(__name__)


##########################
# Globals
##########################
PORT=18888
dirname = os.path.dirname(__file__)
STATIC_PATH = os.path.join(dirname, 'static')
TEMPLATE_PATH = os.path.join(dirname, 'templates')

GLOBALS={
    'sockets': [],
}

educube_connection = None
parser = TelemetryParser()

##########################
# Main Tornado Application
##########################
class Application(tornado.web.Application):
    def __init__(self, educube_connection):
        handlers = [
            (r"/", MainHandler),
            (r"/socket", ClientSocket, 
             {'educube_connection' : educube_connection}),
            # (r"/push", HandleCommand),
        ]
        settings = {
            "template_path": TEMPLATE_PATH,
            "static_path": STATIC_PATH,
            "debug": True
        }
        logger.info("Starting web server with settings:\n{}"\
                    .format(json.dumps(settings, indent=2)))
        tornado.web.Application.__init__(self, handlers, **settings)


##########################
# Request Handlers
##########################
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("educube.html", title="EduCube")


class ClientSocket(websocket.WebSocketHandler):
    """."""
    def __init__(self, application, request, educube_connection, **kwargs):
        self.educube_connection = educube_connection
        websocket.WebSocketHandler.__init__(self, application, request, 
                                            **kwargs                   )

    def open(self):
        GLOBALS['sockets'].append(self)
        print("WebSocket opened")

    def on_message(self, message):
        logger.debug("WebSocket message received: {msg}".format(msg=message))
        if message.startswith("C|"):
            send_command(self.educube_connection, message)
#            if not message.endswith("|T"):
#                time.sleep(0.1) # some delay
#                send_command("C|CDH|T") # Force telem request
        
    def on_close(self):
        print("WebSocket closed")
        GLOBALS['sockets'].remove(self)


##########################
# WebSocket Handlers
##########################
def ws_send(data):
    for socket in GLOBALS['sockets']:
        socket.write_message(data)


#######################
# Telemetry updates
#######################
def call_board_updates(educube_connection):
    def _call_board_updates():
        logger.info("Calling update")
        telemetry_packets = educube_connection.get_telemetry()
        for telem in telemetry_packets:
            try:
                telemetry = parser.parse_telemetry(telem)
                print(display.display_color_json(telemetry))
                ws_send(json.dumps(telemetry))
            except Exception as e:
                logger.exception("Telemetry badly formed: %s\n%s" % (telem, e))
    return _call_board_updates

def send_command(educube_connection, cmd):
    educube_connection.send_command(cmd)


#######################
# Main input
#######################
def start_webserver(connection):
    edu_url = "http://localhost:{port}".format(port=PORT)
    print("EduCube will be available at {url}".format(url=edu_url))

    with educonn.get_connection(connection) as conn:
        click.secho("Your telemetry will be stored at '{path}'"\
                    .format(path=conn.output_path), fg='green')
        click.prompt("Press any key to continue", 
                     default=True, show_default=False)

        application = Application(conn)
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(PORT)
        # Startup periodic calls
        tornado.ioloop.PeriodicCallback(call_board_updates(conn), 500).start()
        webbrowser.open_new(edu_url)

        try:
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            tornado.ioloop.IOLoop.instance().stop()


#    # Initialize the connection to the EduCube
#    educube_connection = educonn.get_connection(connection)

#    # Setup the web application
#    applicaton = Application()
#    http_server = tornado.httpserver.HTTPServer(applicaton)
#    http_server.listen(PORT)
#    # Startup periodic calls
#    tornado.ioloop.PeriodicCallback(
#        call_board_updates, 500
#    ).start()
#    # Start the webserver
#    tornado.autoreload.add_reload_hook( # shutdown serial when reloading
#        educonn.shutdown_all_connections
#    )
#    webbrowser.open_new(edu_url)
#    try:
#        tornado.ioloop.IOLoop.instance().start()
#    except KeyboardInterrupt:
#        tornado.ioloop.IOLoop.instance().stop()
#        educonn.shutdown_all_connections()
