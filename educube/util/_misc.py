import time

def millis():
    """Current system time in milliseconds."""
    return int(round(time.time() * 1000))
