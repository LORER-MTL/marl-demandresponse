# %% Imports

import os
import random
from collections import namedtuple

import numpy as np
import wandb

from v0.agents.ppo import PPO
from v0.cli import cli_train
from v0.config import config_dict
from v0.env.MA_DemandResponse import MADemandResponseEnv
from v0.metrics import Metrics
from v0.utils import (
    adjust_config_train,
    normStateDict,
    render_and_wandb_init,
    saveActorNetDict,
    test_ppo_agent,
)

# %% Functions


def train_ppo(env, agent, opt, config_dict, render, log_wandb, wandb_run):
    id_rng = np.random.default_rng()
    unique_ID = str(int(id_rng.random() * 1000000))

    # Initialize render, if applicable
    if render:
        from v0.env.renderer import Renderer

        renderer = Renderer(env.nb_agents)

    # Initialize variables
    Transition = namedtuple(
        "Transition", ["state", "action", "a_log_prob", "reward", "next_state", "done"]
    )
    time_steps_per_episode = int(opt.nb_time_steps / opt.nb_tr_episodes)
    time_steps_per_epoch = int(opt.nb_time_steps / opt.nb_tr_epochs)
    time_steps_train_log = int(opt.nb_time_steps / opt.nb_tr_logs)
    time_steps_test_log = int(opt.nb_time_steps / opt.nb_test_logs)
    time_steps_per_saving_actor = int(
        opt.nb_time_steps / (opt.nb_inter_saving_actor + 1)
    )
    metrics = Metrics()

    # Get first observation
    obs_dict = env.reset()

    for t in range(opt.nb_time_steps):
        # Render observation
        if render:
            renderer.render(obs_dict)

        # Select action with probabilities
        action_and_prob = {
            k: agent.select_action(normStateDict(obs_dict[k], config_dict))
            for k in obs_dict.keys()
        }
        action = {k: action_and_prob[k][0] for k in obs_dict.keys()}
        action_prob = {k: action_and_prob[k][1] for k in obs_dict.keys()}

        # Take action and get new transition
        next_obs_dict, rewards_dict, dones_dict, info_dict = env.step(action)

        # Render next observation
        if render and t >= opt.render_after:
            renderer.render(next_obs_dict)

        # Episode is done
        done = t % time_steps_per_episode == time_steps_per_episode - 1

        # Storing in replay buffer
        for k in obs_dict.keys():
            agent.store_transition(
                Transition(
                    normStateDict(obs_dict[k], config_dict),
                    action[k],
                    action_prob[k],
                    rewards_dict[k],
                    normStateDict(next_obs_dict[k], config_dict),
                    done,
                ),
                k,
            )
            # Update metrics
            metrics.update(k, obs_dict, next_obs_dict, rewards_dict, env)

        # Set next state as current state
        obs_dict = next_obs_dict

        # New episode, reset environment
        if done:
            print(f"New episode at time {t}")
            obs_dict = env.reset()

        # Epoch: update agent
        if (
            t % time_steps_per_epoch == time_steps_per_epoch - 1
            and len(agent.buffer[0]) >= agent.batch_size
        ):
            print(f"Updating agent at time {t}")
            agent.update(t)

        # Log train statistics
        if t % time_steps_train_log == time_steps_train_log - 1:  # Log train statistics
            # print("Logging stats at time {}".format(t))
            logged_metrics = metrics.log(t, time_steps_train_log)
            if log_wandb:
                wandb_run.log(logged_metrics)
            metrics.reset()

        # Test policy
        if t % time_steps_test_log == time_steps_test_log - 1:  # Test policy
            print(f"Testing at time {t}")
            metrics_test = test_ppo_agent(agent, env, config_dict, opt, t)
            if log_wandb:
                wandb_run.log(metrics_test)
            else:
                print("Training step - {}".format(t))

        if opt.save_actor_name and t % time_steps_per_saving_actor == 0 and t != 0:
            path = os.path.join(".", "actors", opt.save_actor_name + unique_ID)
            saveActorNetDict(agent, path, t)
            if log_wandb:
                wandb.save(os.path.join(path, "actor" + str(t) + ".pth"))

    if render:
        renderer.__del__(obs_dict)

    if opt.save_actor_name:
        path = os.path.join(".", "actors", opt.save_actor_name + unique_ID)
        saveActorNetDict(agent, path)
        if log_wandb:
            wandb.save(os.path.join(path, "actor.pth"))


# %% Train

if __name__ == "__main__":
    import os

    os.environ["WANDB_SILENT"] = "true"
    opt = cli_train()
    adjust_config_train(opt, config_dict)
    render, log_wandb, wandb_run = render_and_wandb_init(opt, config_dict)
    random.seed(opt.env_seed)
    env = MADemandResponseEnv(config_dict)
    agent = PPO(config_dict, opt)
    train_ppo(env, agent, opt, config_dict, render, log_wandb, wandb_run)
