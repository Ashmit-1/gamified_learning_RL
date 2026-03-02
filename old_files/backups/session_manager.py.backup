"""
Student Session Manager for RL-based Quiz System

Manages the reinforcement learning interaction loop for a single student
on a specific topic.
"""

from typing import Dict, List, Optional, Tuple
from rl_agent import (
    QLearningAgent,
    compute_state,
    compute_reward,
    ACTION_TO_PARAMS,
    ACTION_NAMES
)
import uuid


class StudentSession:
    """
    Manages a single student's learning session for a topic.
    
    Implements the RL interaction loop:
    1. Observe state
    2. Select action (teaching strategy)
    3. Generate question based on action
    4. Receive answer
    5. Compute reward
    6. Update Q-table
    7. Transition to next state
    """
    
    def __init__(self, topic: str, agent: QLearningAgent, pool: Dict[str, List[Dict]]):
        """
        Initialize a new session.
        
        Args:
            topic: Learning topic
            agent: RL agent instance
            pool: Pre-generated question pool
        """
        self.session_id = str(uuid.uuid4())
        self.topic = topic
        self.agent = agent
        self.pool = pool
        
        # Track usage per category
        self.category_usage = {
            "easy_conceptual": 0,
            "medium_application": 0,
            "hard_problem_solving": 0,
            "easy_revision": 0
        }
        
        # Map RL action IDs to pool category names
        self.id_to_category = {
            0: "easy_conceptual",
            1: "medium_application",
            2: "hard_problem_solving",
            3: "easy_revision"
        }
        
        # Session state
        self.answer_history: List[Dict] = []
        self.current_state: Optional[Tuple[int, int]] = None
        self.current_action: Optional[int] = None
        self.current_question: Optional[Dict] = None
        self.question_count = 0
        
        # Initialize state
        self.current_state = compute_state([])
        
        print(f"\n{'='*60}")
        print(f"[SESSION] Started new quiz session (POOL BASED) for topic: {topic}")
        print(f"[SESSION] Session ID: {self.session_id}")
        print(f"[SESSION] Initial state: {self._state_to_string(self.current_state)}")
        print(f"{'='*60}\n")
    
    def _state_to_string(self, state: Tuple[int, int]) -> str:
        """Convert state tuple to human-readable string."""
        mastery_map = {0: "Low", 1: "Medium", 2: "High"}
        accuracy_map = {0: "Poor", 1: "Good"}
        return f"(Mastery: {mastery_map[state[0]]}, Recent: {accuracy_map[state[1]]})"
    
    def get_next_question(self) -> Dict:
        """
        Use RL agent to select next action and POP the corresponding question from the pool.
        
        Returns:
            The selected question dictionary.
        """
        # Select action using epsilon-greedy
        self.current_action = self.agent.select_action(self.current_state, training=True)
        category = self.id_to_category[self.current_action]
        action_name = ACTION_NAMES[self.current_action]
        
        # Check if category is empty
        if not self.pool.get(category):
            print(f"[SESSION WARNING] Category '{category}' is EMPTY!")
            # Fallback: Try other categories if possible, or raise error for regeneration
            # For robust uniqueness, we want the backend to catch this and refill.
            raise IndexError(f"Pool category '{category}' exhausted")
            
        # POP the question (absolute removal)
        question = self.pool[category].pop(0) 
        
        self.category_usage[category] += 1
        self.current_question = question
        self.question_count += 1
        
        print(f"[RL STEP {self.question_count}]")
        print(f"  State: {self._state_to_string(self.current_state)}")
        print(f"  Action: {action_name} (A{self.current_action})")
        print(f"  Source: Pool '{category}' (Popped 1, {len(self.pool[category])} left)")
        print(f"  ε: {self.agent.epsilon:.3f}")
        
        return {
            "question": question,
            "action_name": action_name,
            "action_id": self.current_action
        }
    
    def process_answer(
        self,
        correct: bool,
        difficulty: str,
        question_text: str
    ) -> Dict:
        """
        Process student answer and update RL agent.
        """
        # Record answer in history
        self.answer_history.append({
            'correct': correct,
            'difficulty': difficulty,
            'question': question_text[:50] + "..."  # Truncate for logging
        })
        
        # Compute new state
        new_state = compute_state(self.answer_history)
        
        # Compute reward
        reward = compute_reward(correct, self.current_state, new_state, self.current_action)
        
        # Update Q-table
        old_q, new_q = self.agent.update(
            self.current_state,
            self.current_action,
            reward,
            new_state
        )
        
        # Logging
        print(f"  Answer: {'✓ Correct' if correct else '✗ Wrong'}")
        print(f"  Reward: {reward:+.1f}")
        print(f"  Q-update: {old_q:.3f} → {new_q:.3f}")
        print(f"  New State: {self._state_to_string(new_state)}\n")
        
        # Transition to new state
        self.current_state = new_state
        
        # Decay epsilon after each question
        self.agent.decay_epsilon()
        
        return {
            "reward": reward,
            "old_q_value": old_q,
            "new_q_value": new_q,
            "state_transition": {
                "old": self._state_to_string(compute_state(self.answer_history[:-1]) if len(self.answer_history) > 1 else (0,0)),
                "new": self._state_to_string(new_state)
            },
            "correct": correct
        }
    
    def get_session_summary(self) -> Dict:
        """Get summary statistics for the session."""
        correct_count = sum(1 for ans in self.answer_history if ans['correct'])
        total_count = len(self.answer_history)
        
        return {
            "session_id": self.session_id,
            "topic": self.topic,
            "questions_answered": total_count,
            "correct_answers": correct_count,
            "accuracy": correct_count / total_count if total_count > 0 else 0,
            "final_state": self._state_to_string(self.current_state),
            "epsilon": self.agent.epsilon,
            "learning_maturity": self.agent.get_learning_maturity()
        }


class RuleBasedBaseline:
    """
    Simple rule-based baseline for comparison.
    
    Rules:
    - Correct answer → increase difficulty
    - Wrong answer → decrease difficulty
    """
    
    def __init__(self):
        self.difficulty_levels = ["easy", "medium", "hard"]
        self.current_difficulty_idx = 0  # Start with easy
        
    def get_next_difficulty(self) -> str:
        """Get current difficulty level."""
        return self.difficulty_levels[self.current_difficulty_idx]
    
    def update(self, correct: bool):
        """Update difficulty based on correctness."""
        if correct and self.current_difficulty_idx < 2:
            self.current_difficulty_idx += 1
            print(f"[BASELINE] Correct → Difficulty UP to {self.difficulty_levels[self.current_difficulty_idx]}")
        elif not correct and self.current_difficulty_idx > 0:
            self.current_difficulty_idx -= 1
            print(f"[BASELINE] Wrong → Difficulty DOWN to {self.difficulty_levels[self.current_difficulty_idx]}")
        else:
            print(f"[BASELINE] Staying at {self.difficulty_levels[self.current_difficulty_idx]}")
