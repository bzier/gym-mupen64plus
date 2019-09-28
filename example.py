#!/bin/python
import gym, gym_mupen64plus
import subprocess

def startVNC(display):
    subprocess.call("x11vnc -display :{} -localhost -forever -viewonly &".format(str(display)), shell=True)

env = gym.make('Mario-Kart-Luigi-Raceway-v0')
env.reset()

# Start casting VNC at display 1
startVNC(1)

for i in range(88):
    (obs, rew, end, info) = env.step([0, 0, 0, 0, 0]) # NOOP until green light

for i in range(10000):
    (obs, rew, end, info) = env.step([0, 0, 1, 0, 0]) # Drive straight

raw_input("Press <enter> to exit... ")

env.close()
