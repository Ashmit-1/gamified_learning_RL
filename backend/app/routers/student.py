from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.app.db.session import get_db
from backend.app.db.models import Topic, QuizSession
from backend.app.schemas.quiz import (
    TopicRead, 
    QuizStartResult, 
    AnswerSubmission, 
    AnswerResponse, 
    DashboardStats, 
    SessionStats,
    TeacherCreateTopic
)
from backend.app.services.quiz_service import QuizService
from backend.app.services.analytics_service import AnalyticsService
from backend.app.routers.auth import get_current_user

router = APIRouter(prefix="/student", tags=["student"])

@router.get("/topics", response_model=List[TopicRead])
def get_topics(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can access this")
    return db.query(Topic).all()

@router.post("/create-topic", response_model=TopicRead)
def create_topic(topic_in: TeacherCreateTopic, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Students can create any topic they want to be quizzed on."""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can access this")
    existing = db.query(Topic).filter(Topic.name.ilike(topic_in.name)).first()
    if existing:
        return existing
    topic = Topic(name=topic_in.name)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic

@router.post("/start-quiz", response_model=QuizStartResult)
def start_quiz(topic_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can access this")
    return QuizService.start_quiz(db, current_user.id, topic_id)

@router.post("/submit-answer", response_model=AnswerResponse)
def submit_answer(submission: AnswerSubmission, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can access this")
    return QuizService.submit_answer(db, current_user.id, submission)

@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can access this")
    return AnalyticsService.get_student_dashboard(db, current_user.id)

@router.get("/history", response_model=List[SessionStats])
def get_history(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can access this")
    return AnalyticsService.get_student_history(db, current_user.id)

@router.get("/profile", response_model=Dict[str, Any])
def get_profile(current_user = Depends(get_current_user)):
    return {"username": current_user.username, "role": current_user.role}
