"""
__main__.py

Runs the EduCube user interface using click and tornado.

"""

# configure logging
import logging
logger = logging.getLogger(__name__)

# educube imports
from educube._cli import main as cli_main


def patch_asyncio():
    """Set selector event loop for tornado asyncio.

    This fixes a bug that occurs on Windows 10 under Python 3.8, due to the
    default event loop being changed from selector to proactor.

    See https://github.com/tornadoweb/tornado/issues/2608 for further details.

    """
    import sys
    if sys.platform.startswith("win") and sys.version_info >= (3, 8):
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    
def main():
    patch_asyncio()
    cli_main()

# run
main()
