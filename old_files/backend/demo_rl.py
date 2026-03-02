"""
Demo script to test and visualize RL behavior

This script simulates student interactions to demonstrate:
1. Q-learning convergence
2. Policy improvement over episodes
3. Comparison with rule-based baseline
"""

import sys
import random
import numpy as np
from rl_agent import QLearningAgent, compute_state, compute_reward, ACTION_NAMES
from session_manager import RuleBasedBaseline


def simulate_student_answer(difficulty: str, question_type: str, skill_level: float) -> bool:
    """
    Simulate a student answering a question.
    
    Args:
        difficulty: Question difficulty
        question_type: Question type
        skill_level: Student's skill (0.0 to 1.0)
        
    Returns:
        True if answer is "correct"
    """
    # Base probability of correctness based on difficulty
    base_prob = {
        "easy": 0.8,
        "medium": 0.5,
        "hard": 0.2
    }[difficulty]
    
    # Adjust by student skill
    adjusted_prob = base_prob + (skill_level - 0.5) * 0.4
    adjusted_prob = np.clip(adjusted_prob, 0.1, 0.9)
    
    return random.random() < adjusted_prob


def run_rl_episode(agent: QLearningAgent, skill_level: float, num_questions: int = 10) -> dict:
    """Run a single episode with RL agent."""
    answer_history = []
    total_reward = 0
    
    for i in range(num_questions):
        # Get state
        state = compute_state(answer_history)
        
        # Select action
        action = agent.select_action(state, training=True)
        action_name = ACTION_NAMES[action]
        
        # Map action to difficulty/type (simplified)
        if action == 0:  # Easy Conceptual
            difficulty, q_type = "easy", "conceptual"
        elif action == 1:  # Medium Application
            difficulty, q_type = "medium", "application"
        elif action == 2:  # Hard Problem
            difficulty, q_type = "hard", "problem-solving"
        else:  # Easy Revision
            difficulty, q_type = "easy", "revision"
        
        # Simulate answer
        correct = simulate_student_answer(difficulty, q_type, skill_level)
        
        # Record
        answer_history.append({'correct': correct, 'difficulty': difficulty})
        
        # Get new state
        new_state = compute_state(answer_history)
        
        # Compute reward
        reward = compute_reward(correct, state, new_state)
        total_reward += reward
        
        # Update Q-table
        agent.update(state, action, reward, new_state)
        
        # Decay epsilon
        agent.decay_epsilon()
    
    # Calculate accuracy
    correct_count = sum(1 for ans in answer_history if ans['correct'])
    accuracy = correct_count / num_questions
    
    return {
        'accuracy': accuracy,
        'total_reward': total_reward,
        'epsilon': agent.epsilon
    }


def run_baseline_episode(baseline: RuleBasedBaseline, skill_level: float, num_questions: int = 10) -> dict:
    """Run a single episode with rule-based baseline."""
    total_correct = 0
    
    for i in range(num_questions):
        difficulty = baseline.get_next_difficulty()
        correct = simulate_student_answer(difficulty, "conceptual", skill_level)
        
        total_correct += int(correct)
        baseline.update(correct)
    
    return {
        'accuracy': total_correct / num_questions
    }


def main():
    print("\n" + "="*70)
    print("RL QUIZ SYSTEM DEMONSTRATION")
    print("="*70)
    
    # Hyperparameters
    skill_level = 0.5  # Medium skill student
    num_episodes = 50
    num_questions_per_episode = 10
    
    print(f"\nSimulating {num_episodes} episodes with {num_questions_per_episode} questions each")
    print(f"Student skill level: {skill_level:.1f}")
    
    # Initialize agents
    rl_agent = QLearningAgent(epsilon=0.3, epsilon_decay=0.99)
    baseline = RuleBasedBaseline()
    
    # Track metrics
    rl_accuracies = []
    rl_rewards = []
    baseline_accuracies = []
    
    print("\nRunning episodes...")
    print("-" * 70)
    
    for episode in range(num_episodes):
        # RL episode
        rl_result = run_rl_episode(rl_agent, skill_level, num_questions_per_episode)
        rl_accuracies.append(rl_result['accuracy'])
        rl_rewards.append(rl_result['total_reward'])
        
        # Baseline episode
        baseline_result = run_baseline_episode(RuleBasedBaseline(), skill_level, num_questions_per_episode)
        baseline_accuracies.append(baseline_result['accuracy'])
        
        # Print progress every 10 episodes
        if (episode + 1) % 10 == 0:
            avg_rl_acc = np.mean(rl_accuracies[-10:])
            avg_baseline_acc = np.mean(baseline_accuracies[-10:])
            avg_reward = np.mean(rl_rewards[-10:])
            
            print(f"Episode {episode+1:3d} | RL Acc: {avg_rl_acc:.2f} | Baseline Acc: {avg_baseline_acc:.2f} | "
                  f"Avg Reward: {avg_reward:+.1f} | ε: {rl_agent.epsilon:.3f}")
    
    print("-" * 70)
    
    # Final analysis
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    early_rl_acc = np.mean(rl_accuracies[:10])
    late_rl_acc = np.mean(rl_accuracies[-10:])
    early_baseline_acc = np.mean(baseline_accuracies[:10])
    late_baseline_acc = np.mean(baseline_accuracies[-10:])
    
    print(f"\nRL Agent:")
    print(f"  Early accuracy (eps 1-10):  {early_rl_acc:.2%}")
    print(f"  Late accuracy (eps 41-50):  {late_rl_acc:.2%}")
    print(f"  Improvement:                +{(late_rl_acc - early_rl_acc):.2%}")
    print(f"  Final ε:                    {rl_agent.epsilon:.3f}")
    print(f"  Learning maturity:          {rl_agent.get_learning_maturity()}")
    
    print(f"\nRule-Based Baseline:")
    print(f"  Early accuracy (eps 1-10):  {early_baseline_acc:.2%}")
    print(f"  Late accuracy (eps 41-50):  {late_baseline_acc:.2%}")
    print(f"  Improvement:                +{(late_baseline_acc - early_baseline_acc):.2%}")
    
    print(f"\nComparison:")
    improvement_diff = (late_rl_acc - early_rl_acc) - (late_baseline_acc - early_baseline_acc)
    print(f"  RL learns {improvement_diff:+.2%} better than rule-based baseline")
    
    # Show learned Q-table
    print("\n" + "="*70)
    print("LEARNED Q-TABLE")
    print("="*70)
    print("\nState format: (Mastery, Recent Accuracy)")
    print("Actions: 0=Easy Concept, 1=Med App, 2=Hard Prob, 3=Easy Rev\n")
    
    state_names = [
        "(Low, Poor)", "(Low, Good)",
        "(Med, Poor)", "(Med, Good)",
        "(High, Poor)", "(High, Good)"
    ]
    
    print(f"{'State':<15} {'A0':<8} {'A1':<8} {'A2':<8} {'A3':<8} {'Best'}")
    print("-" * 70)
    
    for i, state_name in enumerate(state_names):
        q_values = rl_agent.q_table[i]
        best_action = np.argmax(q_values)
        best_mark = " ★"
        
        print(f"{state_name:<15} ", end="")
        for j, q_val in enumerate(q_values):
            marker = best_mark if j == best_action else "  "
            print(f"{q_val:>5.2f}{marker} ", end="")
        print(f" A{best_action}")
    
    print("\n" + "="*70)
    print("RL DEMONSTRATION COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
