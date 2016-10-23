import json
import tornado.web
import tornado.ioloop

import educube.util.display as display
import educube.util.educube_conn as educonn
import educube.web.ec_settings as ec_settings

from tornado import websocket
from educube.util.telemetry_parser import TelemetryParser

import logging
logger = logging.getLogger(__name__)


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
            "template_path": ec_settings.TEMPLATE_PATH,
            "static_path": ec_settings.STATIC_PATH,
            "debug": True
        }
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
    http_server.listen(ec_settings.PORT)
    # Startup periodic calls
    tornado.ioloop.PeriodicCallback(
        call_board_updates, 500
    ).start()
    # Start the webserver
    tornado.autoreload.add_reload_hook( # shutdown serial when reloading
        educonn.shutdown_all_connections
    )
    print "Visit your browser at http://localhost:%s" % ec_settings.PORT
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().stop()
        educonn.shutdown_all_connections()
