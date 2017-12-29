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

    LAP_COLOR_MAP = {(214, 156, 222): 1,
                     (198, 140, 198): 2,
                     (66, 49, 66): 3}

    DEFAULT_STEP_REWARD = -1
    LAP_REWARD = 100
    CHECKPOINT_REWARD = 100
    END_REWARD = 1000
    END_DETECTION_REWARD_REFUND = 215

    END_EPISODE_THRESHOLD = 30

    PLAYER_ROW = 0
    PLAYER_COL = 0

    MAP_SERIES = 0
    MAP_CHOICE = 0

    ENABLE_CHECKPOINTS = False

    def __init__(self, character='mario'):
        super(MarioKartEnv, self).__init__(mk_config['ROM_NAME'])
        self.end_episode_confidence = 0
        self._set_character(character)

    def _reset(self):
        
        self.lap = 1

        if self.ENABLE_CHECKPOINTS:
            self._checkpoint_tracker = [[False for i in range(len(self.CHECKPOINTS))] for j in range(3)]
        
        # Nothing to do on the first call to reset()
        if self.reset_count > 0:

            if self.episode_over:
                self._wait(count=59)
                self._navigate_post_race_menu()
                self._wait(count=40, wait_for='map select screen')
                self._navigate_map_select()
                self._wait(count=50, wait_for='race to load')
                self.episode_over = False
            else:
                self.controller_server.send_controls(ControllerState.NO_OP, start_button=1)
                self._act(ControllerState.NO_OP)
                self._press_button(ControllerState.JOYSTICK_DOWN)
                self._press_button(ControllerState.A_BUTTON)
                self._wait(count=76, wait_for='race to load')


        return super(MarioKartEnv, self)._reset()

    def _get_reward(self):
        cur_lap = self._get_lap()

        if self.ENABLE_CHECKPOINTS:
            cur_ckpt = self._get_current_checkpoint()

        #cprint('Get Reward called!','yellow')
        if self.episode_over:
            # Refund the reward lost in the frames between the race finish and end episode detection
            return self.END_DETECTION_REWARD_REFUND + self.END_REWARD
        else:
            if cur_lap != self.lap:
                self.lap = cur_lap
                cprint('Lap %s!' % self.lap, 'red')
                return self.LAP_REWARD

            elif self.ENABLE_CHECKPOINTS and cur_ckpt > -1 and not self._checkpoint_tracker[self.lap - 1][cur_ckpt]:

                # Only allow sequential forward achievement, no backward or skipping allowed. 
                # e.g. If you hit checkpoint 6, you must have hit all prior checkpoints (1-5)
                #      on this lap for it to count
                if not all(self._checkpoint_tracker[self.lap - 1][:-(len(self.CHECKPOINTS)-cur_ckpt)]):
                    #cprint('CHECKPOINT hit but not achieved (not all prior points were hit)!', 'red')
                    return self.DEFAULT_STEP_REWARD

                cprint('CHECKPOINT achieved!', 'red')
                self._checkpoint_tracker[self.lap - 1][cur_ckpt] = True
                return self.CHECKPOINT_REWARD
            else:
                return self.DEFAULT_STEP_REWARD

    def _get_lap(self):
        pix_arr = self.numpy_array
        point_a = IMAGE_HELPER.GetPixelColor(pix_arr, 203, 51)
        if point_a in self.LAP_COLOR_MAP:
            return self.LAP_COLOR_MAP[point_a]
        else:
            # TODO: What should this do? The pixel is not known, so assume same lap?
            return self.lap

    def _get_current_checkpoint(self):
        cps = map(self._checkpoint, self.CHECKPOINTS)
        if any(cps):
            #cprint('--------------------------------------------','red')
            #cprint('Checkpoints: %s' % cps, 'yellow')

            checkpoint = np.argmax(cps)

            #cprint('Checkpoint: %s' % checkpoint, 'cyan')

            return checkpoint
        else:
            # We're not at a checkpoint
            return -1

    def _checkpoint(self, checkpoint_points):
        pix_arr = self.numpy_array
        colored_dots = map(lambda point: IMAGE_HELPER.GetPixelColor(pix_arr, point[0], point[1]), 
                           checkpoint_points)
        pixel_means = np.mean(colored_dots, 1)
        #print colored_dots
        #cprint('Pixel means: %s' % pixel_means, 'cyan')
        return any(val < 100 for val in pixel_means)

    def _evaluate_end_state(self):
        #cprint('Evaluate End State called!','yellow')
        pix_arr = self.numpy_array

        upper_left = IMAGE_HELPER.GetPixelColor(pix_arr, 19, 19)
        upper_right = IMAGE_HELPER.GetPixelColor(pix_arr, 620, 19)
        bottom_left = IMAGE_HELPER.GetPixelColor(pix_arr, 19, 460)
        bottom_right = IMAGE_HELPER.GetPixelColor(pix_arr, 620, 460)

        if upper_left == upper_right == bottom_left == bottom_right:
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

        self._wait(count=50, wait_for='race to load')

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
        cur_row = 0
        cur_col = 0
        print('Player row: ' + str(self.PLAYER_ROW))
        print('Player col: ' + str(self.PLAYER_COL))

        if cur_row != self.PLAYER_ROW:
            self._press_button(ControllerState.JOYSTICK_DOWN)
            cur_row += 1

        while cur_col != self.PLAYER_COL:
            self._press_button(ControllerState.JOYSTICK_RIGHT)
            cur_col += 1

        # Select character
        self._press_button(ControllerState.A_BUTTON)

        # Press OK
        self._press_button(ControllerState.A_BUTTON)

    def _navigate_map_select(self):
        cur_row = 0
        cur_col = 0
        print('Map series: ' + str(self.MAP_SERIES))
        print('Map choice: ' + str(self.MAP_CHOICE))

        # Select map series
        while cur_col != self.MAP_SERIES:
            self._press_button(ControllerState.JOYSTICK_RIGHT)
            cur_col += 1
        self._press_button(ControllerState.A_BUTTON)

        # Select map choice
        while cur_row != self.MAP_CHOICE:
            self._press_button(ControllerState.JOYSTICK_DOWN)
            cur_row += 1
        self._press_button(ControllerState.A_BUTTON)

        # Press OK
        self._press_button(ControllerState.A_BUTTON)

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
        for _ in itertools.repeat(None, 5):
            self._press_button(ControllerState.JOYSTICK_UP)

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

        self.PLAYER_ROW, self.PLAYER_COLUMN = characters[character]
