from collections import namedtuple
import json

import logging
logger = logging.getLogger(__name__)

from ._adc_parser import _parse_adc_telem
from ._cdh_parser import _parse_cdh_telem
from ._eps_parser import _parse_eps_telem
from ._exp_parser import _parse_exp_telem
from ._util import serialise, remove_value_none

BOARD_PARSERS = {
        "ADC" : _parse_adc_telem,
        "CDH" : _parse_cdh_telem,
        "EPS" : _parse_eps_telem,
        "EXP" : _parse_exp_telem,
    }

TELEMETRY_FIELDS = ('time', 'type', 'board', 'telem', 'data')

class Telemetry(namedtuple('Telemetry', TELEMETRY_FIELDS)):
    """
    Container for information about a Telemetry packet

    Extends namedtuple to simplify conversion to JSON. 

    """
    def _asdict(self):
        """Hack to work around bug when inheriting from namedtuple in 3.4."""
        return dict(zip(self._fields, self))

    def _serialised(self, remove_null=False):
        """Convert all namedtuple attributes to dictionaries."""
        if remove_null:
            return remove_value_none(serialise(self))
        else:
            return serialise(self)

    def _as_JSON(self, remove_null=False):
        """Convert to a JSON string."""
        return json.dumps(self._serialised(remove_null=remove_null))


class TelemetryParserException(Exception):
    """An exception to be thrown if trying to handle Bad Telemetry."""


def parse_educube_telemetry(timestamp, telemetry_str):
    """
    Extract EduCube telemetry from a telemetry string.
    
    Returns a Telemetry object, which is a hierarchy of namedtuples, extended
    with a method _serialised to allow it to be converted into JSON.

    Parameters
    ==========
    timestamp

    telemetry_str

    """

    logger.info("Parsing telemetry:\n{t}".format(t=telemetry_str))
    _telem_parts = telemetry_str.strip().split("|")

    if len(_telem_parts) < 3:
        logger.warning("Empty telemetry")
        return

    _telem_type, _telem_board, *_chip_telem_parts = _telem_parts
    
    try:
        _parser_function = BOARD_PARSERS[_telem_board]
    except KeyError:
        # unrecognised board type
        errmsg = ("Unrecognised board ID: {b}. ".format(b=_telem_board)
                  +"Ignoring packet")
        logger.exception(errmsg)
        return

    try:
        _parsed_telemetry = _parser_function(_chip_telem_parts)
    except:
        # unhandled parsing error
        errmsg = ("Unhandled error while parsing the following telemetry" 
                  "packet:\n    {t}".format(t=telemetry_str)             )
        logger.exception(errmsg, exc_info=True)
        return


    out = Telemetry(time  = timestamp                  ,
                    type  = _telem_type                ,
                    board = _telem_board               ,
                    telem = "|".join(_chip_telem_parts),
                    data  = _parsed_telemetry           )
    logger.debug('Parsed telemetry:\n{t}'.format(t=repr(out)))
    return out


