from collections import namedtuple

EXP_FIELDS = ('THERM_PWR'  , #
              'INA'        , #
              'PANEL_TEMP' , #
              )
EXPTelemetry = namedtuple('EXPTelemetry', EXP_FIELDS)

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
Panels = namedtuple('Panels', ('P1', 'P2'))
Panel  = namedtuple('Panel' , ('A', 'B', 'C'))

# lookup tables
EXP_INA_NAME = {
    '64' : 'Panel 1',
    '67' : 'Panel 2',
}

def _parse_exp_telem(telem):
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

    # panel temperatures. NOTE: there is a bug in the way this telemetry is
    # formed, meaning that the panel temperatures may be truncated. This
    # exception is caught and None returned
    panels = list()
    for n in (1, 2):
        panel = list()
        for p in ('A', 'B', 'C'):
            try:
                key = 'P{n}{p}'.format(n=n, p=p)
                panel.append(_chip_telem[key][0])
            except:
                panel.append(None)

        panels.append(Panel(*panel))
    panel_temp = Panels(*panels)

    out = EXPTelemetry(THERM_PWR  = therm_pwr ,
                       INA        = ina_telem ,
                       PANEL_TEMP = panel_temp )
    return out
