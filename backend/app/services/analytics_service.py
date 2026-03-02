from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.db.models import QuizSession, User, Topic, Response, Question
from typing import List, Dict, Any

class AnalyticsService:
    @staticmethod
    def get_student_dashboard(db: Session, user_id: int):
        total_quizzes = db.query(QuizSession).filter(QuizSession.user_id == user_id).count()
        avg_score = db.query(func.avg(QuizSession.score)).filter(QuizSession.user_id == user_id).scalar() or 0
        topics_covered = db.query(Topic).join(QuizSession).filter(QuizSession.user_id == user_id).distinct().count()
        
        return {
            "total_quizzes": total_quizzes,
            "avg_score": float(avg_score),
            "topics_covered": topics_covered
        }

    @staticmethod
    def get_student_history(db: Session, user_id: int):
        # Only return sessions where questions were actually answered
        sessions = db.query(QuizSession).filter(
            QuizSession.user_id == user_id,
            QuizSession.total_questions > 0
        ).order_by(QuizSession.created_at.desc()).all()
        history = []
        for s in sessions:
            topic = db.query(Topic).get(s.topic_id)
            history.append({
                "id": s.id,
                "topic_name": topic.name,
                "score": s.score,
                "total_questions": s.total_questions,
                "created_at": s.created_at
            })
        return history

    @staticmethod
    def get_teacher_analytics(db: Session):
        # Using 1.0 * score ensures floating point context
        total_attempts = db.query(QuizSession).filter(QuizSession.total_questions > 0).count()
        avg_score_raw = db.query(func.avg(100.0 * QuizSession.score / QuizSession.total_questions))\
                          .filter(QuizSession.total_questions > 0).scalar() or 0
        avg_score = float(avg_score_raw)
        
        # Student performance: list of {username: ..., avg_score: ...}
        performance = db.query(
            User.username, 
            func.avg(100.0 * QuizSession.score / QuizSession.total_questions).label('avg_score'),
            func.count(QuizSession.id).label('total_attempts')
        ).join(QuizSession, QuizSession.user_id == User.id)\
         .filter(QuizSession.total_questions > 0)\
         .group_by(User.id, User.username)\
         .all()
        
        student_results = [{"username": p.username, "avg_score": float(p.avg_score), "total_attempts": p.total_attempts} for p in performance]
        
        # Topic-wise performance
        topic_performance = db.query(
            Topic.name,
            func.avg(100.0 * QuizSession.score / QuizSession.total_questions).label('avg_score'),
            func.count(QuizSession.id).label('total_attempts')
        ).join(QuizSession, QuizSession.topic_id == Topic.id)\
         .filter(QuizSession.total_questions > 0)\
         .group_by(Topic.id, Topic.name)\
         .all()
         
        topic_results = [{"topic_name": t.name, "avg_score": float(t.avg_score), "total_attempts": t.total_attempts} for t in topic_performance]
        
        # Recent activity log
        recent_sessions = db.query(
            User.username,
            Topic.name.label('topic_name'),
            QuizSession.score,
            QuizSession.total_questions,
            QuizSession.created_at
        ).join(QuizSession, QuizSession.user_id == User.id)\
         .join(Topic, QuizSession.topic_id == Topic.id)\
         .filter(QuizSession.total_questions > 0)\
         .order_by(QuizSession.created_at.desc())\
         .limit(20)\
         .all()
         
        recent_logs = []
        for s in recent_sessions:
            recent_logs.append({
                "username": s.username,
                "topic": s.topic_name,
                "score": s.score,
                "total": s.total_questions,
                "date": s.created_at.isoformat()
            })
        
        return {
            "total_attempts": total_attempts,
            "avg_score": avg_score,
            "student_performance": student_results,
            "topic_performance": topic_results,
            "recent_responses": recent_logs
        }
