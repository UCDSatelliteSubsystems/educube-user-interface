#import os
import json
from collections import namedtuple

import logging
logger = logging.getLogger(__name__)


#Telemetry = namedtuple('Telemetry', ('time', 'type', 'board', 'telem', 'data'))

TELEMETRY_FIELDS = ('time', 'type', 'board', 'telem', 'data')

class Telemetry(namedtuple('Telemetry', TELEMETRY_FIELDS):
    """."""
    def _asJSON(self, remove_null=False):
        """."""
        if remove_null:
            return json.dumps(remove_value_none(self._asdict()))
        else:
            return json.dumps(self._asdict())


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
MagnoTorq = namedtuple('MagnoTorq', ('X_P', 'X_N', 'Y_P', 'Y_N'))
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
    magno_torq = MagnoTorq(*_chip_telem['MAG'])

    react_wheel = _chip_telem['WHL']

    # MPU
    mpu_acc = MPUAcc(*_chip_telem['MPU_ACC'])
    mpu_gyr = MPUGyr(*_chip_telem['MPU_GYR'])
    mpu_mag = MPUMag(*_chip_telem['MPU_MAG'])

    out = ADCTelemetry(SUN_SENSORS = sun_sensors, 
                       SUN_DIR     = sun_dir    , 
                       MAGNO_TORQ  = magno_torq , 
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
            key = 'I{ina_id}'.format(ina_id = chip_telem_parts[0])
            _chip_telem[key] = _chip_telem_parts
        else:
            _chip_telem[_chip_telem_id] = _chip_telem_parts

    ina_chips = (val 
                 for key, val in _chip_telem.items() if key.startswith['I'])
    # WHY IS switch_enabled = 1 HARD CODED???
    ina_telem = [INATelem(name           = EPS_INA_NAME[ina_parts[0]]      ,
                          address        = ina_parts[0]                    ,   
                          shunt_V        = None                            ,
                          bus_V          = ina_parts[1]                    ,
                          current_mA     = ina_parts[2]                    ,
                          power_mW       = '{:.2f}'.format(                
                                              ina_parts[1] * ina_parts[2]) ,
                          switch_enabled = 1                               ,
                          command_id     = EPS_INA_COMMAND_ID[ina_parts[0]] )
                 for ina_parts in ina_chips                                 ]

    # 'temp', 'voltage', 'current'
    ds2438_telem = DS2438(*_chip_telem['DA'])

    # 
    ds18b20_a_telem = DS18B20(_chip_telem.get('DB', [None])[0])
    ds18b20_b_telem = DS18B20(_chip_telem.get('DC', [None])[0])

    # need error handling here???? not trivial to achieve using get. EAFP??? 
    charging_status = _chip_telem['CHARGING'] == '1'

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
            _chip_telem[_chip_telem_id] = chip_telem_parts 

    therm_pwr  = Panels(P1 = chip_telem.get('THERM_P1', [None])[0],
                        P2 = chip_telem.get('THERM_P2', [None])[0] )

    # this feels dangerous -- what if something else starts with I???
    ina_chips = (val 
                 for key, val in _chip_telem.items() if key.startswith['I'])
    # exp ina format has shunt_V , but no switch_enabled???
    ina_telem = [INATelem(name           = EXP_INA_NAME[ina_parts[0]]     ,
                          address        = ina_parts[0]                   ,   
                          shunt_V        = ina_parts[1]                   ,
                          bus_V          = ina_parts[2]                   ,
                          current_mA     = ina_parts[3]                   ,
                          power_mW       = '{:.2f}'.format(              
                                              ina_parts[2] * ina_parts[3]),
                          switch_enabled = None                           ,
                          command_id     = None                            )
                 for ina_parts in ina_chips                                 ]

    panel_temp = Panels(P1 = Panel(A = chip_telem.get('P1A', [None])[0],
                                   B = chip_telem.get('P1B', [None])[0],
                                   C = chip_telem.get('P1C', [None])[0],),
                        P2 = Panel(A = chip_telem.get('P2A', [None])[0],
                                   B = chip_telem.get('P2B', [None])[0],
                                   C = chip_telem.get('P2C', [None])[0],))

    out = EXPTelemetry(THERM_PWR  = therm_pwr ,
                       INA        = ina_telem ,
                       PANEL_TEMP = panel_temp )
    return out



def remove_value_none(d):
    """Recursively traverse a dictionary to remove keys with value None."""
    _dict = dict()
    for key, val in d.items():
        if isinstance(val, dict):
            _dict[key] = remove_value_none(val)
        elif val is not None:
            _dict[key] = val
    return _dict


def as_dict(obj):
    """Recursively parses a namedtuple to convert to dictionary."""
    _dict = dict()
    if isinstance(obj, tuple):  # and hasattr(obj, '_asdict')???
        items = obj._asdict()
        for item in items:
            if isinstance(items[item], tuple): # makes first test redundant???
                _dict[item] = as_dict(items[item])
            else:
                _dict[item] = items[item]
                               # else???
    return _dict

class TelemetryParserException(Exception):
    """An exception to be thrown if trying to handle Bad Telemetry."""


class TelemetryParser(object):

#    BOARD_CONFIG = {
#        "EPS": {
#            "ID": "EPS",
#            "parser": 'parse_eps_telem'
#        },
#        "CDH": {
#            "ID": "CDH",
#            "parser": 'parse_cdh_telem'
#        },
#        "EXP": {
#            "ID": "EXP",
#            "parser": 'parse_exp_telem'
#        },
#        "ADC": {
#            "ID": "ADC",
#            "parser": 'parse_adc_telem'
#        }
#    }

    board_parsers = {
        "ADC" : parse_adc_telem,
        "CDH" : parse_cdh_telem,
        "EPS" : parse_eps_telem,
        "EXP" : parse_exp_telem,
    }

    TELEM_IDENTIFER = "T"

    last_board_telemetry = {}
    
#    def __init__(self):
#        pass

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
#        telem_parts = telemetry.decode('utf8').split("|")
        _telem_parts = telemetry.split("|")

        if len(_telem_parts) < 3:
            logger.warning("Empty telemetry")
            return

        _telem_type, _telem_board, *_chip_telem_parts = _telem_parts
#        telem_struct = {
#            "time": timestamp,
#            "type": telem_type,
#            "board": telem_board,
#            "telem": "|".join(telem_parts[2:])
#        }
        
        try:
            _parser_function = self.board_parser[_telem_board]
        except KeyError:
            # unrecognised board type
            return

        try:
            _parsed_telemetry = _parser_function(chip_telem_parts)
        except:
            # unhandled parsing error
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




    def get_command_id_for_eps_ina(self, address):
        if address == 68:
            return "R"
        if address in [69, 72]:
            return "1"
        if address in [70, 74]:
            return "2"
        if address in [71, 75]:
            return "3"

    def parse_eps_telem(self, telem):
        telem_structure = {
            "INA": [],
            "DS2438": {},
            "DS18B20_A": {},
            "DS18B20_B": {},
            "CHARGING": None
        }
        for chip_telem in telem:
            ctelem_parts = chip_telem.split(",")
            if ctelem_parts[0] == "I":
                ina_telem = {
                    "name": INA_NAMES[ctelem_parts[1]],
                    "address": ctelem_parts[1],
                    "bus_V": ctelem_parts[2],
                    "current_mA": ctelem_parts[3],
                    "switch_enabled": 1,
                    "power_mW": "{:.2f}".format(float(ctelem_parts[2])
                                                * float(ctelem_parts[3])),
                    "command_id": self.get_command_id_for_eps_ina(int(ctelem_parts[1]))
                }
                telem_structure["INA"].append(ina_telem)
            if ctelem_parts[0] == "DA":
                telem_structure["DS2438"] = {
                    "temp": ctelem_parts[1],
                    "voltage": ctelem_parts[2],
                    "current": ctelem_parts[3]
                }
            if ctelem_parts[0] == "DB":
                telem_structure["DS18B20_A"] = {
                    "temp": ctelem_parts[1]
                }
            if ctelem_parts[0] == "DC":
                telem_structure["DS18B20_B"] = {
                    "temp": ctelem_parts[1]
                }
            if ctelem_parts[0] == "C":
                telem_structure["CHARGING"] = (ctelem_parts[1] == 1)

        # Now we go back over the telemetry to add in the status of the INA
        # switches We can't do it in the same loop in case (somehow) the
        # switch state comes before the switch power telemtry

        def add_ina_switch_state(ina_name, switch_state):
            address_ids = []
            if ina_name == "R":
                address_ids = [68]
            if ina_name == "1":
                address_ids = [69, 72]
            if ina_name == "2":
                address_ids = [70, 74]
            if ina_name == "3":
                address_ids = [71, 75]
            for ina_telem in telem_structure["INA"]:
                if int(ina_telem['address']) in address_ids:
                    ina_telem['switch_enabled'] = int(switch_state)

        for chip_telem in telem:
            ctelem_parts = chip_telem.split(",")
            # Skip all telem not 'I_E'    
            if ctelem_parts[0] != "I_E":
                continue
            add_ina_switch_state("R", ctelem_parts[1])
            add_ina_switch_state("1", ctelem_parts[2])
            add_ina_switch_state("2", ctelem_parts[3])
            add_ina_switch_state("3", ctelem_parts[4])
        return telem_structure


    def parse_adc_telem(self, telem):
        telem_structure = {
            "SUN_SENSORS": {},
            "SUN_DIR": {},
            "MAGNO_TORQ": {},
            "REACT_WHEEL": None,
            "MPU_ACC": {},
            "MPU_GYR": {},
            "MPU_MAG": {},
        }
        for chip_telem in telem:
            ctelem_parts = chip_telem.split(",")
            # Handle sunsensors
            if ctelem_parts[0] == "SOL":
                telem_structure["SUN_SENSORS"] = {
                    "FRONT": ctelem_parts[1],
                    "BACK": ctelem_parts[2],
                    "LEFT": ctelem_parts[3],
                    "RIGHT": ctelem_parts[4]
                }
            # Handle sun angle calculation
            if ctelem_parts[0] == "ANG":
                telem_structure["SUN_DIR"] = ctelem_parts[1]
            # Handle MAG intensity
            if ctelem_parts[0] == "MAG":
                telem_structure["MAGNO_TORQ"] = {
                    "X_P": ctelem_parts[1],
                    "X_N": ctelem_parts[2],
                    "Y_P": ctelem_parts[3],
                    "Y_N": ctelem_parts[4]
                }
            # Handle reaction wheel data
            if ctelem_parts[0] == "WHL":
                telem_structure["REACT_WHEEL"] = ctelem_parts[1]
            if ctelem_parts[0] == "MPU":
                if ctelem_parts[1] == "ACC":
                    telem_structure["MPU_ACC"] = {
                        "X": ctelem_parts[2],
                        "Y": ctelem_parts[3],
                        "Z": ctelem_parts[4]
                    }
                if ctelem_parts[1] == "GYR":
                    telem_structure["MPU_GYR"] = {
                        "X": ctelem_parts[2],
                        "Y": ctelem_parts[3],
                        "Z": ctelem_parts[4]
                    }
                if ctelem_parts[1] == "MAG":
                    telem_structure["MPU_MAG"] = {
                        "X": ctelem_parts[2],
                        "Y": ctelem_parts[3],
                        "Z": ctelem_parts[4]
                    }
        return telem_structure

    def _degmin_to_deg(self, degmin):
        str_val = "%s" % degmin
        point_loc = str_val.find(".")
        deg_part = float(str_val[0:point_loc-2])
        min_part = float(str_val[point_loc-2:])
        return deg_part + (min_part/60)

    def parse_cdh_telem(self, telem):
        telem_structure = {
            "GPS_DATE": None,
            "GPS_FIX": {},
            "GPS_META": {},
            "SEPARATION": {},
            "HOT_PLUG": {}
        }
        for chip_telem in telem:
            ctelem_parts = chip_telem.split(",")
            # Handle sunsensors
            if ctelem_parts[0] == "GPS":
                telem_structure["GPS_DATE"] = ctelem_parts[1]
                telem_structure["GPS_FIX_DEGMIN"] = {
                    "LAT": ctelem_parts[2],
                    "LON": ctelem_parts[3],
                }
                telem_structure["GPS_FIX"] = {
                    "LAT": float(ctelem_parts[2])/1e7,
                    "LON": float(ctelem_parts[3])/1e7,
                }
                telem_structure["GPS_META"] = {
                    "HDOP": ctelem_parts[4],
                    "ALT_CM": ctelem_parts[5],
                    "STATUS_INT": ctelem_parts[6],
                    "STATUS": "No Fix"
                }
                stat_int = int(telem_structure["GPS_META"]["STATUS_INT"])
                if stat_int == 1:
                    telem_structure["GPS_META"]["STATUS"] = "EST"
                elif stat_int == 2:
                    telem_structure["GPS_META"]["STATUS"] = "Time only"
                elif stat_int == 3:
                    telem_structure["GPS_META"]["STATUS"] = "STD"
                elif stat_int == 4:
                    telem_structure["GPS_META"]["STATUS"] = "DGPS"
            if ctelem_parts[0] == "SEP":
                telem_structure["SEPARATION"]["ID"] = ctelem_parts[1]
                if ctelem_parts[1] == 0:
                    telem_structure["SEPARATION"]["VAL"] = "Switch Missing"
                if ctelem_parts[1] == 1:
                    telem_structure["SEPARATION"]["VAL"] = "Separated"
                if ctelem_parts[1] == 2:
                    telem_structure["SEPARATION"]["VAL"] = "In Launch Adapter"
                telem_structure["HOT_PLUG"]["ADC"] = ctelem_parts[2]
                telem_structure["HOT_PLUG"]["COMM"] = ctelem_parts[3]
                telem_structure["HOT_PLUG"]["EXP1"] = ctelem_parts[4]
                telem_structure["HOT_PLUG"]["SPARE"] = ctelem_parts[5]
        return telem_structure

    def get_exp_ina_name(self, address):
        if address == 64:
            return "Panel 1"
        if address == 67:
            return "Panel 2"

    def parse_exp_telem(self, telem):
        telem_structure = {
            "THERM_PWR": {},
            "INA": [],
            "PANEL_TEMP": {
                "P1": {},
                "P2": {},
            },
        }
        for chip_telem in telem:
            ctelem_parts = chip_telem.split(",")
            # Handle sunsensors
            if ctelem_parts[0] == "THERM_P1":
                telem_structure["THERM_PWR"]["P1"] = ctelem_parts[1]
            if ctelem_parts[0] == "THERM_P2":
                telem_structure["THERM_PWR"]["P2"] = ctelem_parts[1]
            if ctelem_parts[0] == "I":
                ina_telem = {
                    "name"   : self.get_exp_ina_name(int(ctelem_parts[1])),
                    "address": ctelem_parts[1],
                    "shunt_V": ctelem_parts[2],
                    "bus_V"  : ctelem_parts[3],
                    "current_mA": ctelem_parts[4],
                    "power_mW": "{:.2f}".format(float(ctelem_parts[4])
                                                * float(ctelem_parts[3])),
                }
                telem_structure["INA"].append(ina_telem)
            if ctelem_parts[0] == "P1A":
                telem_structure['PANEL_TEMP']['P1']['A'] = ctelem_parts[1]
            if ctelem_parts[0] == "P1B":
                telem_structure['PANEL_TEMP']['P1']['B'] = ctelem_parts[1]
            if ctelem_parts[0] == "P1C":
                telem_structure['PANEL_TEMP']['P1']['C'] = ctelem_parts[1]
            if ctelem_parts[0] == "P2A":
                telem_structure['PANEL_TEMP']['P2']['A'] = ctelem_parts[1]
            if ctelem_parts[0] == "P2B":
                telem_structure['PANEL_TEMP']['P2']['B'] = ctelem_parts[1]
            if ctelem_parts[0] == "P2C":
                telem_structure['PANEL_TEMP']['P2']['C'] = ctelem_parts[1]
        return telem_structure
