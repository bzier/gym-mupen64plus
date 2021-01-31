#!/bin/python
import gym, gym_mupen64plus

env = gym.make('Mario-Kart-Luigi-Raceway-v0')
env.reset()

print("NOOP waiting for green light")
for i in range(18):
    (obs, rew, end, info) = env.step([0, 0, 0, 0, 0]) # NOOP until green light

print("GO! ...drive straight as fast as possible...")
for i in range(50):
    (obs, rew, end, info) = env.step([0, 0, 1, 0, 0]) # Drive straight

print("Doughnuts!!")
for i in range(10000):
    if i % 100 == 0:
        print("Step " + str(i))
    (obs, rew, end, info) = env.step([-80, 0, 1, 0, 0]) # Hard-left doughnuts!
    (obs, rew, end, info) = env.step([-80, 0, 0, 0, 0]) # Hard-left doughnuts!

raw_input("Press <enter> to exit... ")

env.close()
