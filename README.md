# gym-mupen64plus

This project is an [OpenAI Gym](https://github.com/openai/gym/) environment wrapper for the [Mupen64Plus](http://www.mupen64plus.org/) N64 emulator. The goal of this project is to provide a platform for reinforcement learning agents to be able to easily interface with N64 games using the OpenAI gym library. This should allow for easier adaptation of existing agents that have been built using the gym library to play Atari games, for example.

Currently, only MarioKart64 and SuperSmashBros have been wrapped, but the core environment has been built to support any game. This top-level README will be used to describe the basic setup instructions, architecture of the environment, etc. Each game that gets wrapped will have its own README file within its respective subdirectory. This top-level README will link to each of the games' README file as well.

#### Thanks:
Many of the core concepts for this wrapper were borrowed/adapted directly from [@kevinhughes27](https://github.com/kevinhughes27)'s fantastic [TensorKart](https://github.com/kevinhughes27/TensorKart) project (self-driving MarioKart with TensorFlow). A huge thanks goes out to him for inspiring the foundation of this project.

Another big thanks to everyone who has contributed to the project so far. I appreciate the help, from the small typo/bug fixes to the large implementations.

## Contributing

Please create issues as you encounter them. Future work and ideas will be captured as issues as well, so if you have any ideas of things you'd like to see, please add them. Also, feel free to fork this repository and improve upon it. If you come up with something you'd like to see incorporated, submit a pull request. Adding support for additional games would be a great place to start. If you do decide to implement support for a game, please create an issue mentioning what game you are working on. This will help organize the project and prevent duplicate work.

## Setup

The easiest, cleanest, most consistent way to get up and running with this project is via [`Docker`](https://docs.docker.com/). These instructions will focus on that approach.

### Running with docker-compose

**Pre-requisites:**
- Docker & docker-compose
- Ensure you have a copy of the ROMs you wish to use. See the [Games](#Games) section below for details.

**Steps:**
1. Run the following command to build & run the project via `docker-compose`.

    ```sh
    docker-compose up --build -d
    ```

    This will start the following 4 containers:
    - `xvfbsrv` runs XVFB
    - `vncsrv` runs a VNC server connected to the Xvfb container
    - `agent` runs the example python script
    - `emulator` runs the mupen64plus emulator

2. Then you can use your favorite VNC client (e.g., [VNC Viewer](https://www.realvnc.com/en/connect/download/viewer/)) to connect to `localhost` to watch the XVFB display in real-time. Note that running the VNC server and client can cause some performance overhead.

3. ### That's it!

    ...wait... that's it??

    Yup... Ah, the beauty of Docker.

<br/>
<details>
  <summary><b>Miscelaneous notes (click to expand):</b></summary>

- After connecting with a VNC client, depending how quickly you connected, you should see the environment navigate the menus to select the track/character, then Mario will wait for the green light, drive straight briefly and then start doing doughnuts.

- The script will run for a bit more than 10,000 steps before prompting for input. Without an interactive terminal, if you waited until the end, this will hit an EOF and exit. Mario will appear to have frozen since the XVFB screen is no longer being updated.

- You can view the output from the `example.py` script by tailing the agent container logs. You can see sample output [here](docs/example_script_output.md).
    ```
    docker logs -f gym-mupen64plus_agent_1
    ```
- You can clean up with:
    ```
    docker-compose down
    ```

</details><br/>

### Building the Docker image

If you would like to build the docker image on its own (outside of docker-compose), you can:

1. Run the following command to build the project's docker image

    > You should substitute the placeholders between `< >` with your own values.

    ```sh
    docker build -t <image_name>:<tag> .
    ```
    ```sh
    # Example:
    docker build -t bz/gym-mupen64plus:0.0.5 .
    ```

### Without Docker

<details>
  <summary>:( click to expand :(</summary>
  
  > It is possible to run without Docker, but there isn't a compelling reason to and it just introduces a significant amount of setup work and potential complications.
  >
  > **`Fair warning:`** I likely will ***not*** be testing manual setup or maintaining its documentation going forward so it may become stale over time.
  >
  > However, if you really do want to, here are the [old instructions](docs/manual_setup.md).

</details><br/>

## Example Agents

### Simple Test:

The docker-compose steps above are the easiest approach to get started. However, if you build the image separately and would like to test without using docker-compose, you can.

A simple [example](./example.py) to test if the environment is up-and-running:
```sh
# Note: if you have placed your ROMs in a different location, be sure to update the source path in the command.
docker run -it \
  --name test-gym-env \
  -p 5900 \
  --mount source="$(pwd)/gym_mupen64plus/ROMs",target=/src/gym-mupen64plus/gym_mupen64plus/ROMs,type=bind \
  bz/gym-mupen64plus:0.0.5 \ # This should match the image & tag you used during setup above
  python gym-mupen64plus/example.py
```

The example script will repeat doughnuts for 10,000 steps. You can see sample output [here](docs/example_script_output.md).

**Clean up:**

You can kill the process (and exit the container) by hitting `ctrl`+`c` (probably a few times), and you can remove the container with:
```sh
docker rm test-gym-env
```

### AI Agent (supervised learning):
The original inspiration for this project has now been updated to take advantage of this gym environment. It is an example of using supervised learning to train an AI Agent that is capable of interacting with the environment (Mario Kart). It utilizes the TensorFlow library for its machine learning. Check out TensorKart [here](https://github.com/kevinhughes27/TensorKart).


### AI Agent (reinforcement learning):
An adaptation of the A3C algorithm has been applied to this environment (Mario Kart) and is capable of training from scratch (zero knowledge) to successfully finish races. Check out that agent [here](https://github.com/bzier/universe-starter-agent/tree/mario-kart-agent).


## Games

**ROM files:**

*Links to ROM files will not be included here. Use your ninja skills as appropriate.*

ROM files can be placed in `./gym_mupen64plus/ROMs/`. If you wish to place them elsewhere, update your `.env` file with the path. See the game READMEs below for details about specific games, including specifying the proper ROM file name.

**Game docs:**

Here is a list of games that have been wrapped. Each game may support multiple 'modes' with different levels or missions configured. See each of the games' pages for more details.
* [MarioKart64](gym_mupen64plus/envs/MarioKart64/README.md)
* [Super Smash Bros](gym_mupen64plus/envs/Smash/README.md)

<br/>

# Additional Documentation:

* [Architecture](docs/architecture.md)
* [Thread Synchronization](docs/threadSynchronization.md)
