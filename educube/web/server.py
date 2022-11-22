"""\
educube.web.server

Allows control of the EduCube via a web interface.

This provides a class EduCubeWebApplication which runs the web GUI. The API
user interface is through the server.run function.

"""

# standard library imports
import os
import json
import logging
import webbrowser

# tornado web framework imports
import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.websocket

# local imports
from educube.util import millis
from educube.util.contextutils import listen_for_interrupt

logger = logging.getLogger(__name__)

# ****************************************************************************
# Globals
# ****************************************************************************
DIRNAME = os.path.dirname(__file__)
STATIC_PATH = os.path.join(DIRNAME, 'static')
TEMPLATE_PATH = os.path.join(DIRNAME, 'templates')

#DEFAULT_PORT = 18888

# ****************************************************************************
# Main Tornado Application
# ****************************************************************************
class EduCubeWebApplication(tornado.web.Application):
    def __init__(self, educube_connection, port):
        handlers = [
            (r"/", MainHandler,
             {'websocket_port' : port}),
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
    """Serve the main page."""
    def initialize(self, websocket_port):
        self.websocket_port = websocket_port

    def get(self):
        self.render("educube.html", port=self.websocket_port)


class EduCubeServerSocket(tornado.websocket.WebSocketHandler):
    """WebSocket handler for web interface telemetry & commands."""

    #TODO: is there any reason to have multiple sockets on a single socket?
    _sockets = set()

    def __init__(self, application, request, educube_connection, **kwargs):
        self.connection = educube_connection

        tornado.websocket.WebSocketHandler.__init__(
            self, application, request, **kwargs
        )

        # need to record update time to check for fresh telemetry
        # (should be epoch time in milliseconds)
        self._last_update = 0 #TODO: fix this hack!

        # Startup periodic calls -- callback_time in milliseconds
        self.loop = tornado.ioloop.PeriodicCallback(
            callback = self.put_updated_telemetry,
            callback_time = 500
            )
        self.loop.start()

    def open(self):
        self._sockets.add(self)
        logger.info("WebSocket opened")
#        print("WebSocket opened")

    def on_close(self):
        self._sockets.remove(self)
        logger.info("WebSocket closed")
#        print("WebSocket closed")

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

        logger.debug(f"WebSocket message received: {message!r}")
        
        try:
            msg = json.loads(message)
        except json.JSONDecodeError:
            _errmsg = f'Could not parse message as valid JSON: {message!r}'
            logger.exception(_errmsg, exc_info=True)
            return 

        if msg['msgtype'] == 'command':
            try:
                self.connection.send_command(**msg['msgcontent'])
            except:
                _errmsg = f"Exception processing msgtype 'command': {msg}"
                logger.exception(errmsg, exc_info=True)
                return

        else:
            _msgtype = msg['msgtype']
            logger.warning(f'Unknown msgtype: {_msgtype}')

    def put_updated_telemetry(self):
        """Get fresh telemetry and post it over the websocket."""

        #TODO: more reliable solution? 
        _telemetry_packets = (
            self.connection.educube.new_telemetry(self._last_update)
        )
        self._last_update = millis()
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
                _errmsg = (
                    f"Error converting EduCube telemetry to JSON: {_telemetry}"
                )
                logger.exception(_errmsg, exc_info=True)
                continue

            # send telemetry over websocket
            logger.debug(f"Updating telemetry: {_telemetry_json!r}")
            try:
                for socket in self._sockets:
                    socket.write_message(_telemetry_json)
            except:
                _errmsg = (
                    "Error sending EduCube telemetry over websocket: "
                    f"{_telemetry_json!r}"
                )
                logger.exception(_errmsg, exc_info=True)
                continue

# ****************************************************************************
# Main input
# ****************************************************************************
def log_interrupt_received():
    logger.info('KeyboardInterrupt received')
    return

def run_eventloop(ioloop):
    """Set Tornado ioloop running until KeyboardInterrupt."""
    try:
        logger.info(f'Starting webserver ioloop {ioloop!r}')
        with listen_for_interrupt(callback=log_interrupt_received):
            ioloop.start()
    finally:
        # make sure to stop the loop, even if another exception occurred!
        logger.info(f'Stopping webserver ioloop {ioloop!r}')
        ioloop.stop()
    return



def run(educube_connection, port):
    """
    Start and run the IOLoop, given an EduCubeConnection object to handle.
    """
    application = EduCubeWebApplication(educube_connection, port)

    # create the web server
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)

    # open a new browser tab
    _url = "http://localhost:{port}".format(port=port)
    webbrowser.open_new(_url)

    # run the ioloop
    _ioloop = tornado.ioloop.IOLoop.instance()
    logger.info(f'Starting webserver at {_url}')
    run_eventloop(_ioloop)
    logger.info(f'Stopped webserver at {_url}')


