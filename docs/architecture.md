
## Architecture

### `Mupen64PlusEnv`:

The core `Mupen64PlusEnv` class has been built to handle many of the details of the wrapping and execution of the Mupen64Plus emulator, as well as the implementation of the gym environment. In fact, it inherits from `gym.Env`. The class is abstract and each game environment inherits from it. The game environment subclass provides the ROM path to the base.

#### Initialization:
* starts the controller server using the port specified in the configuration
* starts the emulator process with the provided ROM path (this also uses values from the config file)
* sets up the observation and action spaces (see the [gym documentation](https://gym.openai.com/docs))
    * the observation space is the screen pixels, by default [640, 480, 3]
    * the default action space is the controller mapping provided by `mupen64plus-input-bot`
        * Joystick X-axis (L/R): value from -80 to 80
        * Joystick Y-axis (U/D): value from -80 to 80
        * A Button: value of 0 or 1
        * B Button: value of 0 or 1
        * RB Button: value of 0 or 1
    * *Note:* certain game environments may choose to override this default action space to provide options more suited for the specific game (details should be noted in the respective game's README)

#### Methods:
* `_step(action)` handles taking the supplied action, passing it to the controller server, and reading the new `observation`, `reward`, and `end_episode` values.

* `_observe()` grabs a screenshot of the emulator window and returns the pixel data as a numpy array.

* `_render()` returns the image or opens a viewer depending on the specified mode. Note that calling `_render()` inside a container currently interferes with the emulator display causing the screen to appear frozen, and should be avoided.

* `_close()` shuts down the environment: stops the emulator, and stops the controller server.

* Abstract methods that each game environment must implement:
    * `_navigate_menu()` moves through the game menu from startup to the beginning of an episode.

    * `_get_reward()` determines the reward for each step.

    * `_evaluate_end_state()` determines whether or not the episode is over.

    * `_reset()` resets the environment to begin a new episode.

### `ControllerHTTPServer`:

When initialized, will start an HTTP Server listening on the specified port. The server will listen for `GET` requests, but will wait to respond until `send_controls()` is called. Each time `send_controls()` is called, it will block and wait for the `GET` request to be processed (up to a configured timeout). In other words, the emulator will end up waiting indefinitely for a controller action, essentially waiting for an agent to `step()`.

### `EmulatorMonitor`:

This class simply polls the emulator process to ensure it is still up and running. If not, it prints the emulator process's exit code. Eventually this will also cause the environment to shutdown since the heart of it just died.

### Game Environments:

Each game environment will be created in an appropriately named subdirectory within the `envs` directory. For example: `[...]/gym_mupen64plus/envs/MarioKart64`. The game's environment class must inherit from the base `Mupen64PlusEnv` class described above. This class should be imported in the top-level `__init__.py` file. Example:
```python
from gym_mupen64plus.envs.MarioKart64.mario_kart_env import MarioKartEnv
```

Each game should also have an `__init__.py` file which registers the game's environment(s) in `gym`. Example:
```python
from gym.envs.registration import register
from gym_mupen64plus.envs.MarioKart64.track_envs import MarioKartLuigiRacewayEnv

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
```
