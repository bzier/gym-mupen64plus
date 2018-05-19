# MarioKart64 Environment

This page describes the Super Smash Bros environment(s).

## Configuration

A configuration file ([`smash_config.yml`](smash_config.yml)) has been provided for this game. Currently the only configuration setting is `ROM_PATH`. This setting must specify the full path to the Super Smash Bros ROM on your system.

## Implementation Details

### `SmashEnv`:

#### Methods:

* Implementation of base abstract methods:
    * `_navigate_menu()` moves through the game menu from startup to the beginning of a match.

    * `_get_reward()` determines the reward for each step.
        * There are rewards for dealing damages and getting kills, and costs if you take damage or die.
        * There is a reward for taunting.
        * There is a penalty for going too long without giving or taking damage, or taunting.


    * `_evaluate_end_state()` Always returns false for now.

    * `_reset()` resets to begin a new match. Mostly unimplemented for now.

### Action Space:

For the definitions of possible discrete actions, see `discrete_envs.py`
