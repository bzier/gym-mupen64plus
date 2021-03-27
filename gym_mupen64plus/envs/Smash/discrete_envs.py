import abc
from gym_mupen64plus.envs.Smash.smash_env import SmashEnv
from gym import spaces

def _create_action_map():
    joystick_magnitudes = [
        ("HARDNEG", [-120]),
        ("MIDNEG",  [-60]),
        ("NEUTRAL", [0]),
        ("MIDPOS",  [60]),
        ("HARDPOS", [120]),
    ]
    # Button orders are A, B, RB, LB, Z, CR
    allowed_buttons = [
        ("NOBUTTONS", [0, 0, 0, 0, 0, 0]),
        ("ABUTTON",   [1, 0, 0, 0, 0, 0]),
        ("BBUTTON",   [0, 1, 0, 0, 0, 0]),
        ("ZBUTTON",   [0, 0, 0, 0, 1, 0]),
        ("CBUTTON",   [0, 0, 0, 0, 0, 1]),
    ]
    actions = []
    for xmag in joystick_magnitudes:
        for ymag in joystick_magnitudes:
            for button in allowed_buttons:
                name = xmag[0] + "X_" + ymag[0] + "Y_" + button[0]
                # Joystick X and Y preceed the buttons above.
                state = xmag[1] + ymag[1] + button[1]
                actions.append((name, state))
    # These actions shouldn't be combined with joystick directions.
    actions.append(("GRAB",  [0, 0, 1, 0, 0, 0, 1, 0]))
    actions.append(("TAUNT", [0, 0, 0, 0, 0, 1, 0, 0]))
    return actions

class DiscreteActions:
    ACTION_MAP = _create_action_map()

    @staticmethod
    def get_action_space():
        return spaces.Discrete(len(DiscreteActions.ACTION_MAP))

    @staticmethod
    def get_controls_from_action(action):
        return DiscreteActions.ACTION_MAP[action][1]


class SmashDiscreteEnv(SmashEnv):

    ENABLE_CHECKPOINTS = True

    def __init__(self, my_character='pikachu', their_character='dk',
                 my_character_color='CUP', their_character_color='CLEFT',
                 opponent_bot_level=10, map='DreamLand'):
        super(SmashDiscreteEnv, self).__init__(
            my_character=my_character, their_character=their_character,
            my_character_color=my_character_color,
            their_character_color=their_character_color,
            opponent_bot_level=opponent_bot_level, map=map)

        # This needs to happen after the parent class init to effectively override the action space
        self.action_space = DiscreteActions.get_action_space()

    def step(self, action):
        # Interpret the action choice and get the actual controller state for this step
        controls = DiscreteActions.get_controls_from_action(action)

        return super(SmashDiscreteEnv, self).step(controls)
