from collections import namedtuple
from datetime import datetime as dt

CDH_FIELDS = (
    'GPS_DATE'      , #
    'GPS_FIX'       , #
    'GPS_FIX_DEGMIN', #
    'GPS_META'      , #
    'SEPARATION'    , #
    'HOT_PLUG'      , #
)

CDHTelemetry = namedtuple('CDHTelemetry', CDH_FIELDS)

# structures of subfields:
GPSFix    = namedtuple('GPSFix', ('LAT', 'LON'))
GPSMeta   = namedtuple('GPSMeta', ('HDOP', 'ALT_CM', 'STATUS_INT', 'STATUS'))
SepStatus = namedtuple('SepStatus', ('ID', 'VAL'))
HotPlug   = namedtuple('HotPlug', ('ADC', 'COMM', 'EXP1', 'SPARE'))

# lookup tables
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

def _parse_cdh_telem(telem):
    """
    Extract and process telemetry structure.

    
    The CDH telemetry string contains telemetry from two chips:
        -- GPS
        -- Separation switch 

    """
    gps_telem, sep_telem = telem

    # parse gps_telem
    _, *gps_telem_parts = gps_telem.split(',')
    # this makes up for poor onboard formatting. NOTE: the default date when
    # no GPS telemetry received is 0/1/1T0:0:0, which is not a valid date!
    # This error is caught and None returned.
    try:
        gps_date = (dt.strptime(gps_telem_parts[0], '%y/%m/%dT%H:%M:%S')\
                      .strftime(format='%Y/%m/%d  %H:%M:%S')             )
    except ValueError:
        gps_date = None

    # should this be recast to a fixed precision string???
    gps_fix = GPSFix(
        LAT = float(gps_telem_parts[1])/1e7,
        LON = float(gps_telem_parts[2])/1e7
    )
    # Why doesn't this convert to degrees and minutes???
    gps_fix_degmin = GPSFix(
        LAT = float(gps_telem_parts[1])/1e7,
        LON = float(gps_telem_parts[2])/1e7
    )
    # extract the gps status -- if status unknown, return 'No Fix'
    gps_status_int = gps_telem_parts[5]
    gps_status = GPS_STATUS.get(gps_status_int, 'No Fix')
    # assemble GPS meta data
    gps_meta = GPSMeta(
        HDOP       = gps_telem_parts[3],
        ALT_CM     = gps_telem_parts[4],
        STATUS_INT = gps_status_int    ,
        STATUS     = gps_status
    ) 

    # parse sep_telem
    _, sep_status_id, *board_hotplug_statuses = sep_telem.split(',')

    separation = SepStatus(
        ID  = sep_status_id, 
        VAL = SEPARATION_STATUS[sep_status_id],
    )

    hotplug = HotPlug(
        ADC   = board_hotplug_statuses[0],
        COMM  = board_hotplug_statuses[1],
        EXP1  = board_hotplug_statuses[2],
        SPARE = board_hotplug_statuses[3]
    )

    return CDHTelemetry(
        GPS_DATE       = gps_date      ,
        GPS_FIX        = gps_fix       ,
        GPS_FIX_DEGMIN = gps_fix_degmin,
        GPS_META       = gps_meta      ,
        SEPARATION     = separation    ,
        HOT_PLUG       = hotplug
    )

