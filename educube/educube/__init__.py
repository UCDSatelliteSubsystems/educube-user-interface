"""
educube.educube

"""

# standard library imports
#import logging

# local imports
from educube.telemetry_parser import parse_educube_telemetry

#TODO: does this actually need to do any logging at all?
#logger = logging.getLogger(__name__)

class EduCubeCommandError(Exception):
    """Custom Exception for bad command arguments."""

class EduCube:
    """Software EduCube representation."""

    def __init__(self):
        """Initialiser."""

        # identifiers for the boards
        self.board_ids = ('CDH', 'EPS', 'ADC', 'EXP', )

        # a dictionary to store the telemetry for each board
        self._board_telemetry = {board : None for board in self.board_ids}

    # the core interface for assembling commands
    def command(self, board, cmd, settings):
        """Convert command arguments into an EduCube command."""
        if cmd == 'T':
            return self.request_telemetry(board=board)

        if board == 'EPS':
            if cmd =='PWR_ON':
                return self.set_chip_power_on(**settings)

            if cmd =='PWR_OFF':
                return self.set_chip_power_off(**settings)

        if board == 'ADC':
            if cmd == 'MAG':
                return self.set_magtorquer(**settings)

            if cmd == 'REACT':
                return self.set_reaction_wheel(**settings)

        if board == 'EXP':
            if cmd =='HEAT':
                return self.set_thermal_panel(**settings)

        # we shouldn't have made it this far...
        _errmsg = f"Unknown command parameters {board=}, {cmd=}, {settings=}"
        raise EduCubeCommandError(_errmsg)

            
    # the core interface for updating and accessing telemetry
    def update_telemetry(self, telemetry_str, timestamp):
        """Parses a telemetry packet and updates the stored values."""

        _telemetry = parse_educube_telemetry(timestamp, telemetry_str)

        # something went wrong parsing the telemetry, don't update anything
        #TODO: should this raise an error?
        if not _telemetry:
            return

        # update the stored telemetry for the appropriate board
        #TODO: is Lock needed here? (threadsafe access to shared dictionary)
        self._board_telemetry[_telemetry.board] = _telemetry
        return _telemetry
        
    @property
    def latest_telemetry(self):
        """Return shallow copy of latest telemetry for each board."""
        return dict(**self._board_telemetry)
        
    def new_telemetry(self, cutoff):
        """Return telemetry received since cutoff time."""

        # get latest telemetry for all boards (order doesn't matter)
        _telemetry = list(self.latest_telemetry.values())

        # filter out empty or stale telemetry 
        return [t for t in _telemetry if t is not None and t.time > cutoff]

    # the individual commands
    #TODO: replace this with a cleaner, board-based interface?
    def request_telemetry(self, board):
        """Command to request telemetry. 

        Parameters
        ----------
        board : str
            The board identifier (CDH, ADC, EPS or EXP)

        """

        if board not in self.board_ids:
            errmsg = f'Invalid board identifier {board}'
            raise EduCubeCommandError(errmsg)

        return f'C|{board}|T'

    def set_blinky(self):
        """Command to light EduCube up like a Christmas Tree!"""
        return 'C|CDH|BLINKY'

    def set_magtorquer(self, axis, sign):
        """Command to turn magnetorquer on/off.

        Parameters
        ----------
        axis : str
            Sets the magnetorquer axis ('X' or 'Y')
        sign : int or str
            Sets final status of magnetorquer. Allowed values are 
            ('-', '0', '+') or (-1, 0, 1)

        """
        if axis.upper() not in ('X', 'Y'):
            errmsg = (
                'Invalid axis input for magnetorquer: '
                f'{axis} not in (\'X\', \'Y\')'
            )
            raise EduCubeCommandError(errmsg)

        if sign in (0, '0'):
            sign = '0'
        elif sign in (1, '+'):
            sign = '+'
        elif sign in (-1, '-'):
            sign = '-'
        else:
            errmsg = f'Invalid input for {axis} magnetorquer: {sign}'
            raise EduCubeCommandError(errmsg)

        return f'C|ADC|MAG|{axis.upper()}|{sign}'

    def set_reaction_wheel(self, val):
        """Command to set reaction wheel.

        Parameters
        ----------
        val : int
            Reaction wheel power value as a percentage

        """
        if val < -100 or val > 100:
            errmsg = f'Invalid value {val} for reaction wheel'
            raise EduCubeCommandError(errmsg)

        _sgn = '+' if val >= 0 else '-'
        _mag = int(abs(val))

        return f'C|ADC|REACT|{_sgn}|{_mag}'

    def set_thermal_panel(self, panel, val):
        """Command to set thermal panel.

        Parameters
        ----------
        panel : int
            Thermal panel number 
        val : int
            Thermal panel power value as a percentage

        """
        if panel not in (1,2):
            errmsg = (
                f'Invalid input for thermal experiment: panel {panel} '
                +'(panel must be in [1,2])'
            )
            raise EduCubeCommandError(errmsg)

        if val < 0 or val > 100:
            errmsg = (
                f'Invalid input for thermal experiment val {val} '
                +'(val should be between 0 and 100)'
            )
            raise EduCubeCommandError(errmsg)

        return f'C|EXP|HEAT|{panel}|{val}'

    def set_chip_power_on(self, command_id):
        """Command to turn on chip

        Parameters
        ----------
        command_id : 
            

        """
        return f'C|EPS|PWR_ON|{command_id}'

    def set_chip_power_off(self, command_id):
        """Command to turn off chip

        Parameters
        ----------
        command_id : 

        """
        return f'C|EPS|PWR_OFF|{command_id}'
