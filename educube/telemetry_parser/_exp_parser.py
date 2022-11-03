"""
_exp_parser.py

Interface to parse parts of an EXP telemetry string.

# The EXP Telemetry Format

An EXP telemetry string looks like:

```
T|EXP|THERM_P1,0|THERM_P2,0|I,64,-0.09,0.00,-1.00|I,67,-0.08,0.00,-0.20|P1A,20.69|P1B,20.81|P1C,20.88|P2A,20.94|P2B,21.06|P2C,2
```

The telemetry parts consist of:

- `THERM_P?`: the power status of the two thermal panels
- `I`: telemetry from the INA boards for the two panels
- `P??`: temperature data from the 3 sensors on the 2 thermal panels


# Notes

- As with all telemetry packets, there is no check that the packet is received
  as it was transmitted.

- This is particularly bad here because the EduCube SPI protocol doesn't allow
  enough time for the EXP telemetry to by passed from the board to the
  CDH. This means that the telemetry data from panel 2 is routinely corrupted
  *unless it is directly accessed from the serial port on the EXP board*. This
  parser attempts to catch this bug and return an otherwise valid packet with
  None for those values that have been truncated. You are likely to get some
  odd temperature values that creep through though.

  The only way to fix this is in firmware. 

"""

# new arrangement: (June 2019)
# 
# instead of grouping by functionality, we want to group by panel. So, our
# telemetry will consist of two panels, and each panel will contain attributes
# therm_pwr, ina (which will have sub-attributes for current &c.), and
# temperature (with sub attributes A, B, C).

# standard library imports
from collections import namedtuple


EXP_FIELDS = (
    'panel1', # solar black
    'panel2', # solar white
)

EXPTelemetry = namedtuple('EXPTelemetry', EXP_FIELDS)

EXPPanelTelemetry = namedtuple(
    'EXPThermalTelemetry', ('therm_pwr', 'ina', 'temperature')
)

EXPTemperatureTelemetry = namedtuple(
    'EXPTemperatureTelemetry', ('A', 'B', 'C')
)


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

# lookup tables for INA panels
EXP_INA_NAME = {
    '64' : 'P1',
    '67' : 'P2',
}


def parse_ina_telemetry(ina_chip_parts):
    """Read INA telemetry as provided by EXP board."""
    
    # ina_chip_parts is a list 
    _address, _shunt_V, _bus_V, _current_mA = ina_chip_parts
    # TODO: what if the ina_chip_parts is corrupted?

    # calculate the power:
    _power_mW = '{:.2f}'.format(float(_bus_V) * float(_current_mA))

    return INATelem(
        name           = EXP_INA_NAME[_address],
        address        = _address              ,   
        shunt_V        = _shunt_V              ,
        bus_V          = _bus_V                ,
        current_mA     = _current_mA           ,
        power_mW       = _power_mW             ,
        switch_enabled = None                  ,
        command_id     = None
    )
           

def parse_temperature_telemetry(sensorA, sensorB, sensorC):
    return EXPTemperatureTelemetry(sensorA, sensorB, sensorC)



def _parse_exp_telem(telem):
    """Parser function for telemetry from EXP board."""

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
            try:
                _panel = EXP_INA_NAME[_chip_telem_parts[0]]
                _chip_telem_id = f'I{_panel}'
            except (KeyError, IndexError): # ignore corrupted _chip_telem_parts
                continue
            
        _chip_telem[_chip_telem_id] = _chip_telem_parts 

    # separate out the panel1 and panel2 telemetry parts. These are identified
    # by P1 or P2 appearing in the _chip_telem_id
    panels = dict()
    for panel in ('P1', 'P2'):
        # extract the telemetry for panel into a new dict. The keys are made
        # generic by removing the panel identifier from the key
        _panel_telem = {
            key.replace(panel, '') : _chip_telem[key]
            for key in _chip_telem if panel in key
        }   

        # handle the panel power status
        try:
            therm_pwr, = _panel_telem['therm_']
        except (KeyError, ValueError): 
            # either THERM_{panel} is missing from the packet or it is missing
            # its value
            therm_pwr = None

        # handle the INA current sensor and the temperature sensors
        ina_telem         = parse_ina_telemetry(_panel_telem['I'])
        temperature_telem = parse_temperature_telemetry(
            _panel_telem.get('A', (None,) )[0],
            _panel_telem.get('B', (None,) )[0],
            _panel_telem.get('C', (None,) )[0],
            )

        # store as a complete EXPPanelTelemetry object
        panels[panel] = EXPPanelTelemetry(
            therm_pwr   = therm_pwr,
            ina         = ina_telem,
            temperature = temperature_telem
            )


    return EXPTelemetry(
        panel1 = panels['P1'],
        panel2 = panels['P2']
    )




#    therm_pwr  = Panels(P1 = _chip_telem.get('THERM_P1', [None])[0],
#                        P2 = _chip_telem.get('THERM_P2', [None])[0] )
#
#    # this feels dangerous -- what if something else starts with I???
#    ina_chips = (val 
#                 for key, val in _chip_telem.items() if key.startswith('I'))
#    # exp ina format has shunt_V , but no switch_enabled???
#    ina_telem = [INATelem(name           = EXP_INA_NAME[ina_parts[0]]     ,
#                          address        = ina_parts[0]                   ,   
#                          shunt_V        = ina_parts[1]                   ,
#                          bus_V          = ina_parts[2]                   ,
#                          current_mA     = ina_parts[3]                   ,
#                          power_mW       = '{:.2f}'.format(              
#                                              float(ina_parts[2]) * 
#                                              float(ina_parts[3])  )      ,
#                          switch_enabled = None                           ,
#                          command_id     = None                            )
#                 for ina_parts in ina_chips                                 ]
#
#    # panel temperatures. NOTE: there is a bug in the way this telemetry is
#    # formed, meaning that the panel temperatures may be truncated. This
#    # exception is caught and None returned
#    panels = list()
#    for n in (1, 2):
#        panel = list()
#        for p in ('A', 'B', 'C'):
#            try:
#                key = 'P{n}{p}'.format(n=n, p=p)
#                panel.append(_chip_telem[key][0])
#            except:
#                panel.append(None)
#
#        panels.append(Panel(*panel))
#    panel_temp = Panels(*panels)
#
#    out = EXPTelemetry(THERM_PWR  = therm_pwr ,
#                       INA        = ina_telem ,
#                       PANEL_TEMP = panel_temp )
#    return out
