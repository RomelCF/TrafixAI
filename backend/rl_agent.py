import os
import random
import threading
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

torch.set_num_threads(1)
torch.set_num_interop_threads(1)

class DQNNetwork(nn.Module):
    def __init__(self, state_dim, action_dim):
        super(DQNNetwork, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim)
        )

    def forward(self, x):
        return self.fc(x)

class ReplayBuffer:
    def __init__(self, capacity=2000):
        self.capacity = capacity
        self.buffer = []
        self.position = 0
        self.lock = threading.Lock()

    def push(self, state, action, reward, next_state, done):
        with self.lock:
            if len(self.buffer) < self.capacity:
                self.buffer.append(None)
            self.buffer[self.position] = (state, action, reward, next_state, done)
            self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size):
        with self.lock:
            batch = random.sample(self.buffer, batch_size)
            state, action, reward, next_state, done = zip(*batch)
            return (np.array(state, dtype=np.float32), 
                    np.array(action, dtype=np.int64), 
                    np.array(reward, dtype=np.float32), 
                    np.array(next_state, dtype=np.float32), 
                    np.array(done, dtype=np.float32))

    def __len__(self):
        with self.lock:
            return len(self.buffer)

class SemaforoRLAgent:
    def __init__(self, state_dim=20, action_dim=7, lr=1e-3, gamma=0.95, 
                 epsilon_start=1.0, epsilon_end=0.05, epsilon_decay=0.995):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_min = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = 32
        
        self.device = torch.device("cpu")
        self.model_lock = threading.Lock()
        
        self.policy_net = DQNNetwork(state_dim, action_dim).to(self.device)
        self.target_net = DQNNetwork(state_dim, action_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.buffer = ReplayBuffer(capacity=5000)
        self.steps_done = 0
        self.reward_history = []
        self.loss_history = []

    def select_action(self, state, evaluate=False):
        if not evaluate and random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)
            
        with torch.no_grad():
            state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            with self.model_lock:
                q_values = self.policy_net(state_t)
            return int(q_values.argmax(dim=1).item())

    def update_epsilon(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def train_step(self):
        if len(self.buffer) < self.batch_size:
            return None
            
        states, actions, rewards, next_states, dones = self.buffer.sample(self.batch_size)
        
        states_t = torch.FloatTensor(states).to(self.device)
        actions_t = torch.LongTensor(actions).unsqueeze(1).to(self.device)
        rewards_t = torch.FloatTensor(rewards).unsqueeze(1).to(self.device)
        next_states_t = torch.FloatTensor(next_states).to(self.device)
        dones_t = torch.FloatTensor(dones).unsqueeze(1).to(self.device)
        
        with self.model_lock:
            curr_q = self.policy_net(states_t).gather(1, actions_t)
            
            with torch.no_grad():
                next_q = self.target_net(next_states_t).max(1)[0].unsqueeze(1)
                target_q = rewards_t + (1 - dones_t) * self.gamma * next_q
                
            loss = nn.functional.smooth_l1_loss(curr_q, target_q)
            
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), max_norm=1.0)
            self.optimizer.step()
            
            self.steps_done += 1
            
            if self.steps_done % 100 == 0:
                self.target_net.load_state_dict(self.policy_net.state_dict())
                
            self.loss_history.append(float(loss.item()))
            return float(loss.item())

    def save(self, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with self.model_lock:
            torch.save({
                'policy_state_dict': self.policy_net.state_dict(),
                'target_state_dict': self.target_net.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'epsilon': self.epsilon,
                'steps_done': self.steps_done,
                'reward_history': self.reward_history
            }, filepath)
        print(f"Agente RL guardado en {filepath}")

    def load(self, filepath):
        if os.path.exists(filepath):
            try:
                checkpoint = torch.load(filepath, map_location=self.device)
                with self.model_lock:
                    self.policy_net.load_state_dict(checkpoint['policy_state_dict'])
                    self.target_net.load_state_dict(checkpoint['target_state_dict'])
                    self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
                    self.epsilon = checkpoint.get('epsilon', self.epsilon)
                    self.steps_done = checkpoint.get('steps_done', self.steps_done)
                    self.reward_history = checkpoint.get('reward_history', self.reward_history)
                print(f"Agente RL cargado desde {filepath}")
                return True
            except Exception as e:
                print(f"Error cargando agente RL: {e}")
        return False

