#import os
import json
from collections import namedtuple

import logging
logger = logging.getLogger(__name__)


TELEMETRY_FIELDS = ('time', 'type', 'board', 'telem', 'data')

class Telemetry(namedtuple('Telemetry', TELEMETRY_FIELDS)):
    """
    Container for information about a Telemetry packet

    Extends namedtuple to simplify conversion to JSON. 

    """
    def _as_JSON(self, remove_null=False):
        """Convert to ta JSON string."""
        return json.dumps(self._as_recursive_dict(remove_null=remove_null))

    def _as_recursive_dict(self, remove_null=False):
        """Convert all namedtuple attributes to dictionaries."""
        if remove_null:
            return remove_value_none(as_recursive_dict(self))
        else:
            return as_recursive_dict(self)

def remove_value_none(d):
    """Recursively traverse a dictionary to remove keys with value None."""
    _dict = dict()
    for key, val in d.items():
        if isinstance(val, dict):
            _dict[key] = remove_value_none(val)
        elif val is not None:
            _dict[key] = val
    return _dict


def as_recursive_dict(obj):
    """Recursively parses a namedtuple to convert to dictionary."""
    _dict = dict()
    if isinstance(obj, tuple):  # and hasattr(obj, '_asdict')???
        items = obj._asdict()
        for item in items:
            if isinstance(items[item], tuple): # makes first test redundant???
                _dict[item] = as_recursive_dict(items[item])
            else:
                _dict[item] = items[item]
                               # else???
    return _dict



# 
# 
ADC_FIELDS = ('SUN_SENSORS', #
              'SUN_DIR'    , #
              'MAGNO_TORQ' , #
              'REACT_WHEEL', #
              'MPU_ACC'    , #
              'MPU_GYR'    , #
              'MPU_MAG'    , #
              )
CDH_FIELDS = ('GPS_DATE'      , #
              'GPS_FIX'       , #
              'GPS_FIX_DEGMIN', #
              'GPS_META'      , #
              'SEPARATION'    , #
              'HOT_PLUG'      , #
              )
EPS_FIELDS = ('INA'        , #
              'DS2438'     , #
              'DS18B20_A'  , #
              'DS18B20_B'  , #
              'CHARGING'   , #
              )
EXP_FIELDS = ('THERM_PWR'  , #
              'INA'        , #
              'PANEL_TEMP' , #
              )

ADCTelemetry = namedtuple('ADCTelemetry', ADC_FIELDS)
CDHTelemetry = namedtuple('CDHTelemetry', CDH_FIELDS)
EPSTelemetry = namedtuple('EPSTelemetry', EPS_FIELDS)
EXPTelemetry = namedtuple('EXPTelemetry', EXP_FIELDS)


# structures of subfields:
# ADC
SunSensor = namedtuple('SunSensor', ('FRONT', 'BACK', 'LEFT', 'RIGHT'))
MagTorqs  = namedtuple('MagTorqs', ('X','Y'))
MPUAcc    = namedtuple('MPUAcc', ('X', 'Y', 'Z'))
MPUGyr    = namedtuple('MPUGyr', ('X', 'Y', 'Z'))
MPUMag    = namedtuple('MPUMag', ('X', 'Y', 'Z'))

# CDH
GPSFix    = namedtuple('GPSFix', ('LAT', 'LON'))
GPSMeta   = namedtuple('GPSMeta', ('HDOP', 'ALT_CM', 'STATUS_INT', 'STATUS'))
SepStatus = namedtuple('SepStatus', ('ID', 'VAL'))
HotPlug   = namedtuple('HotPlug', ('ADC', 'COMM', 'EXP1', 'SPARE'))

# EPS

# INATelem is a puzzle -- it appears in both EXP and EPS telemetry, but with
# different arguments (shunt_V only appears on EXP, while switch_enabled and
# command_id only appear on EPS). I have implemented it with the complete set
# of arguments, and it is supplied with None values as appropriate on the
# EPS/EXP boards. These can later be stripped out. It might make more sense to
# implement two separate classes EPSINATelem and EXPINATelem.
INATelem  = namedtuple('INATelem', ('name', 'address', 'shunt_V',
                                    'bus_V', 'current_mA', 'power_mW', 
                                    'switch_enabled', 'command_id'    ))
