import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import httpx
from dotenv import load_dotenv

# Import RL components
from rl_agent import QLearningAgent
from session_manager import StudentSession
from question_generator import generate_question_pool, load_pool, save_pool

load_dotenv()

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (per topic)
# Key: session_id, Value: StudentSession instance
sessions: Dict[str, StudentSession] = {}

# RL agents per topic
# Key: topic, Value: QLearningAgent instance
agents: Dict[str, QLearningAgent] = {}


# Request/Response Models
class StartQuizRequest(BaseModel):
    topic: str

class StartQuizResponse(BaseModel):
    session_id: str
    topic: str
    question: Dict
    message: str

class SubmitAnswerRequest(BaseModel):
    session_id: str
    answer: str
    question_id: str

class SubmitAnswerResponse(BaseModel):
    correct: bool
    reward: float
    q_update: Dict
    next_question: Optional[Dict]
    quiz_complete: bool
    summary: Optional[Dict]


@app.post("/start-quiz", response_model=StartQuizResponse)
async def start_quiz(request: StartQuizRequest):
    """
    Start a new RL-based quiz session.
    Creates or loads a Q-learning agent for the topic.
    """
    topic = request.topic.strip()
    
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty")
    
    # Get or create RL agent for this topic
    if topic not in agents:
        agent = QLearningAgent()
        # Try to load existing policy
        agent.load_policy(topic, save_dir="q_tables")
        agents[topic] = agent
    else:
        agent = agents[topic]
    
    # Try to load existing question pool
    pool = load_pool(topic, save_dir="pools")
    
    if not pool:
        # Generate new pool if none exists
        try:
            pool = await generate_question_pool(topic)
            save_pool(topic, pool, save_dir="pools")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate question pool: {str(e)}")
    
    # Create new session with the pool
    session = StudentSession(topic, agent, pool)
    sessions[session.session_id] = session
    
    # Get first question from the pool
    result = session.get_next_question()
    question = result["question"]
    action_name = result["action_name"]
    
    return {
        "session_id": session.session_id,
        "topic": topic,
        "question": question,
        "message": f"Quiz started! Learning with strategy: {action_name}"
    }


@app.post("/submit-answer", response_model=SubmitAnswerResponse)
async def submit_answer(request: SubmitAnswerRequest):
    """
    Submit an answer and get the next question.
    Updates Q-table based on student performance.
    """
    session_id = request.session_id
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    current_question = session.current_question
    
    # Check if answer is correct
    correct = request.answer == current_question["correct_answer"]
    
    # Process answer and update RL agent
    update_info = session.process_answer(
        correct,
        current_question["difficulty"],
        current_question["text"]
    )
    
    # Check if quiz should end (e.g., after 10 questions)
    quiz_complete = session.question_count >= 10
    
    next_question = None
    summary = None
    
    if quiz_complete:
        # Save Q-table
        session.agent.save_policy(session.topic, save_dir="q_tables")
        session.agent.episodes += 1
        
        summary = session.get_session_summary()
        
        print(f"\n{'='*60}")
        print(f"[SESSION] Quiz completed!")
        print(f"[SESSION] Accuracy: {summary['accuracy']*100:.1f}%")
        print(f"[SESSION] Final ε: {summary['epsilon']:.3f}")
        print(f"[SESSION] Maturity: {summary['learning_maturity']}")
        print(f"{'='*60}\n")
    else:
        # Get next question from the pool
        result = session.get_next_question()
        next_question = result["question"]
    
    return {
        "correct": correct,
        "reward": update_info["reward"],
        "q_update": {
            "old_q": update_info["old_q_value"],
            "new_q": update_info["new_q_value"]
        },
        "next_question": next_question,
        "quiz_complete": quiz_complete,
        "summary": summary
    }


@app.post("/end-quiz")
async def end_quiz(session_id: str):
    """Manually end a quiz session and save progress."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    session.agent.save_policy(session.topic, save_dir="q_tables")
    
    summary = session.get_session_summary()
    
    # Clean up session
    del sessions[session_id]
    
    return {"message": "Quiz ended and progress saved", "summary": summary}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
