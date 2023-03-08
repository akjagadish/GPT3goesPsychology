import openai
import gym
import envs.bandits
import time
import pandas as pd
import numpy as np
import torch

num2words = {0: 'zero', 1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five'}
env = gym.make('palminteri2017-v0')
engine = "text-davinci-002"

def act(text=None):
    # openai.api_key = "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"
    # response = openai.Completion.create(
    #     engine = engine,
    #     prompt = text,
    #     max_tokens = 1,
    #     temperature = 0.0,
    # )
    return torch.tensor([np.random.choice([0,1])]) #response.choices[0].text.strip()

num_tasks = 1

for task in range(num_tasks):
    actions = [None, None, None, None, None]
    env.reset()

    for t in range(5):
        action = act()
        observation, reward, done, _ = env.step(action)
        print(observation, reward, done)

