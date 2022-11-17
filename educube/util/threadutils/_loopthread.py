"""
educube.utils.threadutils._loopthread

"""

# standard library imports
import threading


class LoopThread(threading.Thread):
    """Execute function in infinite loop with optional setup & teardown."""
    def __init__(self, loop, setup=None, teardown=None, stop_event=None):
        """Initialiser."""

        if stop_event is None:
            stop_event = threading.Event()

        self._stop_event = stop_event

        self._loop     = loop
        self._setup    = setup
        self._teardown = teardown
        
        super().__init__()

    def run(self):
        self.setup()
        try:
            while self.is_running():
                self.loop()

        finally:
            self.teardown()

    def setup(self):
        if self._setup:
            self._setup()

    def teardown(self):
        if self._teardown:
            self._teardown()

    def loop(self):
        self._loop()
                
    def is_running(self):
        return not self._stop_event.is_set()
        
    def stop(self):
        """Terminate the looped thread's execution."""
        self._stop_event.set()
        self.join()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()
        return False
