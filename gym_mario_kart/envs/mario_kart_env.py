from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

import array
import os
import signal
import subprocess
import threading
import time
import pygame
from termcolor import cprint

import gym
from gym import error, spaces, utils
from gym.utils import seeding

import numpy as np

import wx
wx.App()

###############################################
class Config:
    PORT_NUMBER = 8082

    SCR_W = 640
    SCR_H = 480
    SCR_D = 3

    DST_W = 640
    DST_H = 480
    DST_D = 3

    OFFSET_X = 400
    OFFSET_Y = 240

    DEFAULT_STEP_REWARD = -1
    END_DETECTION_REWARD_REFUND = 215

    ACTION_TIMEOUT = 5
    END_EPISODE_THRESHOLD = 30

    BLACK_PIXEL = (0, 0, 0)

    NOOP = [0, 0, 0, 0, 0]
    A_BUTTON = [0, 0, 1, 0, 0]
    JOYSTICK_UP = [0, 80, 0, 0, 0]
    JOYSTICK_DOWN = [0, -80, 0, 0, 0]
    JOYSTICK_LEFT = [-80, 0, 0, 0, 0]
    JOYSTICK_RIGHT = [80, 0, 0, 0, 0]

    PLAYER_ROW = 1
    PLAYER_COL = 1

    MAP_SERIES = 0
    MAP_CHOICE = 0

    MUPEN_CMD = 'mupen64plus'
    INPUT_DRIVER_PATH = '/home/brian/Programming/mupen64plus/mupen64plus-input-bot/mupen64plus-input-bot.so'
    ROM_PATH = '/home/brian/Programming/TensorKart/marioKart.n64'


###############################################
class InternalState:
    def __init__(self):
        self.running = False
        self.take_action = False
        self.action = [0, 0, 0, 0, 0]
        self.end_episode_confidence = 0
        self.is_end_episode = False
        self.numpy_array = None
        self.pixel_array = array.array('B', [0] * (Config.SCR_W * Config.SCR_H * Config.SCR_D))


###############################################
class ImageHelper:
    def GetPixelColor(self, image_array, x, y):
        base_pixel = (x + (y * Config.SCR_W)) * 3
        red = image_array[base_pixel + 0]
        green = image_array[base_pixel + 1]
        blue = image_array[base_pixel + 2]
        return (red, green, blue)


###############################################   
class XboxController:
    def __init__(self):
        try:
            pygame.init()
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
        except:
            print('unable to connect to Xbox Controller')


    def read(self):
        pygame.event.pump()
        x = self.joystick.get_axis(0)
        y = self.joystick.get_axis(1)
        a = self.joystick.get_button(0)
        b = self.joystick.get_button(2) # b=1, x=2
        rb = self.joystick.get_button(5)
        return [x, y, a, b, rb]


    def manual_override(self):
        pygame.event.pump()
        return self.joystick.get_button(4) == 1


###############################################
### Variables                               ###
###############################################

# Init contoller for manual override
REAL_CONTROLLER = XboxController()

INTERNAL_STATE = InternalState()
IMAGE_HELPER = ImageHelper()


