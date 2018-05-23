import logging 

LOGLEVELS = {0: logging.ERROR  ,
             1: logging.WARNING,
             2: logging.INFO   ,
             3: logging.DEBUG  ,
             }


from datetime import datetime as dt
def current_time(fmt='%Y-%m-%d-%H-%M-%S'):
    """Return the current time as a formatted string."""
    return dt.now().strftime(format=fmt)

def configure_logging(verbose):
    """Set the logging level and handlers."""
    logging.basicConfig(level=LOGLEVELS[verbose],
                        filename=current_time()+'.log')
