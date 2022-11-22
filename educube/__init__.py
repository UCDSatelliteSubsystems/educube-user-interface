"""
educube
University College Dublin
2016 -

A Python client & user interface for EduCube, the 1U CubeSat simulator. 

"""

from .__version__ import __version__

# the EduCube command and telemetry parsers
from .educube import EduCube

# the serial connection
from .connection import EduCubeConnection
from .connection import configure_connection

# the web server
#from .web import EduCubeWebApplication
