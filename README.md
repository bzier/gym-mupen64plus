# gym-mupen64plus

This project is an [OpenAI Gym](https://github.com/openai/gym/) environment wrapper for the [Mupen64Plus](http://www.mupen64plus.org/) N64 emulator. The goal of this project is to provide a platform for reinforcement learning agents to be able to easily interface with N64 games using the OpenAI gym library. This should allow for easier adaptation of existing agents that have been built using the gym library to play Atari games, for example.

Currently, only MarioKart64 and SuperSmashBros have been wrapped, but the core environment has been built to support any game. This top-level README will be used to describe the basic setup instructions, architecture of the environment, etc. Each game that gets wrapped will have its own README file within its respective subdirectory. This top-level README will link to each of the games' README file as well.

#### Thanks:
Many of the core concepts for this wrapper were borrowed/adapted directly from [@kevinhughes27](https://github.com/kevinhughes27)'s fantastic [TensorKart](https://github.com/kevinhughes27/TensorKart) project (self-driving MarioKart with TensorFlow). A huge thanks goes out to him for inspiring the foundation of this project.


## Contributing

Please create issues as you encounter them. Future work and ideas will be captured as issues as well, so if you have any ideas of things you'd like to see, please add them. Also, feel free to fork this repository and improve upon it. If you come up with something you'd like to see incorporated, submit a pull request. Adding support for additional games would be a great place to start. If you do decide to implement support for a game, please create an issue mentioning what game you are working on. This will help organize the project and prevent duplicate work.

## Setup

The easiest, cleanest, most consistent way to get up and running with this project is via [`Docker`](https://docs.docker.com/). These instructions will focus on that approach.

### With Docker

1. Run the following command to build the project's docker image

    > You should substitute the placeholders between `< >` with your own values.

    ```sh
    docker build -t <image_name>:<tag> .
    ```
    ```sh
    # Example:
    docker build -t bz/gym-mupen64plus:0.0.5 .
    ```

    ### That's it!

    ...wait... that's it??

    Yup... Ah, the beauty of Docker.

### Without Docker
* :(
  > It is possible to run without Docker, but there isn't a compelling reason to and it just introduces a significant amount of setup work and potential complications.
  >
  > **`Fair warning:`** I likely will ***not*** be testing manual setup or maintaining its documentation going forward so it may become stale over time.
  >
  > However, if you really do want to, here are the [old instructions](docs/manual_setup.md).

## Example Agents

### Simple Test:
A simple example to test if the environment is up-and-running:
```
docker run -it \
  --name test-gym-env \
  -p 5900 \
  --mount source="$(MY_ROM_PATH)",target=/src/gym-mupen64plus/gym_mupen64plus/ROMs,type=bind \
  bz/gym-mupen64plus:0.0.5 \ # This should match the image & tag you used during setup
  python verifyEnv.py
```

```python
#!/bin/python
import gym, gym_mupen64plus

env = gym.make('Mario-Kart-Luigi-Raceway-v0')
env.reset()

for i in range(88):
    (obs, rew, end, info) = env.step([0, 0, 0, 0, 0]) # NOOP until green light

for i in range(100):
    (obs, rew, end, info) = env.step([0, 0, 1, 0, 0]) # Drive straight

raw_input("Press <enter> to exit... ")

env.close()
```

### AI Agent (supervised learning):
The original inspiration for this project has now been updated to take advantage of this gym environment. It is an example of using supervised learning to train an AI Agent that is capable of interacting with the environment (Mario Kart). It utilizes the TensorFlow library for its machine learning. Check out TensorKart [here](https://github.com/kevinhughes27/TensorKart).


### AI Agent (reinforcement learning):
An adaptation of the A3C algorithm has been applied to this environment (Mario Kart) and is capable of training from scratch (zero knowledge) to successfully finish races. Check out that agent [here](https://github.com/bzier/universe-starter-agent/tree/mario-kart-agent).


## Games

*Links to ROM files will not be included here. Use your ninja skills as appropriate.*

ROM files can be placed in `./gym_mupen64plus/ROMs/`.

Here is a list of games that have been wrapped. Each game may support multiple 'modes' with different levels or missions configured. See each of the games' pages for more details.
* [MarioKart64](gym_mupen64plus/envs/MarioKart64/README.md)
* [Super Smash Bros](gym_mupen64plus/envs/Smash/README.md)


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
