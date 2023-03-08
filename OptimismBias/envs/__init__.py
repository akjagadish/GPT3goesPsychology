from gym.envs.registration import register

register(
    id='palminteri2017-v0',
    entry_point='envs.bandits:OptimismBiasTaskPalminteri',
    kwargs={'num_actions': 2, 'reward_scaling': 1},
)
