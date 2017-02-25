import logging
from gym.envs.registration import register

logger = logging.getLogger(__name__)


##### MUSHROOM CUP ####
register(
    id='Mario-Kart-Luigi-Raceway-v0',
    entry_point='gym_mupen64plus.envs.MarioKart64:MarioKartLuigiRacewayEnv',
    tags={
        'mupen': True,
        'cup': 'Mushroom',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Moo-Moo-Farm-v0',
    entry_point='gym_mupen64plus.envs.MarioKart64:MarioKartMooMooFarmEnv',
    tags={
        'mupen': True,
        'cup': 'Mushroom',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Koopa-Troopa-Beach-v0',
    entry_point='gym_mupen64plus.envs.MarioKart64:MarioKartKoopaTroopaBeachEnv',
    tags={
        'mupen': True,
        'cup': 'Mushroom',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Kalimari-Desert-v0',
    entry_point='gym_mupen64plus.envs.MarioKart64:MarioKartKalimariDesertEnv',
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
    entry_point='gym_mupen64plus.envs.MarioKart64:MarioKartToadsTurnpikeEnv',
    tags={
        'mupen': True,
        'cup': 'Flower',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Frappe-Snowland-v0',
    entry_point='gym_mupen64plus.envs.MarioKart64:MarioKartFrappeSnowlandEnv',
    tags={
        'mupen': True,
        'cup': 'Flower',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Choco-Mountain-v0',
    entry_point='gym_mupen64plus.envs.MarioKart64:MarioKartChocoMountainEnv',
    tags={
        'mupen': True,
        'cup': 'Flower',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Mario-Raceway-v0',
    entry_point='gym_mupen64plus.envs.MarioKart64:MarioKartMarioRacewayEnv',
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
    entry_point='gym_mupen64plus.envs.MarioKart64:MarioKartWarioStadiumEnv',
    tags={
        'mupen': True,
        'cup': 'Star',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Sherbet-Land-v0',
    entry_point='gym_mupen64plus.envs.MarioKart64:MarioKartSherbetLandEnv',
    tags={
        'mupen': True,
        'cup': 'Star',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Royal-Raceway-v0',
    entry_point='gym_mupen64plus.envs.MarioKart64:MarioKartRoyalRacewayEnv',
    tags={
        'mupen': True,
        'cup': 'Star',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Bowsers-Castle-v0',
    entry_point='gym_mupen64plus.envs.MarioKart64:MarioKartBowsersCastleEnv',
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
    entry_point='gym_mupen64plus.envs.MarioKart64:MarioKartDKsJungleParkwayEnv',
    tags={
        'mupen': True,
        'cup': 'Special',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Yoshi-Valley-v0',
    entry_point='gym_mupen64plus.envs.MarioKart64:MarioKartYoshiValleyEnv',
    tags={
        'mupen': True,
        'cup': 'Special',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-BansheeBoardwalk-v0',
    entry_point='gym_mupen64plus.envs.MarioKart64:MarioKartBansheeBoardwalkEnv',
    tags={
        'mupen': True,
        'cup': 'Special',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)

register(
    id='Mario-Kart-Rainbow-Road-v0',
    entry_point='gym_mupen64plus.envs.MarioKart64:MarioKartRainbowRoadEnv',
    tags={
        'mupen': True,
        'cup': 'Special',
        'wrapper_config.TimeLimit.max_episode_steps': 100000,
    },
    nondeterministic=True,
)
