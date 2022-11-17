"""
educube.utils.fileutils

"""

# standard library imports
from queue import Queue

# local imports
from educube.utils.threadutils import ConsumerThread


# ****************************************************************************

class OutputFile:
    """Thread-safe file output."""
    def __init__(self, filename, mode='w', buffering=-1, encoding=None,
                 timeout=1):
        """Initialiser.

        ==========
        Parameters
        ==========

        filename, mode, buffering, encoding are passed to the built-in open.

        timeout is passed to ConsumerThread

        """
        # file arguments
        self.filename  = filename
        self.mode      = mode
        self.buffering = buffering
        self.encoding  = encoding
        
        # consumer thread arguments
        self._timeout  = timeout
        
        self._queue = Queue()

    def __repr__(self):
        return f'OutputFile({self.filename}, mode={self.mode})'        

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False
        
    def open(self):
        self._file = open(
            self.filename             ,
            mode      = self.mode     ,
            buffering = self.buffering,
            encoding  = self.encoding ,
        )

        self._thread = ConsumerThread(
            queue    = self._queue        ,
            consumer = self._write_to_file,
            timeout  = self._timeout      ,
        )
        self._thread.start()
        return self 
        
    def close(self):
        self._thread.stop()

        # clear any remaining messages in the queue 
        for _msg in self._queue:
            self._write_to_file(_msg)

        return self._file.close()

    def _write_to_file(self, msg):
        """Internal method to write to file."""
        self._file.write(msg)

    def write(self, msg):
        """Write string to file.

        Internally, this uses a Queue to ensure thread-safety.
        """
        self._queue.put(msg)

    def writeline(self, msg, newline='\n'):
        """Write string to file with newline termination.

        Internally, this uses a Queue to ensure thread-safety.
        """
        self.write(msg+newline)
