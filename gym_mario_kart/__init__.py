import logging
from gym.envs.registration import register

logger = logging.getLogger(__name__)


##### MUSHROOM CUP ####
register(
    id='Mario-Kart-Luigi-Raceway-v0',
    entry_point='gym_mario_kart.envs:MarioKartLuigiRacewayEnv',
    tags={
        'mupen': True,
        'cup': 'Mushroom',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Moo-Moo-Farm-v0',
    entry_point='gym_mario_kart.envs:MarioKartMooMooFarmEnv',
    tags={
        'mupen': True,
        'cup': 'Mushroom',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Koopa-Troopa-Beach-v0',
    entry_point='gym_mario_kart.envs:MarioKartKoopaTroopaBeachEnv',
    tags={
        'mupen': True,
        'cup': 'Mushroom',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Kalimari-Desert-v0',
    entry_point='gym_mario_kart.envs:MarioKartKalimariDesertEnv',
    tags={
        'mupen': True,
        'cup': 'Mushroom',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

##### FLOWER CUP ####
register(
    id='Mario-Kart-Toads-Turnpike-v0',
    entry_point='gym_mario_kart.envs:MarioKartToadsTurnpikeEnv',
    tags={
        'mupen': True,
        'cup': 'Flower',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Frappe-Snowland-v0',
    entry_point='gym_mario_kart.envs:MarioKartFrappeSnowlandEnv',
    tags={
        'mupen': True,
        'cup': 'Flower',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Choco-Mountain-v0',
    entry_point='gym_mario_kart.envs:MarioKartChocoMountainEnv',
    tags={
        'mupen': True,
        'cup': 'Flower',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Mario-Raceway-v0',
    entry_point='gym_mario_kart.envs:MarioKartMarioRacewayEnv',
    tags={
        'mupen': True,
        'cup': 'Flower',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

##### STAR CUP ####
register(
    id='Mario-Kart-Wario-Stadium-v0',
    entry_point='gym_mario_kart.envs:MarioKartWarioStadiumEnv',
    tags={
        'mupen': True,
        'cup': 'Star',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Sherbet-Land-v0',
    entry_point='gym_mario_kart.envs:MarioKartSherbetLandEnv',
    tags={
        'mupen': True,
        'cup': 'Star',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Royal-Raceway-v0',
    entry_point='gym_mario_kart.envs:MarioKartRoyalRacewayEnv',
    tags={
        'mupen': True,
        'cup': 'Star',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Bowsers-Castle-v0',
    entry_point='gym_mario_kart.envs:MarioKartBowsersCastleEnv',
    tags={
        'mupen': True,
        'cup': 'Star',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

##### SPECIAL CUP ####
register(
    id='Mario-Kart-DKs-Jungle-Parkway-v0',
    entry_point='gym_mario_kart.envs:MarioKartDKsJungleParkwayEnv',
    tags={
        'mupen': True,
        'cup': 'Special',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Yoshi-Valley-v0',
    entry_point='gym_mario_kart.envs:MarioKartYoshiValleyEnv',
    tags={
        'mupen': True,
        'cup': 'Special',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-BansheeBoardwalk-v0',
    entry_point='gym_mario_kart.envs:MarioKartBansheeBoardwalkEnv',
    tags={
        'mupen': True,
        'cup': 'Special',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Rainbow-Road-v0',
    entry_point='gym_mario_kart.envs:MarioKartRainbowRoadEnv',
    tags={
        'mupen': True,
        'cup': 'Special',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)
