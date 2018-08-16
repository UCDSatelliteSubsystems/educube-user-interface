"""
educube/web/server.py


Allows control of the EduCube via a web interface.


There are two key functions: handle_commands receives commands from the web
interface and uses them to call the appropriate methods of the EduCube
controller; and handle_telemetry_updates collects new telemetry from the
EduCube and passes them as JSON messages over the WebSocket to the web
interface.

"""



import os
import json
import time
import click
import webbrowser
import tornado.web
import tornado.ioloop
import tornado.httpserver
from tornado import websocket

#from educube.util import display as display
from educube.util import educube_conn as educonn

#from educube.util.telemetry_parser import TelemetryParser

import logging
logger = logging.getLogger(__name__)


##########################
# Globals
##########################
PORT=18888
dirname = os.path.dirname(__file__)
STATIC_PATH = os.path.join(dirname, 'static')
TEMPLATE_PATH = os.path.join(dirname, 'templates')

#GLOBALS={
#    'sockets': [],
#}

#educube_connection = None
#parser = TelemetryParser()   # removed 2018-08-16 -- now in educube_connection

##########################
# Main Tornado Application
##########################
class Application(tornado.web.Application):
    def __init__(self, educube_connection):
        handlers = [
            (r"/", MainHandler),
            (r"/socket", EducubeClientSocket, 
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


class EducubeClientSocket(websocket.WebSocketHandler):
    """."""
    sockets = set()

    def __init__(self, application, request, educube_connection, **kwargs):
        self.educube = educube_connection

        websocket.WebSocketHandler.__init__(self, application, request, 
                                            **kwargs                   )

        # Startup periodic calls
        self.loop = tornado.ioloop.PeriodicCallback(
            callback      = handle_telemetry_updates(self.educube, 
                                                     self.sockets ),
            callback_time = 500                                     )
        self.loop.start()


    def open(self):
        self.sockets.add(self)
        print("WebSocket opened")

    def on_message(self, message):
        """
        Callback function to handle received websocket messages.

        Messages should be sent as stringified JSON objects, with the
        following fields:

            { msgtype : <msgtype>, msgcontent : <msgcontent> }

        The only allowed <msgtype> is 'command'. For a command, <msgcontent>
        should be a JavaScript style object, with fields:
            { board : <board>, command : <command>, settings : <settings>}
         
        """

        logger.debug("WebSocket message received: {msg}".format(msg=message))
        
        try:
            msg = json.loads(message)
        except json.JSONDecodeError:
            errmsg = ('Received message could not be parsed as valid JSON'
                      +'\n{msg}'.format(msg=message)                      )
            logger.exception(errmsg, exc_info=True)
            return 

        if msg['msgtype'] == 'command':
            board    = msg['msgcontent'].get('board'   , None)
            cmd      = msg['msgcontent'].get('command' , None)
            settings = msg['msgcontent'].get('settings', None)

            try:
                handle_command(self.educube_connection, board, cmd, settings) 
            except:
                errmsg = ('Exception encountered while processing command '
                          +'with arguments:\n'
                          +'board={board}, cmd={cmd}, settings={settings}'\
                           .format(board=board, cmd=cmd, settings=settings))
                logger.exception(errmsg, exc_info=True)
                return

        else:
            logger.warning('Unknown msgtype: {}'.format(msg['msgtype']))
        
    def on_close(self):
        print("WebSocket closed")
        self.sockets.remove(self)

########################
# Message parser
########################
def handle_command(educube, board, cmd, settings):
    """."""
    if cmd == 'T':
        educube.send_request_telem(board=board)

    elif board == 'ADC' and cmd == 'MAG':
        educube.send_set_magtorquer(**settings)

    elif board == 'ADC' and cmd == 'REACT':
        educube.send_set_reaction_wheel(**settings)

    elif board == 'EXP' and cmd =='HEAT':
        educube.send_set_thermal_panel(**settings)



# should this be moved to become a method of EducubeClientSocket??? Both
# educube and sockets could then be provided as attributes. 
# the parser should be moved into Educube
def handle_telemetry_updates(educube, sockets):
    """Creates a function to be called periodically to send updated telemetry. 

    """
    def _handle_telemetry_updates():
        telemetry_packets = educube.parse_telemetry()
        for _telemetry in telemetry_packets:
#            try:
#                t = parser.parse_telemetry(timestamp, telemetry)
#            except:
#                errmsg = "Telemetry badly formed: {t}".format(t=telemetry)
#                logger.exception(errmsg, exc_info=True)
#                continue
            try:
                _telemetry_json = _telemetry._asJSON()
                logger.debug("Updating telemetry: {}"\
                             .format(_telemetry_json))
                for socket in sockets:
                    socket.write_message(_telemetry_json)
            except:
                errmsg = "Error sending telemetry over websockets"
                logger.exception(errmsg, exc_info=True)

    return _handle_telemetry_updates


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
