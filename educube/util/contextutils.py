"""
educube.util.contextutils

Some helpful context managers.
"""

# standard library imports
import contextlib


@contextlib.contextmanager
def context(setup=None, teardown=None):
    """Handle setup and teardown."""
    if setup:
        setup()

    try:
        yield
    finally:
        if teardown:
            teardown()


@contextlib.contextmanager
def listen_for_interrupt(callback=None):
    """Contextmanager to handle KeyboardInterrupt."""
    try:
        yield
    except KeyboardInterrupt:
        if callback:
            callback()
    return
