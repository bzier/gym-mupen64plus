from gym_mupen64plus.envs.MarioKart64.mario_kart_env import MarioKartEnv

class MarioKartLuigiRacewayEnv(MarioKartEnv):
    MAP_SERIES = 0
    MAP_CHOICE = 0

    CHECKPOINTS = [
        #### Straight-away ####
        [(563, 317), (564, 317), (565, 317), (566, 317), (567, 317)],
        #### Around the first bend ####
        [(563, 285), (564, 285), (565, 285), (566, 285), (567, 285)],
        [(540, 259), (540, 260), (540, 261), (540, 262), (540, 263)],
        [(516, 286), (517, 286), (518, 286), (519, 286), (520, 286)],
        ##### The angled sections on etiher side of the tunnel #####
        [(553, 321), (554, 321), (554, 320), (555, 320), (555, 319)],
        [(547, 370), (548, 371), (549, 372), (550, 373)],
        #### They're making another left turn ####
        [(526, 397), (527, 397), (528, 397), (529, 397), (530, 397)],
        [(546, 412), (546, 413), (546, 414), (546, 415), (546, 416)],
        [(562, 398), (563, 398), (564, 398), (565, 398), (566, 398)],
        #### Straight-away to the line ####
        [(563, 380), (564, 380), (565, 380), (566, 380), (567, 380)]
    ]

class MarioKartMooMooFarmEnv(MarioKartEnv):
    MAP_SERIES = 0
    MAP_CHOICE = 1

class MarioKartKoopaTroopaBeachEnv(MarioKartEnv):
    MAP_SERIES = 0
    MAP_CHOICE = 2

class MarioKartKalimariDesertEnv(MarioKartEnv):
    MAP_SERIES = 0
    MAP_CHOICE = 3

class MarioKartToadsTurnpikeEnv(MarioKartEnv):
    MAP_SERIES = 1
    MAP_CHOICE = 0

class MarioKartFrappeSnowlandEnv(MarioKartEnv):
    MAP_SERIES = 1
    MAP_CHOICE = 1

class MarioKartChocoMountainEnv(MarioKartEnv):
    MAP_SERIES = 1
    MAP_CHOICE = 2

class MarioKartMarioRacewayEnv(MarioKartEnv):
    MAP_SERIES = 1
    MAP_CHOICE = 3

class MarioKartWarioStadiumEnv(MarioKartEnv):
    MAP_SERIES = 2
    MAP_CHOICE = 0

class MarioKartSherbetLandEnv(MarioKartEnv):
    MAP_SERIES = 2
    MAP_CHOICE = 1

class MarioKartRoyalRacewayEnv(MarioKartEnv):
    MAP_SERIES = 2
    MAP_CHOICE = 2

class MarioKartBowsersCastleEnv(MarioKartEnv):
    MAP_SERIES = 2
    MAP_CHOICE = 3

class MarioKartDKsJungleParkwayEnv(MarioKartEnv):
    MAP_SERIES = 3
    MAP_CHOICE = 0

class MarioKartYoshiValleyEnv(MarioKartEnv):
    MAP_SERIES = 3
    MAP_CHOICE = 1

class MarioKartBansheeBoardwalkEnv(MarioKartEnv):
    MAP_SERIES = 3
    MAP_CHOICE = 2

class MarioKartRainbowRoadEnv(MarioKartEnv):
    MAP_SERIES = 3
    MAP_CHOICE = 3
