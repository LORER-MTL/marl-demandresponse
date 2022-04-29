#%% Imports

from config import config_dict
from cli import cli_train
from agents.ppo import PPO
from env.MA_DemandResponse import MADemandResponseEnv
from metrics import Metrics
from plotting import colorPlotTestAgentHouseTemp
from utils import (
    normStateDict,
    testAgentHouseTemperature,
    saveActorNetDict,
    adjust_config,
    render_and_wandb_init,
    test_ppo_agent
)

import os
import random
import numpy as np
from collections import namedtuple

#%% Functions

def train_ppo(env, agent, opt, config_dict, render, log_wandb, wandb_run):

    # Initialize render, if applicable
    if render:
        from env.renderer import Renderer
        renderer = Renderer(env.nb_agents)

    # Initialize variables
    Transition = namedtuple("Transition", ["state", "action", "a_log_prob", "reward", "next_state"])  
    time_steps_per_episode = int(opt.nb_time_steps/opt.nb_tr_episodes)
    time_steps_per_epoch = int(opt.nb_time_steps/opt.nb_tr_epochs)
    time_steps_train_log = int(opt.nb_time_steps/opt.nb_tr_logs)
    time_steps_test_log = int(opt.nb_time_steps/opt.nb_test_logs)
    prob_on_test_on = np.empty(100)
    prob_on_test_off = np.empty(100)
    metrics = Metrics()

    # Get first observation
    obs_dict = env.reset()

    for t in range(opt.nb_time_steps):
        
        # Render observation
        if render:
            renderer.render(obs_dict)
            
        # Select action with probabilities
        action_and_prob = {k: agent.select_action(normStateDict(obs_dict[k], config_dict), temp=opt.exploration_temp) for k in obs_dict.keys()}
        action = {k: action_and_prob[k][0] for k in obs_dict.keys()}
        action_prob = {k: action_and_prob[k][1] for k in obs_dict.keys()}
        
        # Take action and get new transition
        next_obs_dict, rewards_dict, dones_dict, info_dict = env.step(action)
        
        # Render next observation
        if render and t >= opt.render_after:
            renderer.render(next_obs_dict)

        # Storing in replay buffer
        for k in obs_dict.keys():
            agent.store_transition(Transition(normStateDict(obs_dict[k], config_dict), action[k], action_prob[k], rewards_dict[k], normStateDict(next_obs_dict[k], config_dict)))
        
        # Update metrics
        metrics.update("0_1", next_obs_dict, rewards_dict, env)

        # Set next state as current state
        obs_dict = next_obs_dict

        # New episode, reset environment
        if t % time_steps_per_episode == time_steps_per_episode - 1:     # Episode: reset environment
            print(f"New episode at time {t}")
            obs_dict = env.reset()

        # Epoch: update agent
        if t % time_steps_per_epoch == time_steps_per_epoch - 1 and len(agent.buffer) >= agent.batch_size:
            print(f"Updating agent at time {t}")
            agent.update(t)

        # Log train statistics
        if t % time_steps_train_log == time_steps_train_log - 1:       # Log train statistics
            #print("Logging stats at time {}".format(t))
            logged_metrics = metrics.log(t, time_steps_train_log)
            if log_wandb:
                wandb_run.log(logged_metrics)
            metrics.reset()

        # Test policy
        if t % time_steps_test_log == time_steps_test_log - 1:        # Test policy
            print(f"Testing at time {t}")
            prob_on_test_on = np.vstack((prob_on_test_on, testAgentHouseTemperature(agent, obs_dict["0_1"], 10, 30, config_dict, obs_dict["0_1"]["hvac_cooling_capacity"]/obs_dict["0_1"]["hvac_COP"])))
            prob_on_test_off = np.vstack((prob_on_test_off, testAgentHouseTemperature(agent, obs_dict["0_1"], 10, 30, config_dict, 0.0)))
            mean_test_return = test_ppo_agent(agent, env, config_dict, opt)
            if log_wandb:
                wandb_run.log({"Mean test return": mean_test_return, "Training steps": t})
            else:
                print("Training step - {t} - Mean test return: {mean_test_return}")

    if render:
        renderer.__del__(obs_dict)

    colorPlotTestAgentHouseTemp(prob_on_test_on, prob_on_test_off, 10, 30, time_steps_test_log, log_wandb)

    if opt.save_actor_name:
        path = os.path.join(".", "actors", opt.save_actor_name)
        saveActorNetDict(agent, path)
        
#%% Train

if __name__ == "__main__":
    import os
    os.environ["WANDB_SILENT"] = "true"
    opt = cli_train()
    adjust_config(opt, config_dict)
    render, log_wandb, wandb_run = render_and_wandb_init(opt, config_dict)
    random.seed(opt.env_seed)
    env = MADemandResponseEnv(config_dict)
    agent = PPO(config_dict, opt)
    train_ppo(env, agent, opt, config_dict, render, log_wandb, wandb_run)