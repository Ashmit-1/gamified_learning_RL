from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.app.db.session import get_db
from backend.app.db.models import Topic, QuizSession, User
from backend.app.schemas.quiz import TopicRead, TeacherAnalytics, TeacherCreateTopic
from backend.app.services.analytics_service import AnalyticsService
from backend.app.routers.auth import get_current_user

router = APIRouter(prefix="/teacher", tags=["teacher"])

@router.post("/create-test", response_model=TopicRead)
def create_test(topic_in: TeacherCreateTopic, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can access this")
    
    db_topic = db.query(Topic).filter(Topic.name == topic_in.name).first()
    if db_topic:
        raise HTTPException(status_code=400, detail="Topic already exists")
    
    topic = Topic(name=topic_in.name, creator_id=current_user.id)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic

@router.get("/topics", response_model=List[TopicRead])
def get_topics(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can access this")
    return db.query(Topic).all()

@router.get("/analytics", response_model=TeacherAnalytics)
def get_analytics(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can access this")
    return AnalyticsService.get_teacher_analytics(db)
