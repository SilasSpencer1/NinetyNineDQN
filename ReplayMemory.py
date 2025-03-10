import torch
import numpy as np
from collections import namedtuple
import random


Batch = namedtuple(
    'Batch', ('states', 'actions', 'rewards', 'next_states', 'dones')
)


class ReplayMemory:
    def __init__(self, max_size, state_size):
        """Replay memory implemented as a circular buffer."""
        self.max_size = int(max_size)
        self.state_size = state_size

        self.states = torch.empty((max_size, state_size), dtype=torch.float32)
        self.actions = torch.empty((max_size, 1), dtype=torch.long)
        self.rewards = torch.empty((max_size, ), dtype=torch.float32)
        self.next_states = torch.empty((max_size, state_size), dtype=torch.float32)
        self.dones = torch.empty((max_size, ), dtype=torch.bool)

        self.idx = 0 # Pointer to the current location in the circular buffer

        self.size = 0 # Indicates number of transitions currently stored in the buffer

    def add(self, state, action, reward, next_state, done):
        """Add a transition to the buffer."""
        if len(state) != len(next_state):
            return
        self.states[self.idx] = torch.tensor(state, dtype=torch.float32)
        self.actions[self.idx] = torch.tensor(action, dtype=torch.long).unsqueeze(0)
        self.rewards[self.idx] = torch.tensor(reward, dtype=torch.float32)
        self.next_states[self.idx] = torch.tensor(next_state, dtype=torch.float32)
        self.dones[self.idx] = torch.tensor(done, dtype=torch.bool)

        # Circulate the pointer to the next position
        self.idx = (self.idx + 1) % self.max_size
        # Update the current buffer size
        self.size = min(self.size + 1, self.max_size)

    def sample(self, batch_size) -> Batch:
        """Sample a batch of experiences."""
        batch_idx = np.random.choice(self.size, size=min(self.size, batch_size), replace=False)

        #'Batch', ('states', 'actions', 'rewards', 'next_states', 'dones')
        batch = Batch(
            states      =self.states[batch_idx],
            actions     =self.actions[batch_idx],
            rewards     =self.rewards[batch_idx],
            next_states =self.next_states[batch_idx],
            dones       = self.dones[batch_idx]
        )

        return batch

    @staticmethod
    def populate(env, num_steps, memory_bid, memory_play):
        """Populate this replay memory with `num_steps` from the random policy."""
        state = env.reset_game()
        for _ in range(num_steps):
            phase = env.bidding_phase
            action = random.choice(env.possible_actions())
            next_state, reward, done, _ = env.step(action)
            if phase == 1:
                memory_bid.add(state, action, reward, next_state, done)
            else:
                memory_play.add(state, action, reward, next_state, done)

            if done:
                state = env.reset_game()
            else:
                state = next_state