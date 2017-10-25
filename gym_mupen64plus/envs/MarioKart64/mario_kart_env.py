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

    LAP_COLOR_MAP = {(214, 156, 222): 1,
                     (198, 140, 198): 2,
                     (66, 49, 66): 3}

    DEFAULT_STEP_REWARD = -1
    LAP_REWARD = 10
    CHECKPOINT_REWARD = 100
    END_REWARD = 1000
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
        # Nothing to do on the first call to reset()
        if self.reset_count > 0:
            
            self.lap = 1
            self._checkpoint_tracker = [[False for i in range(len(self.CHECKPOINTS))] for j in range(3)]

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
        lap = self._get_lap()
        cur_ckpt = self._get_current_checkpoint()

        #cprint('Get Reward called!','yellow')
        if self.episode_over:
            # Refund the reward lost in the frames between the race finish and end episode detection
            return self.END_DETECTION_REWARD_REFUND + self.END_REWARD
        else:
            if lap != self.lap:
                self.lap = lap
                cprint('Lap %s!' % self.lap, 'red')
                #return self.LAP_REWARD
                return self.CHECKPOINT_REWARD

            elif cur_ckpt > -1 and not self._checkpoint_tracker[self.lap - 1][cur_ckpt]:
                
                # Encourage forward, not backward. If you hit some checkpoint 6-10, you 
                # must have hit a checkpoint 1-5 on this lap for it to count
                # TODO: Bulletproof this... you could still go backwards until you hit 
                # checkpoint 5 and then start collecting them backwards... however unlikely
                # it should be more guaranteed. Or more likely, hit the first one and
                # then turn around to collect them in reverse
                if cur_ckpt >= 5 and not any(self._checkpoint_tracker[self.lap - 1][0:5]):
                    return self.DEFAULT_STEP_REWARD

                cprint('CHECKPOINT!', 'red')
                self._checkpoint_tracker[self.lap - 1][cur_ckpt] = True
                return self.CHECKPOINT_REWARD
            else:
                return self.DEFAULT_STEP_REWARD

    def _get_lap(self):
        pix_arr = self.pixel_array
        point_a = IMAGE_HELPER.GetPixelColor(pix_arr, 203, 51)
        if point_a in self.LAP_COLOR_MAP:
            return self.LAP_COLOR_MAP[point_a]
        else:
            # TODO: What should this do? The pixel is not known, so assume same lap?
            return self.lap

    #CHECKPOINTS = [
    #    (645, 424), (645, 416), (645, 408), (645, 400), (645, 392), (645, 384),
    #    (645, 376), (645, 368), (645, 360), (645, 352), (645, 344), (642, 336),
    #    (636, 328), (628, 323), (620, 322), (612, 324), (604, 329), (599, 337),
    #    (598, 345), (599, 353), (604, 361), (611, 366), (619, 371), (626, 375),
    #    (634, 380), (638, 388), (640, 395), (640, 403), (640, 411), (640, 419),
    #    (635, 427), (627, 434), (619, 440), (612, 446), (608, 454), (608, 462),
    #    (613, 470), (621, 475), (629, 475), (637, 471), (642, 463), (644, 455),
    #    (645, 447), (645, 439), (645, 431)
    #]

    #have_printed = False
    #def _get_position(self):
    #    pix_arr = self.pixel_array
    #    coloredDots = map(lambda point: IMAGE_HELPER.GetPixelColor(pix_arr, point[0]-80, point[1]-61), self.CHECKPOINTS)
    #    if not self.have_printed:
    #        print coloredDots
    #    pixel_mean = np.mean(coloredDots, 1)
    #    position = np.argmin(pixel_mean)
    #    cprint('Argmin: %s; Position: %s' % (pixel_mean, position), 'cyan')
    #    return position

    CHECKPOINTS = [
        #### Straight-away ####
        [(563, 317), (564, 317), (565, 317), (566, 317), (567, 317)],
        #### Around the first bend ####
        [(563, 285), (564, 285), (565, 285), (566, 285), (567, 285)],
        [(540, 259), (540, 260), (540, 261), (540, 262), (540, 263)],
        [(516, 286), (517, 286), (518, 286), (519, 286), (520, 286)],
        ##### The angled sections on etiher side of the tunnel #####
        [(553, 321), (554, 321), (554, 320), (555, 320), (555, 319)],
        [(547, 370), (548, 371), (549, 372), (550, 373)],
        #### They're making another left turn ####
        [(526, 397), (527, 397), (528, 397), (529, 397), (530, 397)],
        [(546, 412), (546, 413), (546, 414), (546, 415), (546, 416)],
        [(562, 398), (563, 398), (564, 398), (565, 398), (566, 398)],
        #### Straight-away to the line ####
        [(563, 380), (564, 380), (565, 380), (566, 380), (567, 380)]
    ]

    _checkpoint_tracker = [[False for i in range(len(CHECKPOINTS))] for j in range(3)]

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
        pix_arr = self.pixel_array
        colored_dots = map(lambda point: IMAGE_HELPER.GetPixelColor(pix_arr, point[0], point[1]), 
                          checkpoint_points)
        pixel_means = np.mean(colored_dots, 1)
        #print colored_dots
        #cprint('Pixel means: %s' % pixel_means, 'cyan')
        return any(val < 100 for val in pixel_means)

    def _evaluate_end_state(self):
        #cprint('Evaluate End State called!','yellow')
        pix_arr = self.pixel_array

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

            if action != ControllerState.NO_OP:
                print('Frame ' + str(frame) + ': ' + str(action))

            self.controller_server.send_controls(action)
            frame += 1

    def _navigate_post_race_menu(self):
        frame = 0
        while frame < 138:
            action = ControllerState.NO_OP

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
