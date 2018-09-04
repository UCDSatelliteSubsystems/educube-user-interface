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

def configure_logging(verbose, error_stream=True):
    """Set the logging level and handlers."""
    fmt = '%(asctime)s : %(name)s : %(levelname)s :\n    %(message)s'
    fmtr = logging.Formatter(fmt)

    filehandler = logging.FileHandler(filename=current_time()+'.log')
    filehandler.setFormatter(fmtr)
    filehandler.setLevel(LOGLEVELS[verbose])

    handlers = (filehandler,)

    if error_stream:
        streamhandler = logging.StreamHandler()
        streamhandler.setFormatter(fmtr)
        streamhandler.setLevel(logging.ERROR)
        handlers = (filehandler, streamhandler)

    root = logging.getLogger()
    root.setLevel(LOGLEVELS[verbose])

    for handler in handlers:
        root.addHandler(handler)

    return root


#    logging.basicConfig(level=LOGLEVELS[verbose],
#                        filename=current_time()+'.log')