DS2438    = namedtuple('DS2438' , ('temp', 'voltage', 'current'))
DS18B20   = namedtuple('DS18B20', ('temp'))

# EXP
Panels = namedtuple('Panels', ('P1', 'P2'))
Panel  = namedtuple('Panel' , ('A', 'B', 'C'))


# lookup tables
EPS_INA_NAME = {
    '64' : "Solar"  ,
    '65' : "Charger",
    '66' : "VBatt"  ,
    '67' : "+5V"    ,
    '73' : "+3.3V"  ,
    '68' : "Radio"  ,
    '69' : "SW1-5V" ,
    '72' : "SW1-3V" ,
    '70' : "SW2-5V" ,
    '74' : "SW2-3V" ,
    '71' : "SW3-5V" ,
    '75' : "SW3-3V" ,
    }

EPS_INA_COMMAND_ID = {
    '68' : 'R',
    '69' : '1',
    '70' : '2',
    '71' : '3',
    '72' : '1',
    '74' : '2',
    '75' : '3',
    }

EXP_INA_NAME = {
    '64' : 'Panel 1',
    '67' : 'Panel 2',
}

GPS_STATUS = {
    '1' : "EST"      ,
    '2' : "Time only",
    '3' : "STD"      ,
    '4' : "DGPS"     ,
    }

SEPARATION_STATUS = {
    '0' : "Switch Missing"   ,
    '1' : "Separated"        ,
    '2' : "In Launch Adapter",
    }


#def parse_


def parse_adc_telem(telem):
    """."""
    # convert the received telemetry to a dictionary with the chip identifiers
    # as keys. The MPU chips have to be handled as special cases -- we give
    # them unique identifiers by combining the identifier (MPU) with their
    # function, which is the first part of the following telemetry.
    _chip_telem = dict()
    for ct in telem:
        _chip_telem_id, *_chip_telem_parts = ct.split(',')
        if _chip_telem_id == 'MPU':
            key = 'MPU_{func_id}'.format(func_id=_chip_telem_parts[0])
            val = _chip_telem_parts[1:]
            _chip_telem[key] = val
        else:
            _chip_telem[_chip_telem_id] = _chip_telem_parts


    # SOL telem gives 'FRONT', 'BACK', 'LEFT', 'RIGHT' in order
    sun_sensors = SunSensor(*_chip_telem['SOL'])

    sun_dir = _chip_telem['ANG']

    # MAG telem gives 'X_P', 'X_N', 'Y_P', 'Y_N'
    # the parsed telemetry packet reduces this to +1/0/-1, depending on 
    # setting. TODO: calculate this as part of a constructor for MagTorqs???   
    x_p, x_n, y_p, y_n = _chip_telem['MAG'] 

    def _magnetorquer_sign(p, n):
        return (1 if p and not n else -1 if n and not p else 0)

    mag_torqs = MagTorqs(X=_magnetorquer_sign(x_p, x_n), 
                         Y=_magnetorquer_sign(y_p, y_n) )
#    magno_torq = None

    react_wheel = _chip_telem['WHL']

    # MPU
    mpu_acc = MPUAcc(*_chip_telem['MPU_ACC'])
    mpu_gyr = MPUGyr(*_chip_telem['MPU_GYR'])
    mpu_mag = MPUMag(*_chip_telem['MPU_MAG'])

    out = ADCTelemetry(SUN_SENSORS = sun_sensors, 
                       SUN_DIR     = sun_dir    , 
                       MAGNO_TORQ  = mag_torqs  , 
                       REACT_WHEEL = react_wheel, 
                       MPU_ACC     = mpu_acc    , 
                       MPU_GYR     = mpu_gyr    , 
                       MPU_MAG     = mpu_mag     )
    return out


