from sqlalchemy.orm import Session
from db.models import QuizSession, Question, Response, Topic, User, UserProgress
from schemas.quiz import QuestionRead, AnswerSubmission, QuizStartResult, AnswerResponse
from services.rl_service import RLService
from services.llm_service import llm_service
from services.rl_agent import ACTION_TO_PARAMS, ACTION_NAMES
from typing import List, Dict, Any, Optional

class QuizService:
    @staticmethod
    def start_quiz(db: Session, user_id: int, topic_id: int):
        # 1. Create session
        session = QuizSession(user_id=user_id, topic_id=topic_id)
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # 2. Get RL agent
        agent, progress = RLService.get_agent(db, user_id, topic_id)
        
        # 3. Get initial state (no history)
        state = RLService.calculate_state([])
        
        # 4. Select initial action
        action = agent.select_action(state)
        params = ACTION_TO_PARAMS[action]
        difficulty, q_type = params
        
        # 5. Generate first question
        topic = db.query(Topic).get(topic_id)
        mastery = agent.get_learning_maturity()
        
        q_data = llm_service.generate_question(topic.name, difficulty, q_type, mastery)
        
        # 6. Store question in DB
        question = Question(
            topic_id=topic_id,
            question_text=q_data["question"],
            options=q_data["options"],
            correct_answer=q_data["correct_answer"],
            difficulty=q_data["difficulty"],
            type=q_data["type"]
        )
        db.add(question)
        db.commit()
        db.refresh(question)
        
        return {
            "session_id": session.id,
            "first_question": {
                "id": question.id,
                "question_text": question.question_text,
                "options": question.options,
                "difficulty": question.difficulty,
                "type": question.type
            }
        }

    @staticmethod
    def submit_answer(db: Session, user_id: int, submission: AnswerSubmission):
        session = db.query(QuizSession).get(submission.session_id)
        if not session or session.user_id != user_id:
            raise Exception("Unauthorized session access")
        
        question = db.query(Question).get(submission.question_id)
        is_correct = submission.selected_answer.strip().lower() == question.correct_answer.strip().lower()
        
        # Store response
        response = Response(
            session_id=session.id,
            question_id=question.id,
            selected_answer=submission.selected_answer,
            is_correct=is_correct
        )
        db.add(response)
        
        # Update session score
        if is_correct:
            session.score += 1
        session.total_questions += 1
        db.commit()
        
        # RL UPDATE
        topic_id = session.topic_id
        agent, progress = RLService.get_agent(db, user_id, topic_id)
        
        # History before this response
        responses_history = db.query(Response).join(Question).filter(
            Response.session_id == session.id,
            Response.id < response.id # All previous responses
        ).all()
        
        prev_history = [
            {"correct": r.is_correct, "difficulty": r.question.difficulty} 
            for r in responses_history
        ]
        
        # Old state s
        old_state = RLService.calculate_state(prev_history)
        
        # Action a was used for current question
        # We can map current question back to action index
        # This is a bit tricky if we have duplicates but for simplicity:
        action = QuizService._params_to_action(question.difficulty, question.type)
        
        # Current history (including this response)
        current_history = prev_history + [{"correct": is_correct, "difficulty": question.difficulty}]
        
        # New state s'
        new_state = RLService.calculate_state(current_history)
        
        # Reward r
        reward = RLService.calculate_reward(is_correct, old_state, new_state, action)
        
        # Q-learning Update
        agent.update(old_state, action, reward, new_state)
        agent.decay_epsilon()
        
        # Save Q-table
        RLService.save_agent(db, progress, agent)
        
        # Check if game over (e.g. 5 questions per session?)
        # Let's say session lasts 10 questions
        game_over = session.total_questions >= 10
        
        next_question = None
        if not game_over:
            # Select next action based on s'
            next_action = agent.select_action(new_state)
            next_params = ACTION_TO_PARAMS[next_action]
            
            topic = db.query(Topic).get(topic_id)
            mastery = agent.get_learning_maturity()
            
            q_data = llm_service.generate_question(topic.name, next_params[0], next_params[1], mastery)
            
            # Store question
            next_question_model = Question(
                topic_id=topic_id,
                question_text=q_data["question"],
                options=q_data["options"],
                correct_answer=q_data["correct_answer"],
                difficulty=q_data["difficulty"],
                type=q_data["type"]
            )
            db.add(next_question_model)
            db.commit()
            db.refresh(next_question_model)
            
            next_question = {
                "id": next_question_model.id,
                "question_text": next_question_model.question_text,
                "options": next_question_model.options,
                "difficulty": next_question_model.difficulty,
                "type": next_question_model.type
            }
            
        return {
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "next_question": next_question,
            "game_over": game_over,
            "score": session.score,
            "total_questions": session.total_questions
        }

    @staticmethod
    def _params_to_action(difficulty: str, q_type: str) -> int:
        for action, params in ACTION_TO_PARAMS.items():
            if params[0] == difficulty.lower() and params[1] == q_type.lower():
                return action
        # Default fallback
        return 0
