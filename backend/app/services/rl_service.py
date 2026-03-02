import numpy as np
from sqlalchemy.orm import Session
from backend.app.db.models import UserProgress
from backend.app.services.rl_agent import (
    QLearningAgent, 
    compute_state as agent_compute_state, 
    compute_reward as agent_compute_reward,
    ACTION_TO_PARAMS,
    MASTERY_LOW,
    ACCURACY_POOR
)
from typing import Dict, List, Tuple, Any

class RLService:
    @staticmethod
    def get_user_progress(db: Session, user_id: int, topic_id: int) -> UserProgress:
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id, 
            UserProgress.topic_id == topic_id
        ).first()
        
        if not progress:
            # Create fresh progress with default Q-table (full of 1.0 as per rl_agent.py)
            initial_q_table = np.full((6, 4), 1.0).tolist()
            progress = UserProgress(
                user_id=user_id,
                topic_id=topic_id,
                q_table=initial_q_table,
                epsilon=0.3,
                episodes=0
            )
            db.add(progress)
            db.commit()
            db.refresh(progress)
        return progress

    @staticmethod
    def get_agent(db: Session, user_id: int, topic_id: int) -> Tuple[QLearningAgent, UserProgress]:
        progress = RLService.get_user_progress(db, user_id, topic_id)
        
        agent = QLearningAgent(
            epsilon=progress.epsilon
        )
        agent.q_table = np.array(progress.q_table)
        agent.episodes = progress.episodes
        
        return agent, progress

    @staticmethod
    def save_agent(db: Session, progress: UserProgress, agent: QLearningAgent):
        progress.q_table = agent.q_table.tolist()
        progress.epsilon = agent.epsilon
        progress.episodes = agent.episodes
        db.add(progress)
        db.commit()

    @staticmethod
    def get_action_params(action: int) -> Dict[str, str]:
        difficulty, q_type = ACTION_TO_PARAMS[action]
        return {"difficulty": difficulty, "type": q_type}

    @staticmethod
    def calculate_state(answer_history: List[Dict[str, Any]]) -> Tuple[int, int]:
        # Expects answer_history to be a list of {'correct': bool, 'difficulty': str}
        return agent_compute_state(answer_history)

    @staticmethod
    def calculate_reward(answer_correct: bool, old_state: Tuple[int, int], new_state: Tuple[int, int], action: int) -> float:
        return agent_compute_reward(answer_correct, old_state, new_state, action)
