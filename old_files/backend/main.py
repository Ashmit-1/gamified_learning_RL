import os
import json
import signal
import sys
from pathlib import Path
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

# Graceful shutdown handler
def graceful_shutdown(signum, frame):
    print("Gracefully shutting down...")
    # Save all active sessions
    for session_id, session in sessions.items():
        try:
            session.agent.save_policy(session.topic, save_dir="q_tables")
            print(f"Saved policy for session {session_id}")
        except Exception as e:
            print(f"Error saving policy for session {session_id}: {e}")
    sys.exit(0)

# Register signals for graceful shutdown
try:
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)
except AttributeError:
    # Windows doesn't support these signals
    pass

# Global reference to sessions for graceful shutdown
global_sessions = {}

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


async def ensure_pool_healthy(topic: str, pool: dict, min_threshold: int = 5):
    """Check if any category in the pool is low and refill if needed."""
    needs_refill = False
    categories = ["easy_conceptual", "medium_application", "hard_problem_solving", "easy_revision"]
    
    for cat in categories:
        if len(pool.get(cat, [])) < min_threshold:
            needs_refill = True
            break
            
    if needs_refill:
        print(f"[POOL] Category low for '{topic}'. Refilling...")
        try:
            # Generate a new pool of 40 and merge
            new_questions = await generate_question_pool(topic)
            for cat in categories:
                # Only refill categories that are below threshold
                if len(pool.get(cat, [])) < min_threshold:
                    pool[cat].extend(new_questions.get(cat, []))
            save_pool(topic, pool, save_dir="pools")
            print(f"[POOL] Refilled and saved for '{topic}'.")
        except Exception as e:
            print(f"[POOL ERROR] Auto-refill failed: {e}")
            # Re-raise exception to be handled by caller
            raise

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
        agent.load_policy(topic, save_dir="q_tables")
        agents[topic] = agent
    else:
        agent = agents[topic]
    
    # Try to load existing question pool
    pool = load_pool(topic, save_dir="pools")
    
    if not pool:
        try:
            print(f"[START] Generating new question pool for topic: {topic}")
            pool = await generate_question_pool(topic)
            save_pool(topic, pool, save_dir="pools")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate question pool: {str(e)}")
    
    # Proactively check if pool needs more questions
    try:
        await ensure_pool_healthy(topic, pool, min_threshold=5)
    except Exception as e:
        print(f"[START] Warning: Pool health check failed: {e}")
        # Continue anyway as we have some questions
    
    # Create new session with the pool
    session = StudentSession(topic, agent, pool)
    sessions[session.session_id] = session
    
    # Get first question from the pool
    try:
        result = session.get_next_question()
    except IndexError:
        print(f"[START] Pool exhausted, regenerating for topic: {topic}")
        try:
            pool = await generate_question_pool(topic)
            save_pool(topic, pool, save_dir="pools")
            session.pool = pool
            result = session.get_next_question()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to regenerate question pool: {str(e)}")
        
    question = result["question"]
    action_name = result["action_name"]
    
    try:
        save_pool(topic, session.pool, save_dir="pools")
    except Exception as e:
        print(f"[START] Warning: Failed to save pool state: {e}")
    
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
    correct = request.answer == current_question["correct_answer"]
    
    update_info = session.process_answer(
        correct,
        current_question["difficulty"],
        current_question["text"]
    )
    
    # Quiz is complete only when game is actually over (player dies or kills all zombies)
    # We'll rely on frontend to indicate when game is actually over
    quiz_complete = False
    next_question = None
    summary = None
    
    # Always get next question since game continues until actual end
    try:
        result = session.get_next_question()
        next_question = result["question"]
        save_pool(session.topic, session.pool, save_dir="pools")
        await ensure_pool_healthy(session.topic, session.pool, min_threshold=5)
    except Exception as e:
        print(f"Error getting next question: {e}")
        # Try to refill pool and get question again
        try:
            await ensure_pool_healthy(session.topic, session.pool, min_threshold=5)
            result = session.get_next_question()
            next_question = result["question"]
            save_pool(session.topic, session.pool, save_dir="pools")
        except Exception as e2:
            print(f"Critical error getting next question: {e2}")
            raise HTTPException(status_code=500, detail=f"Failed to get next question: {str(e2)}")
    
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
    """Force end a session and save Q-table."""
    if session_id in sessions:
        session = sessions[session_id]
        try:
            save_success = session.agent.save_policy(session.topic, save_dir="q_tables")
            if save_success:
                del sessions[session_id]
                return {"message": "Quiz session ended and policy saved."}
            else:
                return {"message": "Quiz session ended but policy save failed."}
        except Exception as e:
            print(f"Error saving policy on session end: {e}")
            # Still remove session to clean up memory
            del sessions[session_id]
            return {"message": f"Quiz session ended but policy save failed: {str(e)}"}
    return {"message": "Session not found."}

@app.post("/game-over")
async def game_over(session_id: str, game_result: str):
    """
    Called when game actually ends (player dies or kills all zombies).
    Saves the Q-table and removes session.
    """
    if session_id in sessions:
        session = sessions[session_id]
        try:
            # Save the final Q-table
            print(f"[GAME-OVER] Saving Q-table for topic: {session.topic}")
            print(f"[GAME-OVER] Current working directory: {os.getcwd()}")
            save_success = session.agent.save_policy(session.topic, save_dir="q_tables")
            if save_success:
                print(f"[GAME-OVER] Successfully saved Q-table for topic: {session.topic}")
                # Verify the file exists
                qtable_path = Path("q_tables") / f"{session.topic.lower().replace(' ', '_')}.json"
                if qtable_path.exists():
                    print(f"[GAME-OVER] Verified Q-table file exists at: {qtable_path.absolute()}")
                else:
                    print(f"[GAME-OVER] Warning: Q-table file not found at expected location: {qtable_path.absolute()}")
            else:
                print(f"[GAME-OVER] Failed to save Q-table for topic: {session.topic}")
            
            session.agent.episodes += 1  # Increment episode count
            
            # Also save a checkpoint for backup
            session.agent.save_checkpoint(session.topic, session_id)
            
            # Get session summary
            summary = session.get_session_summary()
            
            # Remove session
            del sessions[session_id]
            
            if save_success:
                return {
                    "message": "Game ended and policy saved.", 
                    "summary": summary
                }
            else:
                return {
                    "message": "Game ended but policy save failed.",
                    "summary": summary
                }
        except Exception as e:
            print(f"Error saving policy on game over: {e}")
            # Still remove session to clean up memory
            del sessions[session_id]
            return {"message": f"Game ended but policy save failed: {str(e)}"}
    return {"message": "Session not found."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
