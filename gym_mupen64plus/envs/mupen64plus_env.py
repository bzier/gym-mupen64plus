import sys

PY3_OR_LATER = sys.version_info[0] >= 3

if PY3_OR_LATER:
    # Python 3 specific definitions
    from http.server import BaseHTTPRequestHandler, HTTPServer
else:
    # Python 2 specific definitions
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

import abc
import array
from contextlib import contextmanager
import inspect
import itertools
import json
import os
import subprocess
import threading
import time
from termcolor import cprint
import yaml

import gym
from gym import error, spaces, utils
from gym.utils import seeding

import numpy as np

import mss

###############################################
class ImageHelper:

    def GetPixelColor(self, image_array, x, y):
        base_pixel = image_array[y][x]
        red = base_pixel[0]
        green = base_pixel[1]
        blue = base_pixel[2]
        return (red, green, blue)


###############################################
### Variables & Constants                   ###
###############################################

# The width, height, and depth of the emulator window:
SCR_W = 640
SCR_H = 480
SCR_D = 3

MILLISECOND = 1.0 / 1000.0

IMAGE_HELPER = ImageHelper()


###############################################
class Mupen64PlusEnv(gym.Env):
    __metaclass__ = abc.ABCMeta
    metadata = {'render.modes': ['human']}

    def __init__(self):
        self.viewer = None
        self.reset_count = 0
        self.step_count = 0
        self.running = True
        self.mss_grabber = None
        self.episode_over = False
        self.pixel_array = None
        self._base_load_config()
        self._base_validate_config()
        self.frame_skip = self.config['FRAME_SKIP']
        self.controller_server, self.controller_server_thread = self._start_controller_server()
        self.xvfb_process, self.emulator_process = \
            self._start_emulator(rom_name=self.config['ROM_NAME'],
                                 gfx_plugin=self.config['GFX_PLUGIN'],
                                 input_driver_path=self.config['INPUT_DRIVER_PATH'])
        with self.controller_server.frame_skip_disabled():
            self._navigate_menu()

        self.observation_space = \
            spaces.Box(low=0, high=255, shape=(SCR_H, SCR_W, SCR_D))

        self.action_space = spaces.MultiDiscrete([[-80, 80], # Joystick X-axis
                                                  [-80, 80], # Joystick Y-axis
                                                  [  0,  1], # A Button
                                                  [  0,  1], # B Button
                                                  [  0,  1], # RB Button
                                                  [  0,  1], # LB Button
                                                  [  0,  1], # Z Button
                                                  [  0,  1], # C Right Button
                                                  [  0,  1], # C Left Button
                                                  [  0,  1], # C Down Button
                                                  [  0,  1], # C Up Button
                                                  [  0,  1], # D-Pad Right Button
                                                  [  0,  1], # D-Pad Left Button
                                                  [  0,  1], # D-Pad Down Button
                                                  [  0,  1], # D-Pad Up Button
                                                  [  0,  1], # Start Button
                                                 ])

    def _base_load_config(self):
        self.config = yaml.safe_load(open(os.path.join(os.path.dirname(inspect.stack()[0][1]), "config.yml")))
        self._load_config()

    @abc.abstractmethod
    def _load_config(self):
        return

    def _base_validate_config(self):
        if 'ROM_NAME' not in self.config:
            raise AssertionError('ROM_NAME configuration is required')
        if 'GFX_PLUGIN' not in self.config:
            raise AssertionError('GFX_PLUGIN configuration is required')
        self._validate_config()

    @abc.abstractmethod
    def _validate_config(self):
        return

    def _step(self, action):
        #cprint('Step %i: %s' % (self.step_count, action), 'green')
        self._act(action)
        obs = self._observe()
        self.episode_over = self._evaluate_end_state()
        reward = self._get_reward()

        self.step_count += 1
        return obs, reward, self.episode_over, {}

    def _act(self, action, count=1):
        for _ in itertools.repeat(None, count):
            self.controller_server.send_controls(ControllerState(action))

    def _wait(self, count=1, wait_for='Unknown'):
        self._act(ControllerState.NO_OP, count=count)

    def _press_button(self, button, times=1):
        for _ in itertools.repeat(None, times):
            self._act(button) # Press
            self._act(ControllerState.NO_OP) # and release

    def _observe(self):
        #cprint('Observe called!', 'yellow')

        if self.config['USE_XVFB']:
            offset_x = 0
            offset_y = 0
        else:
            offset_x = self.config['OFFSET_X']
            offset_y = self.config['OFFSET_Y']

        image_array = \
            np.array(self.mss_grabber.grab({"top": offset_y,
                                            "left": offset_x,
                                            "width": SCR_W,
                                            "height": SCR_H}),
                     dtype=np.uint8)

        # drop the alpha channel and flip red and blue channels (BGRA -> RGB)
        self.pixel_array = np.flip(image_array[:, :, :3], 2)

        return self.pixel_array

    @abc.abstractmethod
    def _navigate_menu(self):
        return

    @abc.abstractmethod
    def _get_reward(self):
        #cprint('Get Reward called!', 'yellow')
        return 0

    @abc.abstractmethod
    def _evaluate_end_state(self):
        #cprint('Evaluate End State called!', 'yellow')
        return False

    @abc.abstractmethod
    def _reset(self):
        cprint('Reset called!', 'yellow')
        self.reset_count += 1

        self.step_count = 0
        return self._observe()

    def _render(self, mode='human', close=False):
        if close:
            if hasattr(self, 'viewer') and self.viewer is not None:
                self.viewer.close()
                self.viewer = None
            return
        img = self.pixel_array
        if mode == 'rgb_array':
            return img
        elif mode == 'human':
            if not hasattr(self, 'viewer') or self.viewer is None:
                from gym.envs.classic_control import rendering
                self.viewer = rendering.SimpleImageViewer()
            self.viewer.imshow(img)

    def _close(self):
        cprint('Close called!', 'yellow')
        self.running = False
        self._kill_emulator()
        self._stop_controller_server()

    def _start_controller_server(self):
        server = ControllerHTTPServer(server_address  = ('', self.config['PORT_NUMBER']),
                                      control_timeout = self.config['ACTION_TIMEOUT'],
                                      frame_skip      = self.frame_skip) # TODO: Environment argument (with issue #26)
        server_thread = threading.Thread(target=server.serve_forever, args=())
        server_thread.daemon = True
        server_thread.start()
        print('ControllerHTTPServer started on port ', self.config['PORT_NUMBER'])
        return server, server_thread

    def _stop_controller_server(self):
        #cprint('Stop Controller Server called!', 'yellow')
        if hasattr(self, 'controller_server'):
            self.controller_server.shutdown()

    def _start_emulator(self,
                        rom_name,
                        gfx_plugin,
                        input_driver_path,
                        res_w=SCR_W,
                        res_h=SCR_H,
                        res_d=SCR_D):

        rom_path = os.path.abspath(
            os.path.join(os.path.dirname(inspect.stack()[0][1]),
                         '../ROMs',
                         rom_name))

        if not os.path.isfile(rom_path):
            msg = "ROM not found: " + rom_path
            cprint(msg, 'red')
            raise Exception(msg)

        input_driver_path = os.path.abspath(os.path.expanduser(input_driver_path))
        if not os.path.isfile(input_driver_path):
            msg = "Input driver not found: " + input_driver_path
            cprint(msg, 'red')
            raise Exception(msg)

        cmd = [self.config['MUPEN_CMD'],
               "--nospeedlimit",
               "--nosaveoptions",
               "--resolution",
               "%ix%i" % (res_w, res_h),
               "--gfx", gfx_plugin,
               "--audio", "dummy",
               "--input", input_driver_path,
               rom_path]

        initial_disp = os.environ["DISPLAY"]
        cprint('Initially on DISPLAY %s' % initial_disp, 'red')

        xvfb_proc = None
        if self.config['USE_XVFB']:
            display_num = -1
            success = False
            # If we couldn't find an open display number after 15 attempts, give up
            while not success and display_num <= 15:
                display_num += 1
                xvfb_cmd = [self.config['XVFB_CMD'],
                            ":" + str(display_num),
                            "-screen",
                            "0",
                            "%ix%ix%i" % (res_w, res_h, res_d * 8),
                            "-fbdir",
                            self.config['TMP_DIR']]

                cprint('Starting xvfb with command: %s' % xvfb_cmd, 'yellow')

                xvfb_proc = subprocess.Popen(xvfb_cmd, shell=False, stderr=subprocess.STDOUT)

                time.sleep(2) # Give xvfb a couple seconds to start up

                # Poll the process to see if it exited early
                # (most likely due to a server already active on the display_num)
                if xvfb_proc.poll() is None:
                    success = True

                print('')

            if not success:
                msg = "Failed to initialize Xvfb!"
                cprint(msg, 'red')
                raise Exception(msg)

            os.environ["DISPLAY"] = ":" + str(display_num)
            cprint('Using DISPLAY %s' % os.environ["DISPLAY"], 'blue')
            cprint('Changed to DISPLAY %s' % os.environ["DISPLAY"], 'red')

            cmd = [self.config['VGLRUN_CMD'], "-d", ":" + str(display_num)] + cmd

        cprint('Starting emulator with comand: %s' % cmd, 'yellow')

        emulator_process = subprocess.Popen(cmd,
                                            env=os.environ.copy(),
                                            shell=False,
                                            stderr=subprocess.STDOUT)

        # TODO: Test and cleanup:
        # May need to initialize this after the DISPLAY env var has been set
        # so it attaches to the correct X display; otherwise screenshots may
        # come from the wrong place. This used to be true when we were using
        # wxPython for screenshots. Untested after switching to mss.
        cprint('Calling mss.mss() with DISPLAY %s' % os.environ["DISPLAY"], 'red')
        self.mss_grabber = mss.mss()
        time.sleep(2) # Give mss a couple seconds to initialize; also may not be necessary

        # Restore the DISPLAY env var
        os.environ["DISPLAY"] = initial_disp
        cprint('Changed back to DISPLAY %s' % os.environ["DISPLAY"], 'red')

        emu_mon = EmulatorMonitor()
        monitor_thread = threading.Thread(target=emu_mon.monitor_emulator,
                                          args=[emulator_process])
        monitor_thread.daemon = True
        monitor_thread.start()

        return xvfb_proc, emulator_process

    def _kill_emulator(self):
        #cprint('Kill Emulator called!', 'yellow')
        try:
            self._act(ControllerState.NO_OP)
            if self.emulator_process is not None:
                self.emulator_process.kill()
            if self.xvfb_process is not None:
                self.xvfb_process.terminate()
        except AttributeError:
            pass # We may be shut down during intialization before these attributes have been set


