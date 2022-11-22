from collections import namedtuple

EPS_FIELDS = (
    'INA'        , #
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
INA_FIELDS = (
    'name',
    'address',
    'shunt_V',
    'bus_V',
    'current_mA',
    'power_mW', 
    'switch_enabled',
    'command_id'
)

INATelem  = namedtuple('INATelem', INA_FIELDS)
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

def parse_switch_status(*parts):
    """Switch status for switchable boards."""
    return {k : int(p) for k, p in zip(('R', '1', '2', '3'), parts)}

def parse_ina_telemetry(ina_parts, switch_status):
    """Process telemetry structure for individual INA chip.

    ina_parts is a tuple with (addr, voltage, current).

    switch_status is a lookup dictionary with the I_E part of the ADC
    telemetry.

    """
    _addr, _voltage, _current = ina_parts

    # calculate power
    _power = '{:.2f}'.format(float(_voltage) * float(_current))

    # board identifier
    _id = EPS_INA_COMMAND_ID.get(_addr, None)

    # switch status
    _switch_enabled = switch_status.get(_id, 1)
    
    # assemble telemetry info
    return INATelem(
        name           = EPS_INA_NAME.get(_addr, None),
        address        = _addr,
        shunt_V        = None,
        bus_V          = _voltage,
        current_mA     = _current,
        power_mW       = _power,
        switch_enabled = _switch_enabled,
        command_id     = _id
    )

CHARGE_STATUS_LOOKUP = {
    '1' : True,
    '0' : False,
}

def parse_charging_status(s):
    return CHARGE_STATUS_LOOKUP.get(s, None)

def _parse_eps_telem(telem):
    """Extract and process telemetry structure for EPS."""
    _chip_telem = dict()
    for ct in telem:
        _chip_telem_id, *_chip_telem_parts = ct.split(',')
        if _chip_telem_id == 'I':
            key = 'I{ina_id}'.format(ina_id = _chip_telem_parts[0])
            _chip_telem[key] = _chip_telem_parts
        else:
            _chip_telem[_chip_telem_id] = _chip_telem_parts

    # get chip enabled data
    _switch_status = parse_switch_status(*_chip_telem.pop('I_E'))
            
    # handle EPS INA chips. 
    _ina_chips = (
        val for key, val in _chip_telem.items() if key.startswith('I')
    )
    ina_telem = [
        parse_ina_telemetry(_ina_parts, _switch_status)
        for _ina_parts in _ina_chips
    ]

    # battery condition monitor
    # 'temp', 'voltage', 'current'
    ds2438_telem = DS2438(*_chip_telem['DA'])

    # battery temperatures
    ds18b20_a_telem = DS18B20(_chip_telem.get('DB', [None])[0])
    ds18b20_b_telem = DS18B20(_chip_telem.get('DC', [None])[0])

    # need error handling here???? not trivial to achieve using get. EAFP??? 
    charging_status = parse_charging_status(*_chip_telem.get('C', [None]))

    return EPSTelemetry(
        INA       = ina_telem      ,
        DS2438    = ds2438_telem   ,
        DS18B20_A = ds18b20_a_telem,
        DS18B20_B = ds18b20_b_telem,
        CHARGING  = charging_status
    )
