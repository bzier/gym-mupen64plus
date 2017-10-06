import abc
from gym_mupen64plus.envs.MarioKart64.track_envs import MarioKartLuigiRacewayEnv
from gym import spaces

class MarioKartDiscreteLuigiRacewayEnv(MarioKartLuigiRacewayEnv):

    ACTION_MAP = [
        ("NO_OP",         [  0,   0, 0, 0, 0]),
        ("STRAIGHT",      [  0,   0, 1, 0, 0]),
        ("BRAKE",         [  0,   0, 0, 1, 0]),
        ("BACK_UP",       [  0, -80, 0, 1, 0]),
        ("SOFT_LEFT",     [-20,   0, 1, 0, 0]),
        ("LEFT",          [-40,   0, 1, 0, 0]),
        ("HARD_LEFT",     [-60,   0, 1, 0, 0]),
        ("EXTREME_LEFT",  [-80,   0, 1, 0, 0]),
        ("SOFT_RIGHT",    [ 20,   0, 1, 0, 0]),
        ("RIGHT",         [ 40,   0, 1, 0, 0]),
        ("HARD_RIGHT",    [ 60,   0, 1, 0, 0]),
        ("EXTREME_RIGHT", [ 80,   0, 1, 0, 0]),
    ]

    def __init__(self):
        super(MarioKartDiscreteLuigiRacewayEnv, self).__init__()

        self.action_space = spaces.Discrete(12)

    def _step(self, action):
        print('Step called with: ', action)
        controls = self.ACTION_MAP[action][1]
        print('Using controls: ', controls)

        return super(MarioKartDiscreteLuigiRacewayEnv, self)._step(controls)
