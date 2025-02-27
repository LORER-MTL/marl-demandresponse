from copy import deepcopy
import os
from collections import namedtuple
from typing import Dict, List

import numpy as np
import pydantic
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.distributions import Categorical
from torch.utils.data.sampler import BatchSampler, SubsetRandomSampler

from app.core.agents.trainables.network import Actor, Critic
from app.core.agents.trainables.trainable import Trainable
from app.utils.logger import logger


class PPOProperties(pydantic.BaseModel):
    """Properties for PPO agent."""

    actor_layers: list[int] = pydantic.Field(
        default=[100, 100],
        description="List of layer sizes for the actor network.",
    )
    critic_layers: list[int] = pydantic.Field(
        default=[100, 100],
        description="List of layer sizes for the critic network.",
    )
    gamma: float = pydantic.Field(
        default=0.99,
        description="Discount factor for the reward.",
    )
    lr_critic: float = pydantic.Field(
        default=3e-3,
        description="Learning rate for the critic network.",
    )
    lr_actor: float = pydantic.Field(
        default=3e-3,
        description="Learning rate for the actor network.",
    )
    clip_param: float = pydantic.Field(
        default=0.2,
        description="Clipping parameter for the PPO loss.",
    )
    max_grad_norm: float = pydantic.Field(
        default=0.5,
        description="Maximum norm for the gradient clipping.",
    )
    ppo_update_time: int = pydantic.Field(
        default=10,
        description="Update time for the PPO agent.",
    )
    batch_size: int = pydantic.Field(
        default=256,
        description="Batch size for the PPO agent.",
    )
    zero_eoepisode_return: bool = pydantic.Field(
        default=False,
    )


Transition = namedtuple(
    "Transition", ["state", "action", "a_log_prob", "reward", "next_state", "done"]
)


