import os
import json

import logging
logger = logging.getLogger(__name__)

class TelemetryParser(object):

    BOARD_CONFIG = {
        "EPS": {
            "ID": "EPS",
            "parser": 'parse_eps_telem'
        },
        "CDH": {
            "ID": "CDH",
            "parser": 'parse_cdh_telem'
        },
        "EXP": {
            "ID": "EXP",
            "parser": 'parse_exp_telem'
        },
        "ADC": {
            "ID": "ADC",
            "parser": 'parse_adc_telem'
        }
    }
    TELEM_IDENTIFER = "T"

    last_board_telemetry = {}
    
    def __init__(self):
        pass

    def parse_telemetry(self, telem):
        logger.info("Parsing telemetry")
        telem_parts = telem['data'].split("|")
        if len(telem_parts) < 3:
            logger.warning("Empty telemetry")
            return
        telem_type, telem_board = telem_parts[:2]
        telem_struct = {
            "time": telem['time'],
            "type": telem_type,
            "board": telem_board,
            "telem": "|".join(telem_parts[2:])
        }
        if telem_type == self.TELEM_IDENTIFER:
            for bname, board in self.BOARD_CONFIG.items():
                if telem_board == board['ID']:
                    parser = getattr(self, board['parser'], None)
                    if parser:
                        parsed_telem = parser(telem_parts[2:])
                        telem_struct['data'] = parsed_telem
                        self.last_board_telemetry[board['ID']] = parsed_telem
                    else:
                        logger.error("Wrong parser defined for %s board: %s" % (bname, board['parser']))
        return telem_struct

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
                    "address": ctelem_parts[1],
                    "shunt_V": ctelem_parts[2],
                    "bus_V": ctelem_parts[3],
                    "current_mA": ctelem_parts[4]
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
                    "X+": ctelem_parts[1],
                    "X-": ctelem_parts[2],
                    "Y+": ctelem_parts[3],
                    "Y-": ctelem_parts[4]
                }
            # Handle reaction wheel data
            if ctelem_parts[0] == "ANG":
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


    def parse_cdh_telem(self, telem):
        telem_structure = {
            "GPS_DATE": None,
            "GPS_FIX": {},
            "GPS_META": {},
        }
        for chip_telem in telem:
            ctelem_parts = chip_telem.split(",")
            # Handle sunsensors
            if ctelem_parts[0] == "GPS":
                telem_structure["GPS_DATE"] = ctelem_parts[1]
                telem_structure["GPS_FIX"] = {
                    "LAT": ctelem_parts[2],
                    "LON": ctelem_parts[3],
                }
                telem_structure["GPS_META"] = {
                    "HDOP": ctelem_parts[4],
                    "ALT_CM": ctelem_parts[5],
                }
        return telem_structure


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
                    "address": ctelem_parts[1],
                    "shunt_V": ctelem_parts[2],
                    "bus_V": ctelem_parts[3],
                    "current_mA": ctelem_parts[4]
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
