import abc
import inspect
import itertools
import os
import yaml
from termcolor import cprint
from gym_mupen64plus.envs.mupen64plus_env \
  import Mupen64PlusEnv, ControllerState, IMAGE_HELPER
import numpy as np

mk_config = yaml.safe_load(open(os.path.join(os.path.dirname(inspect.stack()[0][1]), "mario_kart_config.yml")))

###############################################
class MarioKartEnv(Mupen64PlusEnv):
    __metaclass__ = abc.ABCMeta

    # Indicates the color value of the pixel at point (203, 51)
    # This is where the lap number is present in the default HUD
    LAP_COLOR_MAP = {(214, 156, 222): 1, # Lap 1
                     (198, 140, 198): 2, # Lap 2
                     ( 66,  49,  66): 3} # Lap 3

    HUD_PROGRESS_COLOR_VALUES = {(000, 000, 255): 1, #   Blue: Lap 1
                                 (255, 255, 000): 2, # Yellow: Lap 2
                                 (255, 000, 000): 3} #    Red: Lap 3

    DEFAULT_STEP_REWARD = -0.1
    LAP_REWARD = 100
    CHECKPOINT_REWARD = 0.5
    BACKWARDS_PUNISHMENT = -1
    END_REWARD = 1000

    END_EPISODE_THRESHOLD = 0

    PLAYER_ROW = 0
    PLAYER_COL = 0

    MAP_SERIES = 0
    MAP_CHOICE = 0

    ENABLE_CHECKPOINTS = False

    def __init__(self, character='mario', course='LuigiRaceway'):
        self._set_character(character)
        self._set_course(course)
        super(MarioKartEnv, self).__init__(mk_config['ROM_NAME'])
        self.end_episode_confidence = 0

    def _reset(self):
        
        self.lap = 1
        self.step_count_at_lap = 0
        self.last_known_lap = -1

        self.CHECKPOINT_LOCATIONS = list(self._generate_checkpoints(64, 36, 584, 444)) 
        if self.ENABLE_CHECKPOINTS:
            self._checkpoint_tracker = [[False for i in range(len(self.CHECKPOINT_LOCATIONS))] for j in range(3)]
            self.last_known_ckpt = -1
        
        # Nothing to do on the first call to reset()
        if self.reset_count > 0:

            # Make sure we don't skip frames while navigating the menus
            with self.controller_server.frame_skip_disabled():

                if self.episode_over:
                    self._wait(count=275)
                    self._navigate_post_race_menu()
                    self._wait(count=40, wait_for='map select screen')
                    self._navigate_map_select()
                    self._wait(count=50, wait_for='race to load')
                    self.episode_over = False
                    self.end_episode_confidence = 0
                else:
                    # Can't pause the race until the light turns green
                    if (self.step_count * self.controller_server.frame_skip) < 120:
                        steps_to_wait = 100 - (self.step_count * self.controller_server.frame_skip)
                        self._wait(count=steps_to_wait, wait_for='green light so we can pause')
                    self.controller_server.send_controls(ControllerState.NO_OP, start_button=1)
                    self._act(ControllerState.NO_OP)
                    self._press_button(ControllerState.JOYSTICK_DOWN)
                    self._press_button(ControllerState.A_BUTTON)
                    self._wait(count=76, wait_for='race to load')

        return super(MarioKartEnv, self)._reset()

    def _get_reward(self):
        #cprint('Get Reward called!','yellow')

        reward_to_return = 0
        cur_lap = self._get_lap()

        if self.ENABLE_CHECKPOINTS:
            cur_ckpt = self._get_current_checkpoint()

        if self.episode_over:
            # Scale out the end reward based on the total steps to get here; the fewer steps, the higher the reward
            reward_to_return = 5 * (1250 - self.step_count) + self.END_REWARD #self.END_REWARD * (5000 / self.step_count) - 3000
        else:
            if cur_lap > self.lap:
                self.lap = cur_lap
                cprint('Lap %s!' % self.lap, 'green')

                # Scale out the lap reward based on the steps to get here; the fewer steps, the higher the reward
                steps_this_lap = self.step_count - self.step_count_at_lap
                reward_to_return = self.LAP_REWARD # TODO: Figure out a good scale here... number of steps required per lap will vary depending on the course; don't want negative reward for completing a lap
                self.step_count_at_lap = self.step_count

            elif (self.ENABLE_CHECKPOINTS and cur_ckpt > -1 and
                  not self._checkpoint_tracker[self.last_known_lap - 1][cur_ckpt]):

                # TODO: Backwards across a lap boundary incorrectly grants a checkpoint reward
                #       Need to investigate further. Might need to restore check for sequential checkpoints

                #cprint(str(self.step_count) + ': CHECKPOINT achieved!', 'green')
                self._checkpoint_tracker[self.lap - 1][cur_ckpt] = True
                reward_to_return = self.CHECKPOINT_REWARD # TODO: This should reward per progress made. It seems as though currently, by going too fast, you could end up skipping over some progress rewards, which would encourage driving around a bit to achieve those rewards. Should reward whatever progress was achieved during the step (perhaps multiple 'checkpoints')

            elif (self.ENABLE_CHECKPOINTS and ( cur_lap < self.last_known_lap or
                                               cur_ckpt < self.last_known_ckpt)):
                
                #cprint(str(self.step_count) + ': BACKWARDS!!', 'red')
                self._checkpoint_tracker[self.lap - 1][self.last_known_ckpt] = False
                reward_to_return = self.BACKWARDS_PUNISHMENT

            else:
                reward_to_return = self.DEFAULT_STEP_REWARD

        if self.ENABLE_CHECKPOINTS:
            self.last_known_ckpt = cur_ckpt
        self.last_known_lap = cur_lap
        return reward_to_return

    def _get_lap(self):
        # The first checkpoint is the upper left corner. It's value should tell us the lap.
        ckpt_val = self._evaluate_checkpoint(self.CHECKPOINT_LOCATIONS[0])

        # If it is unknown, assume same lap (character icon is likely covering the corner)
        return ckpt_val if ckpt_val != -1 else self.lap

    def _generate_checkpoints(self, min_x, min_y, max_x, max_y):
        i, x, y = 0, min_x - 2, min_y # Start just left of the upper left corner
        for dx, dy in (2, 0), (0, 2), (-2, 0), (0, -2): # Iterate deltas for each direction (right, down, left, up)
            x, y = x + dx, y + dy # Step into the rectangle
            while x in range(min_x, max_x + 1) and y in range(min_y, max_y + 1): # Stay within the bounds of the rectangle
                # Skip the bottom right corner (for some reason MK doesn't draw it)
                # Skip the upper left corner the second time to not duplicate (i.e. not the very first iteration)
                if not (x == max_x and y == max_y) and \
                   not (x == min_x and y == min_y and i > 0):
                    # Sample 4 pixels for each point to reduce the likelihood of a pixel matching the color by chance
                    yield [(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)]
                x, y = x + dx, y + dy # Step along the delta direction
            i, x, y = i + 1, x - dx, y - dy # Step back once before changing direction

    def _get_current_checkpoint(self):
        checkpoint_values = map(self._evaluate_checkpoint, self.CHECKPOINT_LOCATIONS)

        # Check if we have achieved any checkpoints
        if any(val > -1 for val in checkpoint_values):
            
            # argmin tells us the first index with the lowest value
            index_of_lowest_val = np.argmin(checkpoint_values)

            if index_of_lowest_val != 0:
                # If the argmin is anything but 0, we have achieved
                # all the checkpoints up through the prior index
                checkpoint = index_of_lowest_val - 1
            else:
                # If the argmin is at index 0, they are all the same value,
                # which means we've hit all the checkpoints for this lap
                checkpoint = len(checkpoint_values) - 1
            
            #if self.last_known_ckpt != checkpoint:
            #    cprint('--------------------------------------------','red')
            #    cprint('Checkpoints: %s' % checkpoint_values, 'yellow')
            #    cprint('Checkpoint: %s' % checkpoint, 'cyan')

            return checkpoint
        else:
            # We haven't hit any checkpoint yet :(
            return -1

    # https://stackoverflow.com/a/3844948
    # Efficiently determines if all items in a list are equal by 
    # counting the occurrences of the first item in the list and 
    # checking if the count matches the length of the list:
    def all_equal(self, some_list):
        return some_list.count(some_list[0]) == len(some_list)

    def _evaluate_checkpoint(self, checkpoint_points):
        pix_arr = self.numpy_array
        checkpoint_pixels = map(lambda point: IMAGE_HELPER.GetPixelColor(pix_arr, point[0], point[1]), 
                                checkpoint_points)

        #print(checkpoint_pixels)
        
        # If the first pixel is not a valid color, no need to check the other three
        if not checkpoint_pixels[0] in self.HUD_PROGRESS_COLOR_VALUES:
            return -1
        # If the first pixel is good, make sure the other three match
        elif not self.all_equal(checkpoint_pixels):
            return -1
        # If all are good, return the corresponding value
        else:
            return self.HUD_PROGRESS_COLOR_VALUES[checkpoint_pixels[0]]

    def _evaluate_end_state(self):
        #cprint('Evaluate End State called!','yellow')
        pix_arr = self.numpy_array

        point_a = IMAGE_HELPER.GetPixelColor(pix_arr, 203, 51)
        
        if point_a in self.LAP_COLOR_MAP:
            self.end_episode_confidence += 1
        else:
            self.end_episode_confidence = 0

        if self.end_episode_confidence > self.END_EPISODE_THRESHOLD:
            return True
        else:
            return False

    def _navigate_menu(self):
        self._wait(count=10, wait_for='Nintendo screen')
        self._press_button(ControllerState.A_BUTTON)

        self._wait(count=68, wait_for='Mario Kart splash screen')
        self._press_button(ControllerState.A_BUTTON)

        self._wait(count=68, wait_for='Game Select screen')
        self._navigate_game_select()

        self._wait(count=14, wait_for='Player Select screen')
        self._navigate_player_select()

        self._wait(count=31, wait_for='Map Select screen')
        self._navigate_map_select()

        self._wait(count=46, wait_for='race to load')
        
        # Change HUD View twice to get to the one we want:
        self._cycle_hud_view(times=2)

    def _navigate_game_select(self):
        # Select number of players (1 player highlighted by default)
        self._press_button(ControllerState.A_BUTTON)
        self._wait(count=3, wait_for='animation')

        # Select GrandPrix or TimeTrials (GrandPrix highlighted by default - down to switch to TimeTrials)
        self._press_button(ControllerState.JOYSTICK_DOWN)
        self._wait(count=3, wait_for='animation')

        # Select TimeTrials
        self._press_button(ControllerState.A_BUTTON)

        # Select Begin
        self._press_button(ControllerState.A_BUTTON)

        # Press OK
        self._press_button(ControllerState.A_BUTTON)

    def _navigate_player_select(self):
        print('Player row: ' + str(self.PLAYER_ROW))
        print('Player col: ' + str(self.PLAYER_COL))

        # Character selection is remembered each time, so ensure upper-left-most is selected
        self._press_button(ControllerState.JOYSTICK_UP)
        self._press_button(ControllerState.JOYSTICK_LEFT, times=3)

        # Navigate to character
        self._press_button(ControllerState.JOYSTICK_DOWN, times=self.PLAYER_ROW)
        self._press_button(ControllerState.JOYSTICK_RIGHT, times=self.PLAYER_COL)

        # Select character
        self._press_button(ControllerState.A_BUTTON)

        # Press OK
        self._press_button(ControllerState.A_BUTTON)

    def _navigate_map_select(self):
        print('Map series: ' + str(self.MAP_SERIES))
        print('Map choice: ' + str(self.MAP_CHOICE))

        # Map series selection is remembered each time, so ensure left-most is selected
        self._press_button(ControllerState.JOYSTICK_LEFT, times=3)

        # Select map series
        self._press_button(ControllerState.JOYSTICK_RIGHT, times=self.MAP_SERIES)
        self._press_button(ControllerState.A_BUTTON)

        # Map choice selection is remembered each time, so ensure top-most is selected
        self._press_button(ControllerState.JOYSTICK_UP, times=3)

        # Select map choice
        self._press_button(ControllerState.JOYSTICK_DOWN, times=self.MAP_CHOICE)
        self._press_button(ControllerState.A_BUTTON)

        # Press OK
        self._press_button(ControllerState.A_BUTTON)

    def _cycle_hud_view(self, times=1):
        for _ in itertools.repeat(None, times):
            self.controller_server.send_controls(ControllerState.NO_OP, r_cbutton=1)
            self._act(ControllerState.NO_OP)

    def _navigate_post_race_menu(self):
        # Times screen
        self._press_button(ControllerState.A_BUTTON)
        self._wait(count=13)

        # Post race menu (previous choice selected by default)
        # - Retry
        # - Course Change
        # - Driver Change
        # - Quit
        # - Replay
        # - Save Ghost

        # Because the previous choice is selected by default, we navigate to the top entry so our
        # navigation is consistent. The menu doesn't cycle top to bottom or bottom to top, so we can
        # just make sure we're at the top by hitting up a few times
        self._press_button(ControllerState.JOYSTICK_UP, times=5)

        # Now we are sure to have the top entry selected
        # Go down to 'course change'
        self._press_button(ControllerState.JOYSTICK_DOWN)
        self._press_button(ControllerState.A_BUTTON)

    def _set_character(self, character):
        characters = {'mario'  : (0, 0),
                      'luigi'  : (0, 1),
                      'peach'  : (0, 2),
                      'toad'   : (0, 3),
                      'yoshi'  : (1, 0),
                      'd.k.'   : (1, 1),
                      'wario'  : (1, 2),
                      'bowser' : (1, 3)}

        self.PLAYER_ROW, self.PLAYER_COL = characters[character]

    def _set_course(self, course):
        courses = {'LuigiRaceway'     : (0, 0),
                   'MooMooFarm'       : (0, 1),
                   'KoopaTroopaBeach' : (0, 2),
                   'KalimariDesert'   : (0, 3),
                   'ToadsTurnpike'    : (1, 0),
                   'FrappeSnowland'   : (1, 1),
                   'ChocoMountain'    : (1, 2),
                   'MarioRaceway'     : (1, 3),
                   'WarioStadium'     : (2, 0),
                   'SherbetLand'      : (2, 1),
                   'RoyalRaceway'     : (2, 2),
                   'BowsersCastle'    : (2, 3),
                   'DKsJungleParkway' : (3, 0),
                   'YoshiValley'      : (3, 1),
                   'BansheeBoardwalk' : (3, 2),
                   'RainbowRoad'      : (3, 3)}

        self.MAP_SERIES, self.MAP_CHOICE = courses[course]
