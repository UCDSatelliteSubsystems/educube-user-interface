from collections import namedtuple

ADC_FIELDS = (
    'SUN_SENSORS', #
    'SUN_DIR'    , #
    'MAGNO_TORQ' , #
    'REACT_WHEEL', #
    'MPU_ACC'    , #
    'MPU_GYR'    , #
    'MPU_MAG'    , #
)

ADCTelemetry = namedtuple('ADCTelemetry', ADC_FIELDS)

# structures of subfields:
SunSensor = namedtuple('SunSensor', ('FRONT', 'BACK', 'LEFT', 'RIGHT'))
MagTorqs  = namedtuple('MagTorqs', ('X','Y'))
MPUAcc    = namedtuple('MPUAcc', ('X', 'Y', 'Z'))
MPUGyr    = namedtuple('MPUGyr', ('X', 'Y', 'Z'))
MPUMag    = namedtuple('MPUMag', ('X', 'Y', 'Z'))

def _magnetorquer_sign(p, n):
    return (1 if p and not n else -1 if n and not p else 0)

def parse_magnetorquer_telemetry(x_p, x_n, y_p, y_n):
    """Process magnetorquer telemetry

    MAG telem gives ('X_P', 'X_N', 'Y_P', 'Y_N'). The parsed telemetry
    packet reduces this to +1/0/-1, depending on setting.

    """
    return MagTorqs(
        X=_magnetorquer_sign(int(x_p), int(x_n)), 
        Y=_magnetorquer_sign(int(y_p), int(y_n))
    )


def _parse_adc_telem(telem):
    """Extract and process telemetry structure for ADC."""

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

    # magnetorquers
    mag_torqs = parse_magnetorquer_telemetry(*_chip_telem['MAG'])

    # reaction wheel
    react_wheel = _chip_telem['WHL']

    # MPU
    mpu_acc = MPUAcc(*_chip_telem['MPU_ACC'])
    mpu_gyr = MPUGyr(*_chip_telem['MPU_GYR'])
    mpu_mag = MPUMag(*_chip_telem['MPU_MAG'])

    return ADCTelemetry(
        SUN_SENSORS = sun_sensors, 
        SUN_DIR     = sun_dir    , 
        MAGNO_TORQ  = mag_torqs  , 
        REACT_WHEEL = react_wheel, 
        MPU_ACC     = mpu_acc    , 
        MPU_GYR     = mpu_gyr    , 
        MPU_MAG     = mpu_mag
    )
