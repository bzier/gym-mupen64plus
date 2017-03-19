import abc
import inspect
import os
import yaml
from termcolor import cprint
from gym_mupen64plus.envs.mupen64plus_env \
  import Mupen64PlusEnv, ControllerHTTPServer, IMAGE_HELPER

mk_config = yaml.safe_load(open(os.path.join(os.path.dirname(inspect.stack()[0][1]), "mario_kart_config.yml")))

###############################################
class MarioKartEnv(Mupen64PlusEnv):
    __metaclass__ = abc.ABCMeta

    LAP_COLOR_MAP = {(214, 156, 222): 1,
                     (198, 140, 198): 2,
                     (66, 49, 66): 3}

    DEFAULT_STEP_REWARD = -1
    LAP_REWARD = 10
    END_DETECTION_REWARD_REFUND = 215

    END_EPISODE_THRESHOLD = 30

    PLAYER_ROW = 0
    PLAYER_COL = 0

    MAP_SERIES = 0
    MAP_CHOICE = 0

    def __init__(self, character='mario'):
        super(MarioKartEnv, self).__init__(mk_config['ROM_NAME'])
        self.end_episode_confidence = 0
        self._set_character(character)
        self.lap = 1

    def _reset(self):
        if self.episode_over:
            self._navigate_post_race_menu()
            self.episode_over = False
        else:
            # TODO: Implement pause and reset
            pass

        return self._observe()

    def _get_reward(self):
        lap = self._get_lap()

        #cprint('Get Reward called!','yellow')
        if self.episode_over:
            # Refund the reward lost in the frames between the race finish and end episode detection
            return self.END_DETECTION_REWARD_REFUND
        else:
            if lap != self.lap:
                self.lap = lap
                return self.LAP_REWARD
            else:
                return self.DEFAULT_STEP_REWARD

    def _get_lap(self):
        pix_arr = self.pixel_array
        point_a = IMAGE_HELPER.GetPixelColor(pix_arr, 203, 50)
        if point_a in self.LAP_COLOR_MAP:
            return self.LAP_COLOR_MAP[point_a]
        else:
            # TODO: What should this do? The pixel is not known, so assume same lap?
            return self.lap

    def _evaluate_end_state(self):
        #cprint('Evaluate End State called!','yellow')
        pix_arr = self.pixel_array

        upper_left = IMAGE_HELPER.GetPixelColor(pix_arr, 19, 19)
        upper_right = IMAGE_HELPER.GetPixelColor(pix_arr, 620, 19)
        bottom_left = IMAGE_HELPER.GetPixelColor(pix_arr, 19, 460)
        bottom_right = IMAGE_HELPER.GetPixelColor(pix_arr, 620, 460)

        if upper_left == upper_right == bottom_left == bottom_right == IMAGE_HELPER.BLACK_PIXEL:
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
            action = ControllerHTTPServer.NOOP

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
            # 284 - <Level loaded; turn over control>
            if frame in [10, 80, 120, 130, 132, 134, 160, 162, 202, 230, 232]:
                action = ControllerHTTPServer.A_BUTTON
            elif frame in [125]:
                action = ControllerHTTPServer.JOYSTICK_DOWN

            # Frame 150 is the 'Player Select' screen
            if frame == 150:
                print('Player row: ', str(self.PLAYER_ROW))
                print('Player col: ', str(self.PLAYER_COL))

                if cur_row != self.PLAYER_ROW:
                    action = ControllerHTTPServer.JOYSTICK_DOWN
                    cur_row += 1

            if frame in range(151, 156) and frame % 2 == 0:
                if cur_col != self.PLAYER_COL:
                    action = ControllerHTTPServer.JOYSTICK_RIGHT
                    cur_col += 1

            # Frame 195 is the 'Map Select' screen
            if frame == 195:
                cur_row = 0
                cur_col = 0
                print('Map series: ', str(self.MAP_SERIES))
                print('Map choice: ', str(self.MAP_CHOICE))

            if frame in range(195, 202) and frame %2 == 0:
                if cur_col != self.MAP_SERIES:
                    action = ControllerHTTPServer.JOYSTICK_RIGHT
                    cur_col += 1

            if frame in range(223, 230) and frame %2 == 0:
                if cur_row != self.MAP_CHOICE:
                    action = ControllerHTTPServer.JOYSTICK_DOWN
                    cur_row += 1

            if action != ControllerHTTPServer.NOOP:
                print('Frame ', str(frame), ': ', str(action))

            self.controller_server.send_controls(action)
            frame += 1

    def _navigate_post_race_menu(self):
        frame = 0
        while frame < 138:
            action = ControllerHTTPServer.NOOP

            # Post race menu (previous choice selected by default)
            # - Retry
            # - Course Change
            # - Driver Change
            # - Quit
            # - Replay
            # - Save Ghost

            #  60 - Times screen
            #  75 - Post race menu
            # 138 - <Level loaded; turn over control>
            if frame in [60, 75]:
                action = ControllerHTTPServer.A_BUTTON

            if action != ControllerHTTPServer.NOOP:
                print('Frame ', str(frame), ': ', str(action))

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
