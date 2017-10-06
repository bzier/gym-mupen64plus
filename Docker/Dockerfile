FROM ubuntu:xenial-20170915


# Setup environment variables in a single layer
ENV \
    # Prevent dpkg from prompting for user input during package setup
    DEBIAN_FRONTEND=noninteractive DEBCONF_NONINTERACTIVE_SEEN=true \
    # mupen64plus will be installed in /usr/games/; add to the $PATH
    PATH=$PATH:/usr/games/ \
    # Set default DISPLAY
    DISPLAY=:0


# Update package cache and install dependencies
RUN apt-get update && \
    apt-get install -y \
        python python-pip python-setuptools python-dev \
        build-essential dpkg-dev libwebkitgtk-dev libjpeg-dev libtiff-dev libgtk2.0-dev \
        libsdl1.2-dev libgstreamer-plugins-base0.10-dev libnotify-dev freeglut3 freeglut3-dev \
        libjson-c2 libjson-c-dev \
        wget git \
        xorg xvfb x11-apps x11vnc \
        imagemagick \
        mupen64plus \
        nano


# TODO: Is upgrading virtualenv necessary?
# Upgrade pip and virtualenv
RUN pip install --upgrade pip virtualenv 


# install VirtualGL (provides vglrun to allow us to run the emulator in XVFB)
# (Check for new releases here: https://github.com/VirtualGL/virtualgl/releases)
ENV VIRTUALGL_VERSION=2.5.2
RUN wget "https://sourceforge.net/projects/virtualgl/files/${VIRTUALGL_VERSION}/virtualgl_${VIRTUALGL_VERSION}_amd64.deb" && \
    apt install ./virtualgl_${VIRTUALGL_VERSION}_amd64.deb && \
    rm virtualgl_${VIRTUALGL_VERSION}_amd64.deb


# clone, build, and install the input bot
# (explicitly specifying commit hash to attempt to guarantee behavior within this container)
WORKDIR /src/mupen64plus-src
RUN git clone https://github.com/mupen64plus/mupen64plus-core && \
        cd mupen64plus-core && \
        git reset --hard 12d136dd9a54e8b895026a104db7c076609d11ff && \
    cd .. && \
    git clone https://github.com/kevinhughes27/mupen64plus-input-bot && \
        cd mupen64plus-input-bot && \
        git reset --hard 40eff412eca6491acb7f70932b87b404c9c3ef70 && \
    make all && \
    make install


# clone the gym environment and install Python requirements
# (explicitly specifying commit hash to attempt to guarantee behavior within this container)
WORKDIR /src
RUN git clone https://github.com/bzier/gym-mupen64plus/ && \
        cd gym-mupen64plus && \
        git reset --hard a94e1a13a12b8cc3e27d16737cb46197adb35b8c && \
    # TODO: Temporary until this is updated in the repo
    sed -i -- 's/wx>=3.0.3/wxPython==4.0.0a1/g' ./setup.py && \
    # TODO: Changing from DISPLAY :1 to :0... maybe handle this differently (spin up a :0 just for nothing, and then use :1)
    sed -i -- 's/XVFB_DISPLAY: :1/XVFB_DISPLAY: :0/g' ./gym_mupen64plus/envs/config.yml && \
    # Install requirements & this package
    pip install -e .


# Declare ROMs as a volume for mounting a host path outside the container
VOLUME /src/gym-mupen64plus/gym_mupen64plus/ROMs/


# Expose the default VNC port for connecting with a client/viewer outside the container
EXPOSE 5900