###############################################
class MarioKartEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        INTERNAL_STATE.running = True
        self.controller_server = None
        self.controller_server_thread = None
        self._start_controller_server()
        self.emulator_process = None
        self._configure_environment()
        self.observation_space = spaces.Box(low=0, high=255,
                                            shape=(Config.SCR_H, Config.SCR_W, Config.SCR_D))

        self.action_space = spaces.Tuple((spaces.Box(low=-80, high=80, shape=1), # Joystick X-axis
                                          spaces.Box(low=-80, high=80, shape=1), # Joystick Y-axis
                                          spaces.Discrete(2), # A Button
                                          spaces.Discrete(2), # B Button
                                          spaces.Discrete(2))) # RB Button

    def _step(self, action):
        #cprint('Step called!','red')
        self._take_action(action)
        obs = self._observe()
        episode_over = self._evaluate_end_state()
        reward = self._get_reward(episode_over)

        return obs, reward, episode_over, {}

    def _take_action(self, action):
        #cprint('Take Action called!','red')
        INTERNAL_STATE.action = action
        INTERNAL_STATE.take_action = True

        # Wait for action to be taken:
        s = time.time()
        while INTERNAL_STATE.take_action and time.time() < s + Config.ACTION_TIMEOUT:
            pass

    def _observe(self):
        #cprint('Observe called!','red')
        self._update_pixels()

        return INTERNAL_STATE.numpy_array

    def _get_reward(self, episode_over):
        #cprint('Get Reward called!','red')
        if episode_over:
            # Refund the reward lost in the frames following the race finish until end episode detection
            return Config.END_DETECTION_REWARD_REFUND
        else:
            # Currently just -1 per step
            return Config.DEFAULT_STEP_REWARD

    def _update_pixels(self):
        #cprint('Update Pixels called!','red')
        screen = wx.ScreenDC()
        bmp = wx.Bitmap(Config.SCR_W, Config.SCR_H)
        mem = wx.MemoryDC(bmp)
        mem.Blit(0, 0, Config.SCR_W, Config.SCR_H, screen, Config.OFFSET_X, Config.OFFSET_Y)
        bmp.CopyToBuffer(INTERNAL_STATE.pixel_array)

        INTERNAL_STATE.numpy_array = np.frombuffer(INTERNAL_STATE.pixel_array, dtype=np.uint8)
        INTERNAL_STATE.numpy_array = INTERNAL_STATE.numpy_array.reshape(Config.SCR_H, Config.SCR_W, Config.SCR_D)

    def _evaluate_end_state(self):
        #cprint('Evaluate End State called!','red')
        pix_arr = INTERNAL_STATE.pixel_array

        upper_left = IMAGE_HELPER.GetPixelColor(pix_arr, 19, 19)
        upper_right = IMAGE_HELPER.GetPixelColor(pix_arr, 620, 19)
        bottom_left = IMAGE_HELPER.GetPixelColor(pix_arr, 19, 460)
        bottom_right = IMAGE_HELPER.GetPixelColor(pix_arr, 620, 460)

        if upper_left == upper_right == bottom_left == bottom_right == Config.BLACK_PIXEL:
            INTERNAL_STATE.end_episode_confidence += 1
        else:
            INTERNAL_STATE.end_episode_confidence = 0

        if INTERNAL_STATE.end_episode_confidence > Config.END_EPISODE_THRESHOLD:
            INTERNAL_STATE.is_end_episode = True

        return INTERNAL_STATE.is_end_episode

    def _kill_emulator(self):
        #cprint('Kill Emulator called!','red')
        self._take_action(Config.NOOP)
        if self.emulator_process is not None:
            self.emulator_process.kill()
        #self._take_action(Config.NOOP)

    def _close(self):
        cprint('Close called!','red')     
        INTERNAL_STATE.running = False
        self._kill_emulator()
        self._stop_controller_server()

    def _reset(self):
        cprint('Reset called!','red')
        #self._kill_emulator()
        #self._configure_environment()

        return self._observe()

    def _render(self, mode='human', close=False):
        pass

    def _stop_controller_server(self):
        #cprint('Stop Controller Server called!','red')
        if self.controller_server is not None:
            self.controller_server.shutdown()

    def _start_controller_server(self):
        server = HTTPServer(('', Config.PORT_NUMBER), ControllerServer)
        self.controller_server_thread = threading.Thread(target=server.serve_forever, args=())
        self.controller_server_thread.daemon = True
        self.controller_server_thread.start()
        self.controller_server = server
        print('ControllerServer started on port ', Config.PORT_NUMBER)
        
    def _configure_environment(self):
        cprint('Configure Env called!','red')
        self._start_emulator()
        self._navigate_menu()

    def _navigate_menu(self):
        frame = 0
        cur_row = 0
        cur_col = 0

        while frame < 284:
            action = Config.NOOP

            #  10 - Nintendo screen
            #  80 - Mario Kart splash screen
            # 120 - Select number of players
            # 125 - Select GrandPrix or TimeTrials
            # 130 - Select TimeTrials
            # 132 - Select Begin
            # 134 - OK
            # 160 - Select player
            # 162 - OK
            # 201 - Select map series
            # 230 - Select map choice
            # 232 - OK
            # 284 - <Level loaded; turn over control>
            if frame in [10, 80, 120, 130, 132, 134, 160, 162, 202, 230, 232]:
                action = Config.A_BUTTON
            elif frame in [125]:
                action = Config.JOYSTICK_DOWN

            # Frame 150 is the 'Player Select' screen
            if frame == 150:
                print('Player row: ', str(Config.PLAYER_ROW))
                print('Player col: ', str(Config.PLAYER_COL))

                if cur_row != Config.PLAYER_ROW:
                    action = Config.JOYSTICK_DOWN
                    cur_row += 1

            if frame in range(151, 156) and frame % 2 == 0:
                if cur_col != Config.PLAYER_COL:
                    action = Config.JOYSTICK_RIGHT
                    cur_col += 1

            # Frame 195 is the 'Map Select' screen
            if frame == 195:
                cur_row = 0
                cur_col = 0
                print('Map series: ', str(Config.MAP_SERIES))
                print('Map choice: ', str(Config.MAP_CHOICE))

            if frame in range(195, 202) and frame %2 == 0:
                if cur_col != Config.MAP_SERIES:
                    action = Config.JOYSTICK_RIGHT
                    cur_col += 1

            if frame in range(223, 230) and frame %2 == 0:
                if cur_row != Config.MAP_CHOICE:
                    action = Config.JOYSTICK_DOWN
                    cur_row += 1

            if action != Config.NOOP:
                print('Frame ', str(frame), ': ', str(action))

            self._take_action(action)
            frame += 1

    def _start_emulator(self,
                        res_w=Config.SCR_W,
                        res_h=Config.SCR_H,
                        input_driver_path=Config.INPUT_DRIVER_PATH,
                        rom_path=Config.ROM_PATH):

        cmd = Config.MUPEN_CMD + \
              " --resolution %ix%i" \
              " --input %s" \
              " %s" \
              % (res_w, res_h,
                 input_driver_path,
                 rom_path)

        print('Starting emulator with comand: %s' % cmd)

        self.emulator_process = subprocess.Popen(cmd.split(' '), shell=False, stderr=subprocess.STDOUT)
        emu_mon = EmulatorMonitor()
        monitor_thread = threading.Thread(target=emu_mon.monitor_emulator, args=[self.emulator_process])
        monitor_thread.daemon = True
        monitor_thread.start()


