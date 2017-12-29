import abc
from gym_mupen64plus.envs.MarioKart64.track_envs import MarioKartLuigiRacewayEnv
from gym import spaces

class DiscreteActions:
    # TODO: make this a dictionary so we can reference by index or string label
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

    @staticmethod
    def get_action_space():
        return spaces.Discrete(len(DiscreteActions.ACTION_MAP))

    @staticmethod
    def get_controls_from_action(action):
        return DiscreteActions.ACTION_MAP[action][1]


class MarioKartDiscreteLuigiRacewayEnv(MarioKartLuigiRacewayEnv):

    ENABLE_CHECKPOINTS = True

    def __init__(self):
        super(MarioKartDiscreteLuigiRacewayEnv, self).__init__()

        # This needs to happen after the parent class init to effectively override the action space
        self.action_space = DiscreteActions.get_action_space()

    def _step(self, action):
        # Interpret the action choice and get the actual controller state for this step
        controls = DiscreteActions.get_controls_from_action(action)

        return super(MarioKartDiscreteLuigiRacewayEnv, self)._step(controls)
