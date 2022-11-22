"""
telemetry_parser

Provides a class Telemetry used to access telemetry parts and to represent
telemetry as JSON. Provides a function parse_educube_telemetry which acts as
the main interface for processing telemetry strings into useable Python
objects.  

"""

# standard library imports
from collections import namedtuple
import json
import logging

# local imports
from ._adc_parser import _parse_adc_telem
from ._cdh_parser import _parse_cdh_telem
from ._eps_parser import _parse_eps_telem
from ._exp_parser import _parse_exp_telem
from ._util import serialise, remove_value_none

# set up logging
LOG = logging.getLogger(__name__)

# look up table for board parser functions
BOARD_PARSERS = {
        "ADC" : _parse_adc_telem,
        "CDH" : _parse_cdh_telem,
        "EPS" : _parse_eps_telem,
        "EXP" : _parse_exp_telem,
    }

TELEMETRY_FIELDS = ('time', 'type', 'board', 'string', 'data')

class Telemetry(namedtuple('Telemetry', TELEMETRY_FIELDS)):
    """Container for information about a Telemetry packet

    Extends namedtuple with methods to simplify conversion to JSON. 

    """
    def _asdict(self):
        """Hack to work around bug when inheriting from namedtuple in 3.4."""
        #TODO: can this be removed now (we no longer support 3.4?)
        return dict(zip(self._fields, self))

    def _serialised(self, remove_null=False):
        """Convert all namedtuple attributes to dictionaries."""
        _serialised = serialise(self)
        
        if remove_null:
            _serialised = remove_value_none(_serialised)

        return _serialised
        
    def _as_JSON(self, remove_null=False):
        """Convert to a JSON string."""
        return json.dumps(self._serialise(remove_null=remove_null))


class TelemetryParserException(Exception):
    """An exception to be thrown if trying to handle Bad Telemetry."""


def parse_educube_telemetry(timestamp, telemetry_str):
    """Extract EduCube telemetry from a telemetry string.
    
    Returns a Telemetry object, which is a hierarchy of namedtuples,
    extended with a method _serialised to allow it to be converted into
    JSON.

    Parameters
    ==========
    timestamp
        the UNIX timestamp (in milliseconds) at which the telemetry was
        received

    telemetry_str
        the board telemetry as a (unicode) string
    
    """

    LOG.debug(f"Parsing telemetry str: {telemetry_str!r}")

    # separate telemetry parts and check for empty telemetry
    _telem_parts = telemetry_str.strip().split("|")

    if len(_telem_parts) < 3:
        LOG.warning("Empty telemetry")
        return

    _telem_type, _telem_board, *_chip_telem_parts = _telem_parts

    # get the appropriate parser using the board identifier in the telemetry
    # string 
    try:
        _parser_function = BOARD_PARSERS[_telem_board]
    except KeyError: # unrecognised board type
        errmsg = f"Unrecognised board ID: {_telem_board} - ignoring packet"
        LOG.exception(errmsg)
        return

    # parse the telemetry string 
    try:
        _parsed_telemetry = _parser_function(_chip_telem_parts)
    except: # unhandled parsing error
        errmsg = (
            f"Unhandled error while parsing telemetry packet: {telemetry_str}"
        )
        LOG.exception(errmsg, exc_info=True)
        return

    # return as a Telemetry object
    telemetry_tuple = Telemetry(
        time   = timestamp        ,
        type   = _telem_type      ,
        board  = _telem_board     ,
        string = telemetry_str    ,
        data   = _parsed_telemetry
    )
    LOG.debug(f'Parsed telemetry: {telemetry_tuple!r}')
    return telemetry_tuple


