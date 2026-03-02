from pydantic import BaseModel
from typing import List, Optional
import datetime

class QuestionBase(BaseModel):
    topic_id: int
    question_text: str
    options: List[str]
    correct_answer: str
    difficulty: str
    type: str

class QuestionRead(QuestionBase):
    id: int
    class Config:
        from_attributes = True

class QuestionResponse(BaseModel):
    id: int
    question_text: str
    options: List[str]
    difficulty: str
    type: str

class AnswerSubmission(BaseModel):
    session_id: int
    question_id: int
    selected_answer: str

class QuizStartResult(BaseModel):
    session_id: int
    first_question: QuestionResponse

class AnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    next_question: Optional[QuestionResponse] = None
    game_over: bool = False
    score: int
    total_questions: int

class SessionStats(BaseModel):
    id: int
    topic_name: str
    score: int
    total_questions: int
    created_at: datetime.datetime
    class Config:
        from_attributes = True

class TopicRead(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_quizzes: int
    avg_score: float
    topics_covered: int

class TeacherCreateTopic(BaseModel):
    name: str

class TeacherAnalytics(BaseModel):
    avg_score: float
    total_attempts: int
    student_performance: List[dict] # {username: ..., avg_score: ..., total_attempts: ...}
    topic_performance: List[dict] # {topic_name: ..., avg_score: ..., total_attempts: ...}
    recent_responses: List[dict] # {username: ..., topic: ..., score: ..., total: ..., date: ...}
