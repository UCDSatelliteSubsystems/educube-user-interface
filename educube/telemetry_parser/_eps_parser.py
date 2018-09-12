from collections import namedtuple

EPS_FIELDS = ('INA'        , #
              'DS2438'     , #
              'DS18B20_A'  , #
              'DS18B20_B'  , #
              'CHARGING'   , #
              )

EPSTelemetry = namedtuple('EPSTelemetry', EPS_FIELDS)

# structures of subfields:
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

def _parse_eps_telem(telem):
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
