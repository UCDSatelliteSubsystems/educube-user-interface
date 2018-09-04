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
import webbrowser

import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.websocket

import logging
logger = logging.getLogger(__name__)


##########################
# Globals
##########################
dirname = os.path.dirname(__file__)
STATIC_PATH = os.path.join(dirname, 'static')
TEMPLATE_PATH = os.path.join(dirname, 'templates')

##########################
# Main Tornado Application
##########################
class EduCubeWebApplication(tornado.web.Application):
    def __init__(self, educube_connection, port):
        handlers = [
            (r"/", MainHandler),
            (r"/socket", EducubeClientSocket, 
             {'educube_connection' : educube_connection}),
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
        self.render("educube.html")


class EducubeClientSocket(tornado.websocket.WebSocketHandler):
    """."""
    sockets = set()

    def __init__(self, application, request, educube_connection, **kwargs):
        self._educube_connection = educube_connection

        tornado.websocket.WebSocketHandler.__init__(
            self, application, request, **kwargs
            )

        # Startup periodic calls -- callback_time in milliseconds
        self.loop = tornado.ioloop.PeriodicCallback(
            callback = handle_telemetry_updates(self._educube_connection, 
                                                self.sockets             ),
            callback_time = 500                                            )
        self.loop.start()

    def open(self):
        self.sockets.add(self)
        logger.info("WebSocket opened")
        print("WebSocket opened")

    def on_close(self):
        self.sockets.remove(self)
        logger.info("WebSocket closed")
        print("WebSocket closed")

    def on_message(self, message):
        """
        Callback function to handle received websocket messages.

        Messages should be sent as stringified JSON objects, with the
        following fields:

            { 'msgtype' : <msgtype>, 'msgcontent' : <msgcontent> }

        The only allowed <msgtype> is 'command'. For a command, <msgcontent>
        should be a JavaScript style object, with fields:
            { 'board'    : <board>   , 'command' : <command>, 
              'settings' : <settings>                        }
         
        """

        logger.debug("WebSocket message received: {msg}".format(msg=message))
        
        try:
            msg = json.loads(message)
        except json.JSONDecodeError:
            errmsg = ('Received message could not be parsed as valid JSON'
                      +'\n        {msg}'.format(msg=message)              )
            logger.exception(errmsg, exc_info=True)
            return 

        if msg['msgtype'] == 'command':
            board    = msg['msgcontent'].get('board'   , None)
            cmd      = msg['msgcontent'].get('command' , None)
            settings = msg['msgcontent'].get('settings', None)

            try:
                handle_command(self._educube_connection, board, cmd, settings) 
            except:
                errmsg = ('Exception encountered while processing command '
                          +'with arguments:\n       '
                          +'board={board}, cmd={cmd}, settings={settings}'\
                           .format(board=board, cmd=cmd, settings=settings))
                logger.exception(errmsg, exc_info=True)
                return

        else:
            logger.warning('Unknown msgtype: {}'.format(msg['msgtype']))
        

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
    """
    Creates a function to be called periodically to send updated telemetry. 

    """
    def _handle_telemetry_updates():
        telemetry_packets = educube.parse_telemetry()

        for _telemetry in telemetry_packets:
            try: 
                _telemetry_json = json.dumps({
                    'msgtype'    : 'telemetry'                    , 
                    'msgcontent' : _telemetry._as_recursive_dict()
                })
            except:
                errmsg = ("Error encountered while converting the following "
                          "telemetry to JSON: \n"
                          "    {t}".format(t=_telemetry)                     )
                logger.exception(errmsg, exc_info=True)
                continue

            try:
                logger.debug("Updating telemetry: {}"\
                             .format(_telemetry_json))
                for socket in sockets:
                    socket.write_message(_telemetry_json)
            except:
                errmsg = ("Error encountered while sending the following "
                          "telemetry message over websockets: \n"
                          "    {t}".format(t=_telemetry_json))
                logger.exception(errmsg, exc_info=True)
                continue

    return _handle_telemetry_updates


#######################
# Main input
#######################
def run(educube_connection, port):
    """
    Start and run the IOLoop, given an EducubeConnection object to handle.
    """
    application = EduCubeWebApplication(educube_connection, port)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)

    webbrowser.open_new("http://localhost:{port}".format(port=port))

    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().stop()


