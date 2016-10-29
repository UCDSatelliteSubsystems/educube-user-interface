import os
import json
import tornado.web
import tornado.ioloop
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
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/socket", ClientSocket),
            # (r"/push", HandleCommand),
        ]
        settings = {
            "template_path": TEMPLATE_PATH,
            "static_path": STATIC_PATH,
            "debug": True
        }
        logger.info("Starting web server with settings:\n%s" % json.dumps(settings, indent=2))
        tornado.web.Application.__init__(self, handlers, **settings)


##########################
# Request Handlers
##########################
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("educube.html", title="EduCube")


class ClientSocket(websocket.WebSocketHandler):
    def open(self):
        GLOBALS['sockets'].append(self)
        print "WebSocket opened"

    def on_message(self, message):
        print "Message received: %s" % message
        if message.startswith("C|"):
            send_command(message)
        # self.write_message(u"You said: " + message)
        
    def on_close(self):
        print "WebSocket closed"
        GLOBALS['sockets'].remove(self)


##########################
# WebSocket Handlers
##########################
# class HandleCommand(tornado.web.RequestHandler):
#     def get(self, *args, **kwargs):
#         data = self.get_argument('data')
#         for socket in GLOBALS['sockets']:
#             socket.write_message(data)
#         self.write('Posted')

def ws_send(data):
    for socket in GLOBALS['sockets']:
        socket.write_message(data)


#######################
# Telemetry updates
#######################
def call_board_updates():
    logger.info("Calling update")
    telemetry_packets = educube_connection.get_telemetry()
    for telem in telemetry_packets:
        try:
            telemetry = parser.parse_telemetry(telem)
            print display.display_color_json(telemetry)
            ws_send(json.dumps(telemetry))
        except Exception as e:
            logger.exception("Telemetry badly formed: %s\n%s" % (telem, e))


def send_command(cmd):
    educube_connection.send_command(cmd)


#######################
# Main input
#######################
def start_webserver(connection):
    global educube_connection
    # Initialize the connection to the EduCube
    educube_connection = educonn.get_connection(connection)
    # Setup the web application
    applicaton = Application()
    http_server = tornado.httpserver.HTTPServer(applicaton)
    http_server.listen(PORT)
    # Startup periodic calls
    tornado.ioloop.PeriodicCallback(
        call_board_updates, 500
    ).start()
    # Start the webserver
    tornado.autoreload.add_reload_hook( # shutdown serial when reloading
        educonn.shutdown_all_connections
    )
    print "Visit your browser at http://localhost:%s" % PORT
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().stop()
        educonn.shutdown_all_connections()
