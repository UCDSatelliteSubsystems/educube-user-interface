"""
educube.util._logging_utils

Helpers for setting up logging.
"""

# standard library imports
import logging 
from datetime import datetime as dt

def current_time(fmt='%Y-%m-%d-%H-%M-%S'):
    """Return the current time as a formatted string."""
    _now = dt.now()
    return f"{_now:{fmt}}"


DEFAULT_LOG_FORMAT = '%(asctime)s : %(name)s : %(levelname)s : %(message)s'

LOGLEVELS = {
    0: logging.ERROR  ,
    1: logging.WARNING,
    2: logging.INFO   ,
    3: logging.DEBUG  ,
}

def configure_logging(verbose, filename=None,
                      fmt=DEFAULT_LOG_FORMAT, error_stream=True):
    """Set the logging level and handlers."""
    fmtr = logging.Formatter(fmt)

    # set up file handler
    if filename is None:
        filename = f"{current_time()}.log"

    filehandler = logging.FileHandler(filename=filename)
    filehandler.setFormatter(fmtr)
    filehandler.setLevel(LOGLEVELS[verbose])

    handlers = (filehandler,)

    # option to write errors to stderr?
    if error_stream:
        streamhandler = logging.StreamHandler()
        streamhandler.setFormatter(fmtr)
        streamhandler.setLevel(logging.ERROR)
        handlers = (*handlers, streamhandler)

    root = logging.getLogger()
    root.setLevel(LOGLEVELS[verbose])

    for handler in handlers:
        root.addHandler(handler)

    return root
