"""
Reinforcement Learning Agent for Personalized Quiz System

This module implements a tabular Q-learning agent that learns
optimal question-selection policies for personalized learning.
"""

import numpy as np
import json
import os
from pathlib import Path
from typing import Tuple, List, Dict, Optional

# State space constants
MASTERY_LOW = 0
MASTERY_MEDIUM = 1
MASTERY_HIGH = 2

ACCURACY_POOR = 0
ACCURACY_GOOD = 1

# Action space constants
ACTION_EASY_CONCEPTUAL = 0
ACTION_MEDIUM_APPLICATION = 1
ACTION_HARD_PROBLEM = 2
ACTION_EASY_REVISION = 3

ACTION_NAMES = [
    "Easy Conceptual",
    "Medium Application", 
    "Hard Problem-Solving",
    "Easy Revision"
]

# Action to question parameters mapping
ACTION_TO_PARAMS = {
    ACTION_EASY_CONCEPTUAL: ("easy", "conceptual"),
    ACTION_MEDIUM_APPLICATION: ("medium", "application"),
    ACTION_HARD_PROBLEM: ("hard", "problem-solving"),
    ACTION_EASY_REVISION: ("easy", "revision")
}


class QLearningAgent:
    """
    Tabular Q-learning agent for adaptive quiz question selection.
    
    State: (mastery_level, recent_accuracy)
    - mastery_level ∈ {0, 1, 2} (low, medium, high)
    - recent_accuracy ∈ {0, 1} (poor, good)
    
    Actions: 4 teaching strategies
    - A0: Easy conceptual question
    - A1: Medium application question
    - A2: Hard problem-solving question
    - A3: Easy revision question 
    """
    
    def __init__(
        self,
        alpha: float = 0.1,
        gamma: float = 0.95,
        epsilon: float = 0.3,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.05
    ):
        """
        Initialize Q-learning agent.
        
        Args:
            alpha: Learning rate
            gamma: Discount factor
            epsilon: Initial exploration rate
            epsilon_decay: Decay rate for epsilon
            epsilon_min: Minimum epsilon value
        """
        # Q-table: 6 states x 4 actions
        self.q_table = np.full((6, 4), 1.0)
        
        # Hyperparameters
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        
        # Tracking
        self.episodes = 0
        
    def state_to_index(self, mastery_level: int, recent_accuracy: int) -> int:
        """Convert state tuple to Q-table index."""
        return mastery_level * 2 + recent_accuracy
    
    def select_action(self, state: Tuple[int, int], training: bool = True) -> int:
        """
        Select action using ε-greedy policy.
        
        Args:
            state: (mastery_level, recent_accuracy)
            training: If True, use epsilon-greedy; else use greedy
            
        Returns:
            Selected action index
        """
        state_idx = self.state_to_index(*state)
        
        # Epsilon-greedy exploration
        if training and np.random.random() < self.epsilon:
            action = np.random.randint(0, 4)
            return action
        else:
            # Greedy: select best action
            action = np.argmax(self.q_table[state_idx])
            return action
    
    def update(
        self,
        state: Tuple[int, int],
        action: int,
        reward: float,
        next_state: Tuple[int, int]
    ):
        """
        Update Q-table using Q-learning update rule.
        
        Q(s,a) ← Q(s,a) + α[r + γ max(Q(s',a')) - Q(s,a)]
        """
        s_idx = self.state_to_index(*state)
        s_next_idx = self.state_to_index(*next_state)
        
        # Q-learning update
        current_q = self.q_table[s_idx, action]
        max_next_q = np.max(self.q_table[s_next_idx])
        new_q = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
        
        self.q_table[s_idx, action] = new_q
        
        return current_q, new_q
    
    def decay_epsilon(self):
        """Decay exploration rate."""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
    
    def save_policy(self, topic: str, save_dir: str = "q_tables"):
        """Save Q-table and hyperparameters to disk."""
        Path(save_dir).mkdir(exist_ok=True)
        
        policy_data = {
            "q_table": self.q_table.tolist(),
            "epsilon": self.epsilon,
            "episodes": self.episodes,
            "alpha": self.alpha,
            "gamma": self.gamma
        }
        
        filepath = Path(save_dir) / f"{topic.lower().replace(' ', '_')}.json"
        with open(filepath, 'w') as f:
            json.dump(policy_data, f, indent=2)
        
        print(f"[RL] Saved Q-table for topic '{topic}' (ε={self.epsilon:.3f}, episodes={self.episodes})")
    
    def load_policy(self, topic: str, save_dir: str = "q_tables") -> bool:
        """
        Load Q-table from disk if exists.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        filepath = Path(save_dir) / f"{topic.lower().replace(' ', '_')}.json"
        
        if not filepath.exists():
            print(f"[RL] No saved policy found for topic '{topic}'. Starting fresh.")
            return False
        
        with open(filepath, 'r') as f:
            policy_data = json.load(f)
        
        self.q_table = np.array(policy_data["q_table"])
        self.epsilon = policy_data["epsilon"]
        self.episodes = policy_data["episodes"]
        
        print(f"[RL] Loaded Q-table for topic '{topic}' (ε={self.epsilon:.3f}, episodes={self.episodes})")
        print(f"[RL] Resuming learning with maturity level: {self.get_learning_maturity()}")
        
        return True
    
    def get_learning_maturity(self) -> str:
        """Get qualitative description of learning progress."""
        if self.epsilon > 0.2:
            return "Exploring (high ε)"
        elif self.epsilon > 0.1:
            return "Learning (medium ε)"
        else:
            return "Exploiting (low ε)"


def compute_state(answer_history: List[Dict]) -> Tuple[int, int]:
    """
    Derive RL state from student's answer history.
    
    Args:
        answer_history: List of dicts with keys: 'correct', 'difficulty'
        
    Returns:
        (mastery_level, recent_accuracy) tuple
    """
    if not answer_history:
        # Default initial state
        return (MASTERY_LOW, ACCURACY_POOR)
    
    # Calculate overall accuracy for mastery level
    correct_count = sum(1 for ans in answer_history if ans['correct'])
    total_count = len(answer_history)
    overall_accuracy = correct_count / total_count
    
    if overall_accuracy < 0.4:
        mastery_level = MASTERY_LOW
    elif overall_accuracy < 0.7:
        mastery_level = MASTERY_MEDIUM
    else:
        mastery_level = MASTERY_HIGH
    
    # Calculate recent accuracy (last 3 answers)
    recent_window = answer_history[-3:]
    recent_correct = sum(1 for ans in recent_window if ans['correct'])
    recent_total = len(recent_window)
    recent_accuracy_pct = recent_correct / recent_total
    
    if recent_accuracy_pct >= 0.5:
        recent_accuracy = ACCURACY_GOOD
    else:
        recent_accuracy = ACCURACY_POOR
    
    return (mastery_level, recent_accuracy)


def compute_reward(
    answer_correct: bool,
    old_state: Tuple[int, int],
    new_state: Tuple[int, int], 
    action: int
) -> float:
    """
    Compute reward signal that encourages long-term learning.
    
    Args:
        answer_correct: Whether the answer was correct
        old_state: State before answering
        new_state: State after answering
        
    Returns:
        Reward value
    """
    reward = 0.0
    
    # Immediate correctness
    if answer_correct:
        reward += 1.0
    else:
        reward -= 0.5
    
    old_mastery, old_accuracy = old_state
    new_mastery, new_accuracy = new_state
    
    # Mastery progression (most important)
    if new_mastery > old_mastery:
        reward += 5.0  # Big bonus for leveling up
    elif new_mastery < old_mastery:
        reward -= 3.0  # Penalty for regression
    
    # Recent accuracy improvement
    if new_accuracy > old_accuracy:
        reward += 2.0
    elif new_accuracy < old_accuracy:
        reward -= 1.0

    # Penalize lack of challenge when mastery is already high
    # Penalize lack of challenge at high mastery
    if old_state[0] == MASTERY_HIGH and action in (
        ACTION_EASY_CONCEPTUAL,
        ACTION_EASY_REVISION
    ):
        reward -= 1.5

    if answer_correct and action == ACTION_HARD_PROBLEM:
        reward += 3.0

    return reward
