import abc
import inspect
import itertools
import os
import yaml
from termcolor import cprint
from gym import spaces
from gym_mupen64plus.envs.mupen64plus_env \
  import Mupen64PlusEnv, ControllerState, IMAGE_HELPER
import numpy as np

mk_config = yaml.safe_load(open(os.path.join(os.path.dirname(inspect.stack()[0][1]), "smash_config.yml")))

###############################################
class SmashEnv(Mupen64PlusEnv):
    """Environment for Super Smash Bros.

    Allows custom stage and characters for self and opponents.
    Attributes:
        _curr_frame: int, the current frame
        _last_dmg_frame: int, the last frame we took damage
        _my_curr_dmg: int, the current health of the agent.
        _their_curr_dmg: int, the health of the opponent.
        _my_prev_dmg: int, the health of the agent at the previous update.
        _their_prev_dmg: int, the health of the opponent at the previous update.
        _is_taunting: bool, whether the agent just taunted.
        _my_char_pos: (int, int), the (row, col) of agent character in the
            selection screen.
        _their_char_pos: (int, int), the (row, col) of opponent character in the
            selection screen.
        _my_char_color: [int], button to press for agent character color.
        _their_char_color: [int], button to press for opponent character color.
        _map_pos: (int, int), the (row, col) of the map in the selection screen.
        _action_space: MultiDiscrete gym action space, possible allowed actions.
    """
    __metaclass__ = abc.ABCMeta

    # TODO: Add pixel info to figure out health of agent and opponent.

    # TODO: Read this from a config?
    FRAMES_PER_SECOND = 60
    FRAMES_PER_UPDATE = 1
    UPDATES_PER_SECOND = FRAMES_PER_SECOND / float(FRAMES_PER_UPDATE)

    def __init__(
            self, my_character='pikachu', their_character='luigi',
            my_character_color='CUP', their_character_color='CLEFT',
            map='DreamLand'):
        self._set_characters(my_character, their_character)
        self._set_characters_color(my_character_color, their_character_color)
        # Agent and opponent cannot be the same character and color.
        assert (self._my_char_pos != self._their_char_pos or
                self._my_char_color != self._their_char_color)
        self._set_map(map)

        super(SmashEnv, self).__init__(mk_config['ROM_NAME'])
        self._action_space = spaces.MultiDiscrete([[-80, 80],  # Joystick X-axis
                                                   [-80, 80],  # Joystick Y-axis
                                                   [  0,  1],  # A
                                                   [  0,  1],  # B
                                                   [  0,  0],  # RB- unused
                                                   [  0,  1],  # LB
                                                   [  0,  1],  # Z
                                                   [  0,  1]]) # C

    def _step(self, action):
        self._set_damages()
        # Append unneeded inputs.
        if action[5] == 1:
            self._is_taunting = True
        else:
            self._is_taunting = False
        num_missing = len(ControllerState.A_BUTTON) - len(action)
        full_action = action + [0] * num_missing
        return super(SmashEnv, self)._step(controls)

    def _reset(self):
        self._curr_frame = 0
        self._last_dmg_frame = 0
        self._my_curr_dmg = 0
        self._their_curr_dmg = 0
        self. _my_prev_dmg = 0
        self._their_prev_dmg = 0
        self._is_taunting = False

        # Nothing to do on the first call to reset()
        if self.reset_count > 0:

            # Make sure we don't skip frames while navigating the menus
            with self.controller_server.frame_skip_disabled():
                # TODO: Possibly allow exiting an in-progress map?
                pass
        return super(SmashEnv, self)._reset()


    # Agressiveness hyperparam- start applying if they go too long without
    # either taking or giving damage.
    def _get_aggressiveness_penalty(self):
        frames_since_dmg = self._curr_frame - self._last_dmg_frame
        # Apply if we've gone 4 seconds without any damage.
        if frames_since_dmg > 4 * FRAMES_PER_SECOND:
            # Penalty is tuned to be equal to taking 1 damage every 1 second.
            return 1.0 / UPDATES_PER_SECOND
        return 0.0

    def _get_dmg_reward(self):
        dmg_factor = 1.0
        death_factor = 200.0
        reward = 0.0
        dmg_taken = self._my_curr_dmg - self._my_prev_dmg
        dmg_given = self._their_curr_dmg - self._their_prev_dmg
        if dmg_taken > 0:
            reward -= dmg_taken * dmg_factor
        if dmg_given > 0:
            reward += dmg_given * dmg_factor
        # If the total damage resets to 0, it means a death happened.
        # TODO: This doesn't work in Saffron City, or if healing items are
        # enabled. Kind of a corner case though, and not relevant to
        # competitive, where only Dream Land is played with no items.
        if dmg_taken < 0 and self._my_curr_dmg == 0:
            reward -= death_factor
        if dmg_given < 0 and self._their_curr_dmg == 0:
            reward += death_factor
        if dmg_taken != 0 or dmg_given != 0:
            self._last_dmg_frame = self._curr_frame
        return reward

    def _get_taunt_reward(self):
        if self._is_taunting:
            # This does emotional damage.
            self._last_dmg_frame = self._curr_frame
            return 1.0
        return 0.0

    def _get_reward(self):
        return (self._get_taunt_reward() + self._get_dmg_reward() +
                self._get_aggressiveness_penalty())

    # Sets agent's and opponent's current damage.
    def _set_damages(self):
        # TODO: Implement.
        pass

    def _navigate_menu(self):
        self._navigate_start_menus()
        self._navigate_player_select()
        self._navigate_map_select()

    def _navigate_start_menus(self):
        # TODO: Implement.
        self._wait(count=10, wait_for='HAL Screen')


    def _navigate_player_select(self):
        print('Agent player (row, col): ', self._my_char_pos)
        print('Opponent player (row, col): ', self._their_char_pos)
        self._select_player(self._my_char_pos, self._my_char_color)

        # TODO: Select computer for opponent.
        # TODO: Allow custom opponent level.
        self._select_player(self._their_char_pos, self._their_char_color)
        self._press_button(ControllerState.START_BUTTON)

    def _select_player(self, pos, color):
        # Ensure we are in the upper left corner.
        self._press_button(ControllerState.JOYSTICK_UP, times=100)
        self._press_button(ControllerState.JOYSTICK_LEFT, times=100)

        # TODO: Tune this.
        down_offset = 10
        right_offset = 10
        down_multip = 10
        right_multip = 10
        # Navigate to character
        self._press_button(ControllerState.JOYSTICK_DOWN,
                          times=down_offset + down_multip * pos[1])
        self._press_button(ControllerState.JOYSTICK_RIGHT,
                           times=right_offset + right_multip * pos[0])
        self._press_button(color)


    def _navigate_map_select(self):
        print('Map position: ', self._map_pos)

        # Navigate to upper left corner if necessary.
        self._press_button(ControllerState.JOYSTICK_LEFT, times=5)
        self._press_button(ControllerState.JOYSTICK_UP, times=1)

        # Select map.
        self._press_button(ControllerState.JOYSTICK_RIGHT,
                           times=self._map_pos[0])
        self._press_button(ControllerState.JOYSTICK_DOWN,
                           times=self._map_pos[1])
        # Press start.
        self._press_button(ControllerState.START_BUTTON)

    def _navigate_pause_screen(self):
        # TODO: Possibly implement, if we want to allow exiting the map.
        pass

    def _evaluate_end_state(self):
        return False

    def _load_config(self):
        self.config.update(yaml.safe_load(open(os.path.join(os.path.dirname(inspect.stack()[0][1]), "smash.yml"))))

    def _validate_config(self):
        print("validate sub")
        gfx_plugin = self.config["GFX_PLUGIN"]
        if gfx_plugin not in self.END_RACE_PIXEL_COLORS:
            raise AssertionError("Video Plugin '" + gfx_plugin + "' not currently supported by Smash environment")

    def _set_characters(self, my_character, their_character):
        characters = {'luigi'       : (0, 0),
                      'mario'       : (0, 1),
                      'dk'          : (0, 2),
                      'link'        : (0, 3),
                      'samus'       : (0, 4),
                      'falcon'      : (0, 5),
                      'ness'        : (1, 0),
                      'yoshi'       : (1, 1),
                      'kirby'       : (1, 2),
                      'fox'         : (1, 3),
                      'pikachu'     : (1, 4),
                      'jigglypuff'  : (1, 5)}

        self._my_char_pos = characters[my_character]
        self._their_char_pos = characters[their_character]

    def _set_characters_color(self, my_character_color, their_character_color):
        buttons = {'CUP'    : ControllerState.CU_BUTTON,
                   'CDOWN'  : ControllerState.CD_BUTTON,
                   'CLEFT'  : ControllerState.CL_BUTTON,
                   'CRIGHT' : ControllerState.CR_BUTTON}

        self._my_char_color = buttons[my_character_color]
        self._their_char_color = buttons[their_character_color]

    def _set_map(self, map):
        maps = {'PeachsCastle'       : (0, 0),
                'CongoJungle'        : (0, 1),
                'HyruleCastle'       : (0, 2),
                'PlanetZebes'        : (0, 3),
                'MushroomKingdom'    : (0, 4),
                'YoshisIsland'       : (1, 0),
                'DreamLand'          : (1, 1),
                'SectorZ'            : (1, 2),
                'SaffronCity'        : (1, 3),
                'Random'             : (1, 4)}

        self._map_pos = maps[map]
