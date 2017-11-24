import abc
import inspect
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

    DEFAULT_STEP_REWARD = -1
    LAP_REWARD = 100
    CHECKPOINT_REWARD = 1
    END_REWARD = 1000

    END_EPISODE_THRESHOLD = 30
    END_DETECTION_REWARD_REFUND = END_EPISODE_THRESHOLD - 1

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
            self.CHECKPOINT_LOCATIONS = list(self._generate_checkpoints(64, 36, 584, 444)) 
            self._checkpoint_tracker = [[False for i in range(len(self.CHECKPOINT_LOCATIONS))] for j in range(3)]
            self.last_known_ckpt = -1
        
        # Nothing to do on the first call to reset()
        if self.reset_count > 0:

            if self.episode_over:
                self._navigate_post_race_menu()
                self.episode_over = False
            else:
                self.controller_server.send_controls(ControllerState.NO_OP, start_button=1)
                self.controller_server.send_controls(ControllerState.NO_OP)
                self.controller_server.send_controls(ControllerState.JOYSTICK_DOWN)
                self.controller_server.send_controls(ControllerState.NO_OP)
                self.controller_server.send_controls(ControllerState.A_BUTTON)
                for i in range(77):
                    self.controller_server.send_controls(ControllerState.NO_OP)

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
            if cur_lap > self.lap:
                self.lap = cur_lap
                cprint('Lap %s!' % self.lap, 'green')
                return self.LAP_REWARD

            elif self.ENABLE_CHECKPOINTS and cur_ckpt > -1 and not self._checkpoint_tracker[self.lap - 1][cur_ckpt]:
                self._checkpoint_tracker[self.lap - 1][cur_ckpt] = True
                #cprint('CHECKPOINT achieved!', 'red')
                return self.CHECKPOINT_REWARD
            
            else:
                return self.DEFAULT_STEP_REWARD

    def _get_lap(self):
        # The first checkpoint is the upper left corner. It's value should tell us the lap.
        ckpt_val = self._evaluate_checkpoint(self.CHECKPOINT_LOCATIONS[0])

        # If it is unknown, assume same lap (character icon is likely covering the corner)
        return ckpt_val if ckpt_val != -1 else self.lap

    def _generate_checkpoints(self, min_x, min_y, max_x, max_y):
        # TODO: I'm sure this can/should be more pythonic somehow

        # Sample 4 pixels for each checkpoint to reduce the
        # likelihood of a pixel matching the color by chance

        # Top
        for i in range((max_x - min_x) / 2):
            x_val = min_x + i*2
            y_val = min_y
            yield [(x_val, y_val), (x_val + 1, y_val), (x_val, y_val + 1), (x_val + 1, y_val + 1)]

        # Right-side
        for i in range((max_y - min_y) / 2):
            x_val = max_x
            y_val = min_y + i*2
            yield [(x_val, y_val), (x_val + 1, y_val), (x_val, y_val + 1), (x_val + 1, y_val + 1)]
        
        # Bottom
        for i in range((max_x - min_x) / 2):
            if i == 0: # Skip the bottom right corner (for some reason MK doesn't draw it)
                continue
            x_val = max_x - i*2
            y_val = max_y
            yield [(x_val, y_val), (x_val + 1, y_val), (x_val, y_val + 1), (x_val + 1, y_val + 1)]
        
        # Left-side
        for i in range((max_y - min_y) / 2):
            x_val = min_x
            y_val = max_y - i*2
            yield [(x_val, y_val), (x_val + 1, y_val), (x_val, y_val + 1), (x_val + 1, y_val + 1)]

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

            self.last_known_ckpt = checkpoint
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
        frame = 0
        cur_row = 0
        cur_col = 0

        while frame < 284:
            action = ControllerState.NO_OP

            #  10 - Nintendo screen
            #  80 - Mario Kart splash screen
            # 120 - Select number of players
            # 125 - Select GrandPrix or TimeTrials
            # 130 - Select TimeTrials
            # 132 - Select Begin
            # 134 - OK
            # 160 - Select player
            # 162 - OK
            # 202 - Select map series
            # 230 - Select map choice
            # 232 - OK
            # 263 - Toggle through HUD options
            # 284 - <Level loaded; turn over control>
            if frame in [10, 80, 120, 130, 132, 134, 160, 162, 202, 230, 232]:
                action = ControllerState.A_BUTTON
            elif frame in [125]:
                action = ControllerState.JOYSTICK_DOWN

            # Frame 150 is the 'Player Select' screen
            if frame == 150:
                print('Player row: ' + str(self.PLAYER_ROW))
                print('Player col: ' + str(self.PLAYER_COL))

                if cur_row != self.PLAYER_ROW:
                    action = ControllerState.JOYSTICK_DOWN
                    cur_row += 1

            if frame in range(151, 156) and frame % 2 == 0:
                if cur_col != self.PLAYER_COL:
                    action = ControllerState.JOYSTICK_RIGHT
                    cur_col += 1

            # Frame 195 is the 'Map Select' screen
            if frame == 195:
                cur_row = 0
                cur_col = 0
                print('Map series: ' + str(self.MAP_SERIES))
                print('Map choice: ' + str(self.MAP_CHOICE))

            if frame in range(195, 202) and frame %2 == 0:
                if cur_col != self.MAP_SERIES:
                    action = ControllerState.JOYSTICK_RIGHT
                    cur_col += 1

            if frame in range(223, 230) and frame %2 == 0:
                if cur_row != self.MAP_CHOICE:
                    action = ControllerState.JOYSTICK_DOWN
                    cur_row += 1

            if self.ENABLE_CHECKPOINTS:
                # Just as the course loads, change the HUD view
                if frame in [263, 265]:
                    self.controller_server.send_controls(ControllerState.NO_OP, r_cbutton=1)
                    frame += 1
                    continue

            if action != ControllerState.NO_OP:
                print('Frame ' + str(frame) + ': ' + str(action))

            self.controller_server.send_controls(action)
            frame += 1

    def _navigate_post_race_menu(self):
        frame = 0
        while frame < 323:
            action = ControllerState.NO_OP

            # Post race menu (previous choice selected by default)
            # - Retry
            # - Course Change
            # - Driver Change
            # - Quit
            # - Replay
            # - Save Ghost

            # 245 - Times screen
            # 260 - Post race menu
            # 323 - <Level loaded; turn over control>
            if frame in [245, 260]:
                action = ControllerState.A_BUTTON

            if action != ControllerState.NO_OP:
                print('Frame ' + str(frame) + ': ' + str(action))

            self.controller_server.send_controls(action)
            frame += 1

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
