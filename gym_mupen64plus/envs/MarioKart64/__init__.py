from gym.envs.registration import register

from gym_mupen64plus.envs.MarioKart64.mario_kart_env import MarioKartEnv
from gym_mupen64plus.envs.MarioKart64.discrete_envs import MarioKartDiscreteEnv

courses = [
    { 'name' : 'Luigi-Raceway',      'cup': 'Mushroom', 'max_steps': 1250 },
    { 'name' : 'Moo-Moo-Farm',       'cup': 'Mushroom', 'max_steps': 1250 },
    { 'name' : 'Koopa-Troopa-Beach', 'cup': 'Mushroom', 'max_steps': 1250 },
    { 'name' : 'Kalimari-Desert',    'cup': 'Mushroom', 'max_steps': 1250 },
    { 'name' : 'Toads-Turnpike',     'cup': 'Flower',   'max_steps': 1250 },
    { 'name' : 'Frappe-Snowland',    'cup': 'Flower',   'max_steps': 1250 },
    { 'name' : 'Choco-Mountain',     'cup': 'Flower',   'max_steps': 1250 },
    { 'name' : 'Mario-Raceway',      'cup': 'Flower',   'max_steps': 1250 },
    { 'name' : 'Wario-Stadium',      'cup': 'Star',     'max_steps': 1250 },
    { 'name' : 'Sherbet-Land',       'cup': 'Star',     'max_steps': 1250 },
    { 'name' : 'Royal-Raceway',      'cup': 'Star',     'max_steps': 1250 },
    { 'name' : 'Bowsers-Castle',     'cup': 'Star',     'max_steps': 1250 },
    { 'name' : 'DKs-Jungle-Parkway', 'cup': 'Special',  'max_steps': 1250 },
    { 'name' : 'Yoshi-Valley',       'cup': 'Special',  'max_steps': 1250 },
    { 'name' : 'Banshee-Boardwalk',  'cup': 'Special',  'max_steps': 1250 },
    { 'name' : 'Rainbow-Road',       'cup': 'Special',  'max_steps': 1250 },
]

for course in courses:

    # Continuous Action Space:
    register(
        id='Mario-Kart-%s-v0' % course['name'],
        entry_point='gym_mupen64plus.envs.MarioKart64:MarioKartEnv',
        kwargs={'course' : course['name'].replace('-','')},
        nondeterministic=True,
        max_episode_steps=course['max_steps']
    )

    # Discrete Action Space:
    register(
        id='Mario-Kart-Discrete-%s-v0' % course['name'],
        entry_point='gym_mupen64plus.envs.MarioKart64:MarioKartDiscreteEnv',
        kwargs={'course' : course['name'].replace('-','')},
        nondeterministic=True,
        max_episode_steps=course['max_steps']
    )
