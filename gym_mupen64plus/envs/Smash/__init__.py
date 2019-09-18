from gym.envs.registration import register

from gym_mupen64plus.envs.Smash.smash_env import SmashEnv
from gym_mupen64plus.envs.Smash.discrete_envs import SmashDiscreteEnv

# TODO: Add support for other oppenents, colors, maps.
characters = ['luigi', 'mario', 'dk', 'link', 'samus', 'falcon', 'ness',
              'yoshi', 'kirby', 'fox', 'pikachu', 'jigglypuff']

for character in characters:
    # Continuous Action Space:
    register(
        id='Smash-%s-v0' % character,
        entry_point='gym_mupen64plus.envs.Smash:SmashEnv',
        kwargs={'my_character' : character},
        nondeterministic=True,
        max_episode_steps=2147483647
    )

    # Discrete Action Space:
    register(
        id='Smash-Discrete-%s-v0' % character,
        entry_point='gym_mupen64plus.envs.Smash:SmashDiscreteEnv',
        kwargs={'my_character' : character},
        nondeterministic=True,
        max_episode_steps=2147483647
    )
