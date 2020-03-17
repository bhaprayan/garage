"""Variant of the HalfCheetahEnv with different target directions."""
import numpy as np

from garage.envs.half_cheetah_env_meta_base import HalfCheetahEnvMetaBase


class HalfCheetahDirEnv(HalfCheetahEnvMetaBase):
    """Half-cheetah environment with target direction, as described in [1].

    The code is adapted from
    https://github.com/cbfinn/maml_rl/blob/9c8e2ebd741cb0c7b8bf2d040c4caeeb8e06cc95/rllab/envs/mujoco/half_cheetah_env_rand_direc.py

    The half-cheetah follows the dynamics from MuJoCo [2], and receives at each
    time step a reward composed of a control cost and a reward equal to its
    velocity in the target direction. The tasks are generated by sampling the
    target directions from a Bernoulli distribution on {-1, 1} with parameter
    0.5 (-1: backward, +1: forward).

    [1] Chelsea Finn, Pieter Abbeel, Sergey Levine, "Model-Agnostic
        Meta-Learning for Fast Adaptation of Deep Networks", 2017
        (https://arxiv.org/abs/1703.03400)
    [2] Emanuel Todorov, Tom Erez, Yuval Tassa, "MuJoCo: A physics engine for
        model-based control", 2012
        (https://homes.cs.washington.edu/~todorov/papers/TodorovIROS12.pdf)

    Args:
        task (dict or None):
            direction (float): Target direction, either -1 or 1.

    """

    def __init__(self, task=None):
        task = task or {'direction': 1.}
        self._goal_dir = task['direction']
        super().__init__()

    def step(self, action):
        """Take one step in the environment.

        Equivalent to step in HalfCheetahEnv, but with different rewards.

        Args:
            action (np.ndarray): The action to take in the environment.

        Returns:
            tuple:
                * observation (np.ndarray): The observation of the environment.
                * reward (float): The reward acquired at this time step.
                * done (boolean): Whether the environment was completed at this
                    time step. Always False for this environment.
                * infos (dict):
                    * reward_forward (float): Reward for moving, ignoring the
                        control cost.
                    * reward_ctrl (float): The reward for acting i.e. the
                        control cost (always negative).
                    * task_dir (float): Target direction. 1.0 for forwards,
                        -1.0 for backwards.

        """
        xposbefore = self.sim.data.qpos[0]
        self.do_simulation(action, self.frame_skip)
        xposafter = self.sim.data.qpos[0]

        forward_vel = (xposafter - xposbefore) / self.dt
        forward_reward = self._goal_dir * forward_vel
        ctrl_cost = 0.5 * 1e-1 * np.sum(np.square(action))

        observation = self._get_obs()
        reward = forward_reward - ctrl_cost
        done = False
        infos = dict(reward_forward=forward_reward,
                     reward_ctrl=-ctrl_cost,
                     task_dir=self._goal_dir)
        return observation, reward, done, infos

    def sample_tasks(self, num_tasks):
        """Sample a list of `num_tasks` tasks.

        Args:
            num_tasks (int): Number of tasks to sample.

        Returns:
            list[dict[str, float]]: A list of "tasks," where each task is a
                dictionary containing a single key, "direction", mapping to -1
                or 1.

        """
        directions = (
            2 * self.np_random.binomial(1, p=0.5, size=(num_tasks, )) - 1)
        tasks = [{'direction': direction} for direction in directions]
        return tasks

    def set_task(self, task):
        """Reset with a task.

        Args:
            task (dict[str, float]): A task (a dictionary containing a single
                key, "direction", mapping to -1 or 1).

        """
        self._goal_dir = task['direction']
