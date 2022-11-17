"""
educube.utils.threadutils._producer_consumer

"""

# standard library imports
import queue

# local imports
from ._loopthread import LoopThread


def consume(q, func, timeout=None):
    """Gets the next item from Queue q and performs func on it.

    If q is empty, waits for up to timeout seconds before timing out.
    """
    # TODO: should this return a value here? 
    try:
        item = q.get(timeout=timeout)
    except queue.Empty:
        pass
    else:
        func(item)

def produce(q, func):
    """Tries to create a new item and add it to a Queue for later use."""
    item = func()
    if item:
        q.put(item)

# ****************************************************************************

class ConsumerThread(LoopThread):
    """Waits for items in a Queue and consumes them."""
    def __init__(self, queue, consumer, timeout, setup=None, teardown=None):
        """Initialisation."""
        self.queue = queue
        self._consume = consumer

        self._timeout = timeout

        super().__init__(loop=None, setup=setup, teardown=teardown)
        
    def loop(self):
        consume(self.queue, self._consume, self._timeout)

# ****************************************************************************

class ProducerThread(LoopThread):
    """Produces items and adds them to a Queue."""
    def __init__(self, queue, producer, setup=None, teardown=None):
        self.queue = queue
        self._produce = producer

        super().__init__(loop=None, setup=setup, teardown=teardown)

    def loop(self):
        produce(self.queue, self._produce)


# ****************************************************************************

class ProducerConsumerThread(LoopThread):
    """Produces new items and immediately consumes them."""
    def __init__(self, producer, consumer, setup=None, teardown=None):
        """Initialiser.

        The parameters producer and consumer must be callables that produce and
        consume items one at a time.

        """
        self._produce = producer
        self._consume = consumer

        super().__init__(loop=None, setup=setup, teardown=teardown)

    def loop(self):
        item = self._produce()
        if item:
            self._consume(item)
