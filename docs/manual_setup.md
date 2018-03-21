## Manual Setup

> **`Fair warning:`** I likely will ***not*** be testing manual setup or maintaining its documentation going forward so it may become stale over time. For the current setup documentation using Docker, go [here](../README.md#with-docker)

### Python Dependencies
*If you follow the installation steps below, these dependencies will be resolved automatically.*
* Python 2.7
* gym
* numpy
* PyYAML
* termcolor
* mss

### Additional Dependencies
*These dependencies must be manually installed following these instructions.*
* Mupen64Plus
    ```bash
    #!/bin/bash
    sudo apt-get install mupen64plus
    ```

* mupen64plus-input-bot
    ```bash
    #!/bin/bash
    mkdir mupen64plus-src && cd "$_"
    git clone https://github.com/mupen64plus/mupen64plus-core
    git clone https://github.com/kevinhughes27/mupen64plus-input-bot
    cd mupen64plus-input-bot
    make all
    sudo make install
    ```

* One or more N64 ROMs (see the [Games](#games) section below)

### Installation

Setting up the dependencies can be accomplished in many different ways. Two methods are provided here:

#### Method #1: Directly installing via `pip`:
To simply install the necessary dependencies into your system, use the following commands.

*Note that this may upgrade/replace existing packages you may already have installed.*

```bash
#!/bin/bash
cd gym-mupen64plus

# Install the gym-mupen64plus package (and dependencies)
pip install -e .
```

#### Method #2: Installing in a [conda environment](http://conda.pydata.org/docs/using/envs.html):
To minimize disruption to your system and to prevent version conflicts with libraries you may already have installed, you can set up a conda environment with the following commands.

```bash
#!/bin/bash
cd gym-mupen64plus

# Create the conda environment with all the necessary requirements
conda env create -f environment.yml

# Activate the new environment
source activate gym-mupen64plus

# Install the gym-mupen64plus package in the new environment
pip install -e .
```

### Configuration

A configuration file ([`config.yml`](gym_mupen64plus/envs/config.yml)) has been provided for the core wrapper where the primary settings are stored. This configuration may vary on your system, so please take a look at the available settings and adjust as necessary.

Additionally, each game environment may specify configuration values which will be stored in a separate config file in the game's specific subdirectory (see each game's README for those details).


## XVFB

The environment is currently configured to use [XVFB](https://www.x.org/archive/X11R7.6/doc/man/man1/Xvfb.1.xhtml) by default. This allows the emulator to run behind-the-scenes and simplifies configuration. The config file includes a flag to turn this behavior on/off (see below for details running with the flag turned off). 

### Viewing the emulator in XVFB
Since the emulator runs off-screen, the environment provides a `render()` call which displays a window with the screen pixels. Each call to `render()` will update this display. For example, an agent can make this call between each `step()`.

### Connecting to XVFB with VNC
When calling `reset()`, the environment handles navigating menus and getting the game ready for the next episode. This is a blocking call, so `render()` will not show what is happening in-between. An alternative view into the XVFB display is using VNC. You can connect a VNC server to the XVFB display using the following command:
```bash
x11vnc -display :1 -localhost -forever -viewonly &
```
*(where `:1` matches the chosen display number; the startup output will show "`Using DISPLAY :1`" in blue)*

Then you can use your favorite VNC client to connect to `localhost` to watch the XVFB display in real-time. Note that running the VNC server and client can cause some performance overhead.

### Running without XVFB
If XVFB is turned off, the emulator will run in your default X display manager. As a result, the display manager positions the emulator window (we have no control over where the window is positioned). This means that you will need to configure the offset values to ensure we are capturing the correct portion of the screen. Additionally, it means the emulator must remain the top-most window for the entirety of the session. Otherwise, the AI agent will see whatever is on-screen rather than the emulator window.
