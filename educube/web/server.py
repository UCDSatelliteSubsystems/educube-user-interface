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
import logging
import webbrowser

import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.websocket

logger = logging.getLogger(__name__)


# ****************************************************************************
# Globals
# ****************************************************************************
dirname = os.path.dirname(__file__)
STATIC_PATH = os.path.join(dirname, 'static')
TEMPLATE_PATH = os.path.join(dirname, 'templates')

DEFAULT_PORT = 18888

# ****************************************************************************
# Main Tornado Application
# ****************************************************************************
class EduCubeWebApplication(tornado.web.Application):
    def __init__(self, educube_connection, port):
        handlers = [
            (r"/", MainHandler),
            (r"/socket", EduCubeServerSocket, 
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


# ****************************************************************************
# Request Handlers
# ****************************************************************************
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("educube.html", port=DEFAULT_PORT)


class EduCubeServerSocket(tornado.websocket.WebSocketHandler):
    """
    WebSocket handler to send telemetry & receive commands from web interface.

    """
    _sockets = set()

    def __init__(self, application, request, educube_connection, **kwargs):
        self.educube = educube_connection

        tornado.websocket.WebSocketHandler.__init__(
            self, application, request, **kwargs
            )

        # Startup periodic calls -- callback_time in milliseconds
        self.loop = tornado.ioloop.PeriodicCallback(
            callback = self.put_updated_telemetry,
            callback_time = 500
            )
        self.loop.start()

    def open(self):
        self._sockets.add(self)
        logger.info("WebSocket opened")
        print("WebSocket opened")

    def on_close(self):
        self._sockets.remove(self)
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

            try:
                self.educube.process_command(**msg['msgcontent'])
            except:
                errmsg = ('Exception encountered while processing command '
                          +'with arguments:\n       {msg}'.format(msg=msg))
                logger.exception(errmsg, exc_info=True)
                return

        else:
            logger.warning('Unknown msgtype: {}'.format(msg['msgtype']))


    def put_updated_telemetry(self):
        _telemetry_packets = self.educube.parse_telemetry()

        # when an error is encountered in parsing the data,
        # educube.parse_telemetry() returns None. This then causes another
        # error when turning to JSON, so first we need to filter out None.
        _telemetry_packets = (t for t in _telemetry_packets if t is not None)

        for _telemetry in _telemetry_packets:
            # convert telemetry to JSON
            try: 
                _telemetry_json = json.dumps({
                    'msgtype'    : 'telemetry'             , 
                    'msgcontent' : _telemetry._serialised()
                })
            except:
                errmsg = ("Error encountered while converting the following "
                          "telemetry to JSON: \n"
                          "    {t}".format(t=_telemetry)                     )
                logger.exception(errmsg, exc_info=True)
                continue

            # send telemetry over websocket
            try:
                logger.debug("Updating telemetry: {}"\
                             .format(_telemetry_json))
                for _socket in self._sockets:
                    _socket.write_message(_telemetry_json)
            except:
                errmsg = ("Error encountered while sending the following "
                          "telemetry message over websockets: \n"
                          "    {t}".format(t=_telemetry_json))
                logger.exception(errmsg, exc_info=True)
                continue

        

# ****************************************************************************
# Message parser
# ****************************************************************************
#def handle_command(educube, board, cmd, settings):
#    """."""
#    if cmd == 'T':
#        educube.send_request_telem(board=board)
#
#    elif board == 'ADC' and cmd == 'MAG':
#        educube.send_set_magtorquer(**settings)
#
#    elif board == 'ADC' and cmd == 'REACT':
#        educube.send_set_reaction_wheel(**settings)
#
#    elif board == 'EXP' and cmd =='HEAT':
#        educube.send_set_thermal_panel(**settings)
#
#    elif board == 'EPS' and cmd =='PWR_ON':
#        educube.send_set_chip_power_on(**settings)
#
#    elif board == 'EPS' and cmd =='PWR_OFF':
#        educube.send_set_chip_power_off(**settings)


## should this be moved to become a method of EduCubeServerSocket??? Both
## educube and sockets could then be provided as attributes. 
## the parser should be moved into EduCube
#def handle_telemetry_updates(educube, sockets):
#    """
#    Creates a function to be called periodically to send updated telemetry. 
#
#    """
#    def _handle_telemetry_updates():
#        telemetry_packets = educube.parse_telemetry()
#
#        # when an error is encountered in parsing the data,
#        # educube.parse_telemetry() returns None. This then causes another
#        # error when turning to JSON, so we need to filter out None.
#        telemetry_packets = (t for t in telemetry_packets if t is not None)
#
#        for _telemetry in telemetry_packets:
#            try: 
#                _telemetry_json = json.dumps({
#                    'msgtype'    : 'telemetry'             , 
#                    'msgcontent' : _telemetry._serialised()
#                })
#            except:
#                errmsg = ("Error encountered while converting the following "
#                          "telemetry to JSON: \n"
#                          "    {t}".format(t=_telemetry)                     )
#                logger.exception(errmsg, exc_info=True)
#                continue
#
#            try:
#                logger.debug("Updating telemetry: {}"\
#                             .format(_telemetry_json))
#                for socket in sockets:
#                    socket.write_message(_telemetry_json)
#            except:
#                errmsg = ("Error encountered while sending the following "
#                          "telemetry message over websockets: \n"
#                          "    {t}".format(t=_telemetry_json))
#                logger.exception(errmsg, exc_info=True)
#                continue
#
#    return _handle_telemetry_updates


# ****************************************************************************
# Main input
# ****************************************************************************
def run(educube_connection, port):
    """
    Start and run the IOLoop, given an EduCubeConnection object to handle.
    """
    application = EduCubeWebApplication(educube_connection, port)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)

    webbrowser.open_new("http://localhost:{port}".format(port=port))

    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().stop()


