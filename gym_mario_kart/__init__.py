import logging
from gym.envs.registration import register

logger = logging.getLogger(__name__)

register(
    id='Mario-Kart-v0',
    entry_point='gym_mario_kart.envs:MarioKartEnv',
#    max_episode_steps=100000,
    timestep_limit=100000,
    tags={
        'mupen': True,
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic = True,
)