class PPO(Trainable):
    def __init__(
        self, config: PPOProperties, num_state=22, num_action=2, seed=1
    ) -> None:
        self.seed = seed
        self.last_actions: Dict[int, bool] = {}
        self.last_probs: Dict[int, float] = {}
        torch.manual_seed(self.seed)
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        # if True:
        #    self.actor_net = OldActor(num_state=num_state, num_action=num_action)
        #    self.critic_net = OldCritic(num_state=num_state)
        self.actor_net = Actor(
            num_state=num_state,
            num_action=num_action,
            layers=config.actor_layers,
        ).to(self.device)
        self.critic_net = Critic(num_state=num_state, layers=config.critic_layers).to(
            self.device
        )
        # TODO: change this static value (only for tests)
        self.nb_agents = num_action
        self.batch_size = config.batch_size
        self.ppo_update_time = config.ppo_update_time
        self.max_grad_norm = config.max_grad_norm
        self.clip_param = config.clip_param
        self.gamma = config.gamma
        self.lr_actor = config.lr_actor
        self.lr_critic = config.lr_critic
        self.zero_eoepisode_return = config.zero_eoepisode_return

        # Initialize buffer
        self.buffer: Dict[int, List[Transition]] = {}
        for agent in range(self.nb_agents):
            self.buffer[agent] = []

        logger.info(
            "ppo_update_time: {}, max_grad_norm: {}, clip_param: {}, gamma: {}, batch_size: {}, lr_actor: {}, lr_critic: {}".format(
                self.ppo_update_time,
                self.max_grad_norm,
                self.clip_param,
                self.gamma,
                self.batch_size,
                self.lr_actor,
                self.lr_critic,
            )
        )
        self.training_step = 0

        self.actor_optimizer = optim.Adam(self.actor_net.parameters(), self.lr_actor)
        self.critic_net_optimizer = optim.Adam(
            self.critic_net.parameters(), self.lr_critic
        )

    def select_actions(self, observations: List[np.ndarray]) -> Dict[int, bool]:
        actions: Dict[int, bool] = {}
        probs: Dict[int, float] = {}
        for obs_id, obs in enumerate(observations):
            state = torch.from_numpy(obs).float().unsqueeze(0).to(self.device)
            with torch.no_grad():
                # pylint: disable=not-callable
                action_prob = self.actor_net(state)
            c = Categorical(action_prob.cpu())
            action = c.sample()
            actions[obs_id] = bool(action.item())
            probs[obs_id] = action_prob[:, action.item()].item()
        self.last_probs = probs
        self.last_actions = actions
        return actions

    def get_value(self, state):
        # state = torch.from_numpy(state)
        state = state.to(self.device)
        with torch.no_grad():
            # pylint: disable=not-callable
            value = self.critic_net(state)
        return value.cpu().item()

    def reset_buffer(self) -> None:
        self.buffer = {}
        for agent in range(self.nb_agents):
            self.buffer[agent] = []

    def store_transition(
        self,
        observations: List[np.ndarray],
        next_observations: List[np.ndarray],
        rewards: Dict[int, float],
        done: bool,
    ) -> None:
        for agent in range(self.nb_agents):
            transition = Transition(
                observations[agent],
                self.last_actions[agent],
                self.last_probs[agent],
                rewards[agent],
                next_observations[agent],
                done,
            )
            self.buffer[agent].append(transition)

    def update(self, t) -> None:
        if len(self.buffer[0]) < self.batch_size:
            return
        else:
            sequential_buffer = []
            for agent in range(self.nb_agents):
                sequential_buffer += self.buffer[agent]

            state_np = np.array([t.state for t in sequential_buffer])
            next_state_np = np.array([t.next_state for t in sequential_buffer])
            action_np = np.array([t.action for t in sequential_buffer])
            old_action_log_prob_np = np.array([t.a_log_prob for t in sequential_buffer])

            state = torch.tensor(state_np, dtype=torch.float).to(self.device)
            next_state = torch.tensor(next_state_np, dtype=torch.float).to(self.device)
            action = (
                torch.tensor(action_np, dtype=torch.long).view(-1, 1).to(self.device)
            )
            reward = [t.reward for t in sequential_buffer]
            old_action_log_prob = (
                torch.tensor(old_action_log_prob_np, dtype=torch.float)
                .view(-1, 1)
                .to(self.device)
            )
            done = [t.done for t in sequential_buffer]
        Gt = []
        for i in reversed(range(len(reward))):
            if done[i]:
                if self.zero_eoepisode_return:
                    R = 0
                else:
                    R = self.get_value(
                        next_state[i]
                    )  # When last state of episode, start from estimated value of next state
            R = reward[i] + self.gamma * R
            Gt.insert(0, R)
        Gt = torch.tensor(Gt, dtype=torch.float).to(self.device)
        ratios = np.array([])
        clipped_ratios = np.array([])
        gradient_norms = np.array([])
        logger.info("The agent is updating....")
        for i in range(self.ppo_update_time):
            for index in BatchSampler(
                SubsetRandomSampler(range(len(sequential_buffer))),
                self.batch_size,
                False,
            ):
                if self.training_step % 1000 == 0:
                    logger.info(
                        "Time step: {} ，train {} times".format(t, self.training_step)
                    )
                # with torch.no_grad():
                Gt_index = Gt[index].view(-1, 1)

                # pylint: disable=not-callable
                V = self.critic_net(state[index])
                delta = Gt_index - V
                advantage = delta.detach()

                # epoch iteration, PPO core
                # pylint: disable=not-callable
                action_prob = self.actor_net(state[index]).gather(
                    1, action[index]
                )  # new policy
                ratio = action_prob / old_action_log_prob[index]
                clipped_ratio = torch.clamp(
                    ratio, 1 - self.clip_param, 1 + self.clip_param
                )
                ratios = np.append(ratios, ratio.cpu().detach().numpy())
                clipped_ratios = np.append(
                    clipped_ratios, clipped_ratio.cpu().detach().numpy()
                )

                surr1 = ratio * advantage
                surr2 = clipped_ratio * advantage

                # update actor network
                action_loss = -torch.min(surr1, surr2).mean()  # MAX->MIN desent
                # self.writer.add_scalar('loss/action_loss', action_loss, global_step=self.training_step)
                self.actor_optimizer.zero_grad()
                action_loss.backward()
                gradient_norm = nn.utils.clip_grad_norm_(
                    self.actor_net.parameters(), self.max_grad_norm
                )
                gradient_norms = np.append(gradient_norms, gradient_norm.cpu().detach())
                self.actor_optimizer.step()

                # update critic network
                value_loss = F.mse_loss(Gt_index, V)
                # self.writer.add_scalar('loss/value_loss', value_loss, global_step=self.training_step)
                self.critic_net_optimizer.zero_grad()
                value_loss.backward()
                nn.utils.clip_grad_norm_(
                    self.critic_net.parameters(), self.max_grad_norm
                )
                self.critic_net_optimizer.step()
                self.training_step += 1

        self.reset_buffer()  # clear experience

    # TODO: Move this to abstract class
    def save(self, path: str, time_step=None) -> None:
        if not os.path.exists(path):
            os.makedirs(path)
        actor_net = self.actor_net
        if time_step:
            torch.save(
                actor_net.state_dict(),
                os.path.join(path, "actor" + str(time_step) + ".pth"),
            )
        else:
            torch.save(actor_net.state_dict(), os.path.join(path, "actor.pth"))
