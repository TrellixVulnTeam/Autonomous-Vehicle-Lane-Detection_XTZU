# Autonomous-Vehicle-Lane-Detection

OpenAI Gym Environments for Donkey Car

Free software: MIT license
Documentation: https://gym-donkeycar.readthedocs.io/en/latest/
Installation

Download simulator binaries: https://github.com/tawnkramer/gym-donkeycar/releases

Install master version of gym donkey car:

pip install git+https://github.com/tawnkramer/gym-donkeycar
Example Usage

A short and compact introduction for people who know gym environments, but want to understand this one. Simple example code:

import os
import gym
import gym_donkeycar
import numpy as np

# SET UP ENVIRONMENT
# You can also launch the simulator separately in that case, you don't need to pass a `conf` object
exe_path = f"{PATH_TO_APP}/donkey_sim.exe"
port = 9091

conf = { "exe_path" : exe_path, "port" : port }

env = gym.make("donkey-generated-track-v0", conf=conf)

 PLAY
obs = env.reset()
for t in range(100):
  action = np.array([0.0, 0.5]) # drive straight with small speed
   execute the action
  obs, reward, done, info = env.step(action)

 Exit the scene
env.close()
or if you already launched the simulator:

import gym
import numpy as np

import gym_donkeycar

env = gym.make("donkey-warren-track-v0")

obs = env.reset()
try:
    for _ in range(100):
        # drive straight with small speed
        action = np.array([0.0, 0.5])  
        # execute the action
        obs, reward, done, info = env.step(action)
except KeyboardInterrupt:
    # You can kill the program using ctrl+c
    pass

    # Exit the scene
env.close()
see more examples: https://github.com/tawnkramer/gym-donkeycar/tree/master/examples
Action space

A permissable action is a numpy array of length two with first steering and throttle, respectively. E.g. np.array([0,1]) goes straight at full speed, np.array([-5,1]) turns left etc.

# Action Space:

Action names: ['steer', 'throttle']

What you receive back on step:

obs: The image that the donkey is seeing (np.array shape (120,160,3))
reward: a reward that combines game over, how far from center and speed (max=1, min approx -2)
done: Boolean. Game over if cte > max_cte or hit != "none"
info contains:
cte: Cross track error (how far from center line)
positions: x,y,z
speed: positive forward, negative backward
hit: 'none' if all is good.
Example info:

{'pos': (51.49209, 0.7399381, 117.3004),
 'cte': -5.865292,
 'speed': 9.319956,
 'hit': 'none'}
# Environments

"donkey-warehouse-v0"
"donkey-generated-roads-v0"
"donkey-avc-sparkfun-v0"
"donkey-generated-track-v0"
"donkey-roboracingleague-track-v0"
"donkey-waveshare-v0"
"donkey-minimonaco-track-v0"
"donkey-warren-track-v0"
# Credits

Original Source Code

Tawn Kramer - https://github.com/tawnkramer/gym-donkeycar

