import gym
import stable_baselines as sb
import numpy as np
from stable_baselines.common.vec_env import SubprocVecEnv
from stable_baselines.common import set_global_seeds, make_vec_env
from stable_baselines import ACKTR
import stable_baselines.common as sbc
from stable_baselines.gail import ExpertDataset
import os



root_dir = os.getcwd()
model_name = root_dir + '/models/'+ 'pretrained_ppo2_revised'
use_vec_envs = True
number_of_vec_envs = 8
framestack = 0 #NOTE: cannot use framestacking and pretraining together
use_pretraining = False
expert_dir = root_dir + '/' + 'i_am_the_expert.npz'
traj_limitation = -1 #-1 uses whole dataset
pretraining_epochs = 44
training_iterations = 200000000
policy = 'CnnPolicy'
seed = 0
log_dir = root_dir + '/' + 'stats/pretrain_ppo2_revised2'
vid_dir = root_dir + '/' + 'videos/pretrain_ppo2_revised2'
vid_freq = 500000
vid_length = 1750
verbose = 1
num_levels = 100
seq_levels = True
record = True
normalize = True
learning_rate = sbc.schedules.LinearSchedule(50000, final_p=5e-5, initial_p=2.5e-3)
auto_save = root_dir + '/models/' + 'autosave'
save_freq = 500000

#Note: Cannot record after loading!




print('-'*50)
print('V6')
print('-'*50)
print("\n\n\nInitializing\n\n\n")
def make_env(rank, seed=seed):
	def func():
		env = gym.make(id='procgen:procgen-fruitbot-v0', use_sequential_levels=seq_levels, num_levels=num_levels, distribution_mode='easy')
		env.seed(rank+seed)
		return env
	set_global_seeds(seed)
	return func

vid_trigger = lambda step: (step % vid_freq == 0)

print("Setting Up Vectorized Environment")

def make_vec(num):
	return SubprocVecEnv([make_env(i) for i in range(num)], start_method='fork')


if use_vec_envs:
	env = make_vec(number_of_vec_envs)
	if normalize:
		env = sbc.vec_env.VecNormalize(env)
	if framestack:
		env = sbc.vec_env.VecFrameStack(env, framestack)
	if record:
		env = sbc.vec_env.VecVideoRecorder(env, vid_dir, vid_trigger, video_length=vid_length)
else:
	env = sbc.vec_env.DummyVecEnv([make_env(0)])
	if normalize:
		env = sbc.vec_env.VecNormalize(env)


eval = sbc.callbacks.CheckpointCallback(save_freq=save_freq, save_path=auto_save, name_prefix='revised_ppo2_')

model = sb.PPO2.load(model_name, env, {'learning_rate': learning_rate.value, 'tensorboard_log' : log_dir})

model.save(model_name + '_sanity2')

if use_pretraining:
	print("Pretraining\n")
	dataset = ExpertDataset(expert_path=expert_dir, traj_limitation=traj_limitation, verbose=verbose)
	model.pretrain(dataset, n_epochs=pretraining_epochs)

print("Training")
try:
	model.learn(training_iterations, callback=eval)
except:
	print("Error or interruption; saving model")

model.save(model_name + '_revised2')

env.close()