###############################################
class EmulatorMonitor:
    def monitor_emulator(self, emulator):
        emu_return = emulator.poll()
        while emu_return is None:
            time.sleep(2)
            if emulator is not None:
                emu_return = emulator.poll()
            else:
                print('Emulator reference is no longer valid. Shutting down?')
                return

        # TODO: this means our environment died... need to die too
        print('Emulator closed with code: ' + str(emu_return))


###############################################
class ControllerState(object):

    # Controls           [ JX,  JY,  A,  B, RB, LB,  Z, CR, CL, CD, CU, DR, DL, DD, DU,  S]
    NO_OP              = [  0,   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0]
    START_BUTTON       = [  0,   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1]
    A_BUTTON           = [  0,   0,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0]
    B_BUTTON           = [  0,   0,  0,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0]
    RB_BUTTON          = [  0,   0,  0,  0,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0]
    CR_BUTTON          = [  0,   0,  0,  0,  0,  0,  0,  1,  0,  0,  0,  0,  0,  0,  0,  0]
    CL_BUTTON          = [  0,   0,  0,  0,  0,  0,  0,  0,  1,  0,  0,  0,  0,  0,  0,  0]
    CD_BUTTON          = [  0,   0,  0,  0,  0,  0,  0,  0,  0,  1,  0,  0,  0,  0,  0,  0]
    CU_BUTTON          = [  0,   0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  0,  0,  0,  0,  0]
    JOYSTICK_UP        = [  0,  127, 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0]
    JOYSTICK_DOWN      = [  0, -128, 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0]
    JOYSTICK_LEFT      = [-128,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0]
    JOYSTICK_RIGHT     = [ 127,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0]

    def __init__(self, controls=NO_OP):
        self.X_AXIS = controls[0]
        self.Y_AXIS = controls[1]
        self.A_BUTTON = controls[2]
        self.B_BUTTON = controls[3]
        self.R_TRIG = controls[4]
        self.L_TRIG = controls[5]
        self.Z_TRIG = controls[6]
        self.R_CBUTTON = controls[7]
        self.L_CBUTTON = controls[8]
        self.D_CBUTTON = controls[9]
        self.U_CBUTTON = controls[10]
        self.R_DPAD = controls[11]
        self.L_DPAD = controls[12]
        self.D_DPAD = controls[13]
        self.U_DPAD = controls[14]
        self.START_BUTTON = controls[15]

    def to_json(self):
        return json.dumps(self.__dict__)

