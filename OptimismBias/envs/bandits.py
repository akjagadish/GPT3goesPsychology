import math
import numpy as np
import gym
from gym import error, spaces, utils
from gym.utils import seeding
from torch.distributions import Normal, Bernoulli, MultivariateNormal
import torch.nn.functional as F
import torch

class OptimismBiasTaskPalminteri(gym.Env):
    metadata = {'render.modes': ['human']}
    def __init__(self, num_actions=2, max_steps_per_context=2, num_contexts=4, reward_scaling=1, batch_size=1): # 1 for simulations
        
        self.num_actions = num_actions
        self.num_contexts = num_contexts
        self.batch_size = batch_size
        self.max_steps_per_context =  max_steps_per_context 
        self.reward_scaling = reward_scaling
        self.action_space = spaces.Discrete(self.num_actions)
        self.probs = {'low':0.25, 'high':0.75}
        self.observation_space = spaces.Box(np.ones(5), np.ones(5)) #  5 = action+reward+context+trial
 
    def reset(self):

        # keep track of time-steps
        self.t = 0
        self.max_steps = self.max_steps_per_context * self.num_contexts

        # generate reward functions
        mean_rewards_context_ll, rewards_context_ll = self.sample_contextual_rewards(context=['low', 'low'])
        mean_rewards_context_lh, rewards_context_lh = self.sample_contextual_rewards(context=['low', 'high'])
        mean_rewards_context_hl, rewards_context_hl = self.sample_contextual_rewards(context=['high', 'low'])
        mean_rewards_context_hh, rewards_context_hh = self.sample_contextual_rewards(context=['high', 'high'])

        self.cue_context = torch.zeros(self.batch_size, self.num_contexts, self.max_steps_per_context, 2)
        self.cue_context[:, 0, :, :] = 0
        self.cue_context[:, 1, :, 1] = 1
        self.cue_context[:, 2, :, 0] = 1
        self.cue_context[:, 3, :, :] = 1

        # stack all the rewards together
        shuffle_idx = torch.randperm(self.max_steps_per_context*self.num_contexts)
        self.mean_rewards = torch.stack((mean_rewards_context_ll, mean_rewards_context_lh, mean_rewards_context_hl, mean_rewards_context_hh), dim=1).reshape(self.batch_size, self.max_steps_per_context*self.num_contexts, self.num_actions)[:, shuffle_idx]
        self.rewards = torch.stack((rewards_context_ll, rewards_context_lh, rewards_context_hl, rewards_context_hh), dim=1).reshape(self.batch_size, self.max_steps_per_context*self.num_contexts, self.num_actions)[:, shuffle_idx] 
        self.contexts = self.cue_context.reshape(self.batch_size, self.max_steps_per_context*self.num_contexts, 2)[:, shuffle_idx]

        last_reward = torch.zeros(self.batch_size)
        last_action = torch.zeros(self.batch_size)

        return self.get_observation(last_reward, last_action, self.t, self.contexts[:, 0])

    def get_observation(self, last_reward, last_action, time_step, cue_context):
        return torch.cat([
            last_reward.unsqueeze(-1),
            last_action.unsqueeze(-1),
            torch.ones(self.batch_size, 1) * time_step,
            cue_context],
            dim=1)

    def sample_contextual_rewards(self, context):
        assert len(context)==self.num_actions, "lengths of context and actions do not match"
        ones = torch.ones((self.batch_size, self.max_steps_per_context, self.num_actions))
        mean_rewards_context = torch.zeros((self.batch_size, self.max_steps_per_context, self.num_actions))
        for idx, option in enumerate(context):
            ones[..., idx] = ones[..., idx]*self.probs[option]
            mean_rewards_context[..., idx] = self.probs[option]
        rewards_context = torch.bernoulli(ones)
        return mean_rewards_context, rewards_context

    def step(self, action):
       
        regrets = self.mean_rewards[:, self.t].max(1).values[0] - self.mean_rewards[:, self.t][:, action][0]
        reward = self.rewards[:, self.t][:, action][0]
        reward = reward / self.reward_scaling
        self.t += 1
        done = True if (self.t >= self.max_steps) else False
        if not done:
            observation = self.get_observation(reward, action.float(), self.t, self.contexts[:, self.t])
        else:
            raise NotImplementedError
        return observation, reward, done, {'regrets': regrets.mean()}