def parse_cdh_telem(telem):
    """
    Extract and process telemetry structure.

    
    The CDH telemetry string contains telemetry from two chips:
        -- GPS
        -- Separation switch 

    """
    gps_telem, sep_telem = telem

    # parse gps_telem
    _, *gps_telem_parts = gps_telem.split(',')
    gps_date       = gps_telem_parts[0]
    gps_fix        = GPSFix(LAT = gps_telem_parts[1],
                            LON = gps_telem_parts[2] )
    # Why doesn't this convert to degrees and minutes???
    gps_fix_degmin = GPSFix(LAT = float(gps_telem_parts[1])/1e7,
                            LON = float(gps_telem_parts[2])/1e7 )
    # Why is STATUS = 'No Fix' hard coded????
    gps_meta       = GPSMeta(HDOP       = gps_telem_parts[3],
                             ALT_CM     = gps_telem_parts[4],
                             STATUS_INT = gps_telem_parts[5],
                             STATUS     = 'No Fix'           ) 

    # parse sep_telem
    _, sep_status_id, *board_hotplug_statuses = sep_telem.split(',')

    separation = SepStatus(ID  = sep_status_id                   , 
                           VAL = SEPARATION_STATUS[sep_status_id] )

    hotplug    = HotPlug(ADC   = board_hotplug_statuses[0],
                         COMM  = board_hotplug_statuses[1],
                         EXP1  = board_hotplug_statuses[2],
                         SPARE = board_hotplug_statuses[3] )

    out = CDHTelemetry(GPS_DATE       = gps_date      ,
                       GPS_FIX        = gps_fix       ,
                       GPS_FIX_DEGMIN = gps_fix_degmin,
                       GPS_META       = gps_meta      ,
                       SEPARATION     = separation    ,
                       HOT_PLUG       = hotplug        )
    return out


def parse_eps_telem(telem):
    """."""
    _chip_telem = dict()
    for ct in telem:
        _chip_telem_id, *_chip_telem_parts = ct.split(',')
        if _chip_telem_id == 'I':
            key = 'I{ina_id}'.format(ina_id = _chip_telem_parts[0])
            _chip_telem[key] = _chip_telem_parts
        else:
            _chip_telem[_chip_telem_id] = _chip_telem_parts

    # handle EPS INA chips. 
    ina_chips = (val 
                 for key, val in _chip_telem.items() if key.startswith('I'))
    # WHY IS switch_enabled = 1 HARD CODED???
    ina_telem = [
        INATelem(name           = EPS_INA_NAME.get(ina_parts[0], None),
                 address        = ina_parts[0]                              ,
                 shunt_V        = None                                      ,
                 bus_V          = ina_parts[1]                              ,
                 current_mA     = ina_parts[2]                              ,
                 power_mW       = '{:.2f}'.format(float(ina_parts[1]) *
                                                  float(ina_parts[2])  )    ,
                 switch_enabled = 1                                         ,
                 command_id     = EPS_INA_COMMAND_ID.get(ina_parts[0], None),
                 )
        for ina_parts in ina_chips                                           ]

    # 'temp', 'voltage', 'current'
    ds2438_telem = DS2438(*_chip_telem['DA'])

    # 
    ds18b20_a_telem = DS18B20(_chip_telem.get('DB', [None])[0])
    ds18b20_b_telem = DS18B20(_chip_telem.get('DC', [None])[0])

    # need error handling here???? not trivial to achieve using get. EAFP??? 
    _charging_val = _chip_telem.get('C', None) 
    charging_status = (True if _charging_val == '1' 
                       else False if _charging_val == '0'
                       else None                         )

    out = EPSTelemetry(INA       = ina_telem      ,
                       DS2438    = ds2438_telem   ,
                       DS18B20_A = ds18b20_a_telem,
                       DS18B20_B = ds18b20_b_telem,
                       CHARGING  = charging_status )
    return out
    