###############################################
class ControllerHTTPServer(HTTPServer, object):

    def __init__(self, server_address, control_timeout, frame_skip):
        self.control_timeout = control_timeout
        self.controls = ControllerState()
        self.hold_response = True
        self.running = True
        self.send_count = 0
        self.frame_skip = frame_skip
        self.frame_skip_enabled = True
        self.TEXT_PLAIN_CONTENT_TYPE = "text/plain".encode()
        super(ControllerHTTPServer, self).__init__(server_address, self.ControllerRequestHandler)

    def send_controls(self, controls):
        #print('Send controls called')
        self.send_count = 0
        self.controls = controls
        self.hold_response = False

        # Wait for controls to be sent:
        #start = time.time()
        while not self.hold_response: # and time.time() < start + self.control_timeout:
            time.sleep(MILLISECOND)

    def shutdown(self):
        self.running = False
        super(ControllerHTTPServer, self).shutdown()
        super(ControllerHTTPServer, self).server_close()

    # http://preshing.com/20110920/the-python-with-statement-by-example/#implementing-the-context-manager-as-a-generator
    @contextmanager
    def frame_skip_disabled(self):
        self.frame_skip_enabled = False
        yield True
        self.frame_skip_enabled = True

    class ControllerRequestHandler(BaseHTTPRequestHandler, object):

        def log_message(self, fmt, *args):
            pass

        def write_response(self, resp_code, resp_data):
            self.send_response(resp_code)
            self.send_header("Content-type", self.server.TEXT_PLAIN_CONTENT_TYPE)
            self.end_headers()
            self.wfile.write(resp_data.encode())

        def do_GET(self):

            while self.server.running and self.server.hold_response:
                time.sleep(MILLISECOND)

            if not self.server.running:
                print('Sending SHUTDOWN response')
                # TODO: This sometimes fails with a broken pipe because
                # the emulator has already stopped. Should handle gracefully (Issue #4)
                self.write_response(500, "SHUTDOWN")

            ### respond with controller output
            self.write_response(200, self.server.controls.to_json())
            self.server.send_count += 1

            # If we have sent the controls 'n' times, now we block until the next action is sent
            if self.server.send_count >= self.server.frame_skip or not self.server.frame_skip_enabled:
                self.server.hold_response = True
            return

###############################################
