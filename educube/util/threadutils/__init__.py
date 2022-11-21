"""
educube.utils.threadutils

Extensions to Python's threading library to handle looped thread behaviour.

This provides five main classes:
* LoopThread
* SchedulerThread
* ConsumerThread
* ProducerThread
* ProducerConsumerThread

The library makes extensive use of Queues for thread synchronisation. 

"""

# standard library imports
import threading

# local imports
from ._loopthread import LoopThread
from ._scheduler import SchedulerThread
from ._producer_consumer import produce, ProducerThread
from ._producer_consumer import consume, ConsumerThread
from ._producer_consumer import ProducerConsumerThread



class ThreadPool:
    """Synchronised control of multiple threads."""
    def __init__(self, threads, stop_event=None):
        """Initialiser."""

        if stop_event is None:
            stop_event = threading.Event()

        self.stop_event = stop_event
        self.threads = threads

        # set a common stop event for all threads
        for thread in threads:
            thread._stop_event = stop_event


    def __repr__(self):
        return f"ThreadPool({self.threads!r})"
        
    def __iter__(self):
        return iter(self.threads)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()
        return False
    
    def start(self):
        """Start all threads."""
        # start each thread
        for thread in self:
            thread.start()

    def stop(self):
        """Stop all threads."""
        self.stop_event.set()

        # wait for each thread to finish
        for thread in self:
            thread.join()