###############################################
class EmulatorMonitor:
    def monitor_emulator(self, emulator):
        emu_return = emulator.poll()
        while emu_return is None:
            time.sleep(2)
            emu_return = emulator.poll()

        print('Emulator closed with code: ' + str(emu_return))

###############################################
class ControllerServer(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def write_response(self, resp_code, resp_data):
        self.send_response(resp_code)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(resp_data)

    def do_GET(self):

        while INTERNAL_STATE.running and not INTERNAL_STATE.take_action:
            pass

        if not INTERNAL_STATE.running:
            print('Sending SHUTDOWN response')
            self.write_response(500, "SHUTDOWN")

        #### determine manual override
        #manual_override = REAL_CONTROLLER.manual_override()

        #if not manual_override:
        #    output = INTERNAL_STATE.action
        #    cprint("AI: " + str(output), 'green')

        #else:
        #    joystick = REAL_CONTROLLER.read()
        #    joystick[1] *= -1 # flip y (this is in the config when it runs normally)

        #    ### calibration
        #    output = [
        #        int(joystick[0] * 80),
        #        int(joystick[1] * 80),
        #        int(round(joystick[2])),
        #        int(round(joystick[3])),
        #        int(round(joystick[4])),
        #    ]
        #    cprint("Manual: " + str(output), 'yellow')

        ### respond with controller output
        self.write_response(200, INTERNAL_STATE.action)

        INTERNAL_STATE.take_action = False
        return

###############################################
