from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

import abc
import array
import inspect
import os
import signal
import subprocess
import threading
import time
import pygame
from termcolor import cprint
import yaml

import gym
from gym import error, spaces, utils
from gym.utils import seeding

import numpy as np

import wx
wx.App()

config = yaml.safe_load(open(os.path.join(os.path.dirname(inspect.stack()[0][1]), "config.yml")))



###############################################
class InternalState:
    def __init__(self):
        self.running = False
        self.take_action = False
        self.action = [0, 0, 0, 0, 0]
        self.end_episode_confidence = 0
        self.is_end_episode = False
        self.numpy_array = None
        self.pixel_array = array.array('B', [0] * (config['SCR_W'] * config['SCR_H'] * config['SCR_D']))


###############################################
class ImageHelper:

    BLACK_PIXEL = (0, 0, 0)
    
    def GetPixelColor(self, image_array, x, y):
        base_pixel = (x + (y * config['SCR_W'])) * 3
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
        x_axis = self.joystick.get_axis(0)
        y_axis = self.joystick.get_axis(1)
        a_button = self.joystick.get_button(0)
        b_button = self.joystick.get_button(2) # b=1, x=2
        rb_button = self.joystick.get_button(5)
        return [x_axis, y_axis, a_button, b_button, rb_button]

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
class Mupen64PlusEnv(gym.Env):
    __metaclass__ = abc.ABCMeta
    metadata = {'render.modes': ['human']}

    def __init__(self, rom_path):
        INTERNAL_STATE.running = True
        self.controller_server = None
        self.controller_server_thread = None
        self._start_controller_server()
        self.emulator_process = None
        self._configure_environment(rom_path)
        self.observation_space = spaces.Box(low=0, high=255,
                                            shape=(config['SCR_H'], config['SCR_W'], config['SCR_D']))

        self.action_space = spaces.Tuple((spaces.Box(low=-80, high=80, shape=1), # Joystick X-axis
                                          spaces.Box(low=-80, high=80, shape=1), # Joystick Y-axis
                                          spaces.Discrete(2), # A Button
                                          spaces.Discrete(2), # B Button
                                          spaces.Discrete(2))) # RB Button

    def _step(self, action):
        #cprint('Step called!', 'red')
        self._take_action(action)
        obs = self._observe()
        episode_over = self._evaluate_end_state()
        reward = self._get_reward(episode_over)

        return obs, reward, episode_over, {}

    def _take_action(self, action):
        #cprint('Take Action called!', 'red')
        INTERNAL_STATE.action = action
        INTERNAL_STATE.take_action = True

        # Wait for action to be taken:
        start = time.time()
        while INTERNAL_STATE.take_action and time.time() < start + config['ACTION_TIMEOUT']:
            pass

    def _observe(self):
        #cprint('Observe called!', 'red')
        self._update_pixels()

        return INTERNAL_STATE.numpy_array

    @abc.abstractmethod
    def _get_reward(self, episode_over):
        #cprint('Get Reward called!', 'red')
        return 0

    def _update_pixels(self):
        #cprint('Update Pixels called!', 'red')
        screen = wx.ScreenDC()
        bmp = wx.Bitmap(config['SCR_W'], config['SCR_H'])
        mem = wx.MemoryDC(bmp)
        mem.Blit(0, 0, config['SCR_W'], config['SCR_H'], screen, config['OFFSET_X'], config['OFFSET_Y'])
        bmp.CopyToBuffer(INTERNAL_STATE.pixel_array)

        INTERNAL_STATE.numpy_array = np.frombuffer(INTERNAL_STATE.pixel_array, dtype=np.uint8)
        INTERNAL_STATE.numpy_array = INTERNAL_STATE.numpy_array.reshape(config['SCR_H'], config['SCR_W'], config['SCR_D'])

    @abc.abstractmethod
    def _evaluate_end_state(self):
        #cprint('Evaluate End State called!', 'red')
        return False

    def _kill_emulator(self):
        #cprint('Kill Emulator called!', 'red')
        self._take_action(ControllerServer.NOOP)
        if self.emulator_process is not None:
            self.emulator_process.kill()
        #self._take_action(ControllerServer.NOOP)

    def _close(self):
        cprint('Close called!', 'red')
        INTERNAL_STATE.running = False
        self._kill_emulator()
        self._stop_controller_server()

    def _reset(self):
        cprint('Reset called!', 'red')
        #self._kill_emulator()
        #self._configure_environment()

        return self._observe()

    def _render(self, mode='human', close=False):
        pass

    def _stop_controller_server(self):
        #cprint('Stop Controller Server called!', 'red')
        if self.controller_server is not None:
            self.controller_server.shutdown()

    def _start_controller_server(self):
        server = HTTPServer(('', config['PORT_NUMBER']), ControllerServer)
        self.controller_server_thread = threading.Thread(target=server.serve_forever, args=())
        self.controller_server_thread.daemon = True
        self.controller_server_thread.start()
        self.controller_server = server
        print('ControllerServer started on port ', config['PORT_NUMBER'])

    def _configure_environment(self, rom_path):
        cprint('configure Env called!', 'red')
        self._start_emulator(rom_path=rom_path)
        self._navigate_menu()

    def _start_emulator(self,
                        rom_path,
                        res_w=config['SCR_W'],
                        res_h=config['SCR_H'],
                        input_driver_path=config['INPUT_DRIVER_PATH']):

        cmd = config['MUPEN_CMD'] + \
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

    @abc.abstractmethod
    def _navigate_menu(self):
        return

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

    # Buttons
    NOOP = [0, 0, 0, 0, 0]
    A_BUTTON = [0, 0, 1, 0, 0]
    B_BUTTON = [0, 0, 0, 1, 0]
    RB_BUTTON = [0, 0, 0, 0, 1]
    JOYSTICK_UP = [0, 80, 0, 0, 0]
    JOYSTICK_DOWN = [0, -80, 0, 0, 0]
    JOYSTICK_LEFT = [-80, 0, 0, 0, 0]
    JOYSTICK_RIGHT = [80, 0, 0, 0, 0]

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