def parse_exp_telem(telem):
    """."""

    # convert the received telemetry to a dictionary with the chip identifiers
    # as keys. The INA chips have to be handled as special cases -- they don't
    # have unique identifiers, so the identifier is formed by combining the
    # first two pieces of info: I and a number representing the chip identity.
    # Note that the chip address is retained in the _chip_telem_parts -- we
    # need it for the final reported telemetry
    _chip_telem = dict()
    for ct in telem:
        _chip_telem_id, *_chip_telem_parts = ct.split(',')
        if _chip_telem_id == 'I':
            key = 'I{ina_id}'.format(ina_id = _chip_telem_parts[0] )
            _chip_telem[key] = _chip_telem_parts
        else:
            _chip_telem[_chip_telem_id] = _chip_telem_parts 

    therm_pwr  = Panels(P1 = _chip_telem.get('THERM_P1', [None])[0],
                        P2 = _chip_telem.get('THERM_P2', [None])[0] )

    # this feels dangerous -- what if something else starts with I???
    ina_chips = (val 
                 for key, val in _chip_telem.items() if key.startswith('I'))
    # exp ina format has shunt_V , but no switch_enabled???
    ina_telem = [INATelem(name           = EXP_INA_NAME[ina_parts[0]]     ,
                          address        = ina_parts[0]                   ,   
                          shunt_V        = ina_parts[1]                   ,
                          bus_V          = ina_parts[2]                   ,
                          current_mA     = ina_parts[3]                   ,
                          power_mW       = '{:.2f}'.format(              
                                              float(ina_parts[2]) * 
                                              float(ina_parts[3])  )      ,
                          switch_enabled = None                           ,
                          command_id     = None                            )
                 for ina_parts in ina_chips                                 ]

    panel_temp = Panels(P1 = Panel(A = _chip_telem.get('P1A', [None])[0],
                                   B = _chip_telem.get('P1B', [None])[0],
                                   C = _chip_telem.get('P1C', [None])[0],),
                        P2 = Panel(A = _chip_telem.get('P2A', [None])[0],
                                   B = _chip_telem.get('P2B', [None])[0],
                                   C = _chip_telem.get('P2C', [None])[0],))

    out = EXPTelemetry(THERM_PWR  = therm_pwr ,
                       INA        = ina_telem ,
                       PANEL_TEMP = panel_temp )
    return out


class TelemetryParserException(Exception):
    """An exception to be thrown if trying to handle Bad Telemetry."""


class TelemetryParser(object):
    board_parsers = {
        "ADC" : parse_adc_telem,
        "CDH" : parse_cdh_telem,
        "EPS" : parse_eps_telem,
        "EXP" : parse_exp_telem,
    }

    TELEM_IDENTIFER = "T"

    last_board_telemetry = {}
    
    # -- changed to take telemetry as a unicode string, not bytes.
    # -- shouldn't the check that this is telemetry happen before the parser?
    #    Therefore, isn't _telem_type always just going to be T?
    # -- changed the creation of telem_struct (renamed out) to the end, and 
    #    made explicitly into a Telemetry object
    # -- renamed the telem_parts breakdowns to make things clearer
    # -- what is the point of last_board_telemetry??? We never seem to do 
    #    anything with this stored telemetry?
    # -- removed self.BOARD_CONFIG and replaced with self.board_parser, which 
    #    is a dictionary that stores the parser functions. I don't see why we 
    #    need the board ID options -- those are what we know already?
    # -- changed so that we don't iterate over the possible telem boards, but 
    #    just look up the one we need. 
    def parse_telemetry(self, timestamp, telemetry):
        """."""

        logger.info("Parsing telemetry")
        _telem_parts = telemetry.strip().split("|")

        if len(_telem_parts) < 3:
            logger.warning("Empty telemetry")
            return

        _telem_type, _telem_board, *_chip_telem_parts = _telem_parts
        
        try:
            _parser_function = self.board_parsers[_telem_board]
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
                      "packet:\n    {t}".format(t=telemetry)                 )
            logger.exception(errmsg, exc_info=True)
            return


#        if telem_type == self.TELEM_IDENTIFER:
#            for bname, board in self.BOARD_CONFIG.items():
#                if telem_board == board['ID']:
#                    parser = getattr(self, board['parser'], None)
#                    if parser:
#                        parsed_telem = parser(telem_parts[2:])
#                        telem_struct['data'] = parsed_telem
#                        self.last_board_telemetry[board['ID']] = parsed_telem
#                    else:
#                        errmsg = ("Wrong parser defined for {bname} board: {parser}".format(bname=bname, parser=board['parser']))
#                        logger.error(errmsg)

        out = Telemetry(time  = timestamp                  ,
                        type  = _telem_type                ,
                        board = _telem_board               ,
                        telem = "|".join(_chip_telem_parts),
                        data  = _parsed_telemetry           )
        return out


