"""
educube.utils.threadutils._scheduler

"""

# standard library imports
from time import time, sleep

# local imports
from ._loopthread import LoopThread


class SchedulerThread(LoopThread):
    """Schedule function to run in infinite loop at regular intervals."""
    def __init__(self, loop, interval, setup=None, teardown=None):
        self._interval = interval

        super().__init__(loop, setup, teardown)

    def setup(self):

        # perform any custom setup steps
        super().setup()
        
        # set the timer start time
        # TODO: allow this to be supplied by user? 
        self._next_time = time()


    def loop(self):
        if self._block_until_next_time():
            self._loop()

    def _block_until_next_time(self):
        """.

        Returns either True or False, depending on how it reaches its end: True
        indicates that it ran to timeout, and so it is time for the next
        iteration of the function. False indicates that the function was
        interrupted early by the user (ie, ScheduleThread.stop was called) and
        the next iteration of the function should not be run.

        """
        # TODO: what happens if _loop takes longer than interval to complete?
        # Current behaviour is that Event.wait returns immediately, but
        # self._next_time can get further and further behind the current
        # time. Should this  function skip missed appointments?
        
        # set the time for the next iteration
        self._next_time += self._interval

        # calculate the time remaining until the next iteration is due
        _timeout = self._next_time - time()

        # threading.Event.wait blocks until either:
        # -- time out completes (returns False); or
        # -- Event.set is called (returns True).

        return (not self._stop_event.wait(_timeout))
