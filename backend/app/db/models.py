from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, DateTime, Boolean
from sqlalchemy.orm import relationship
import datetime
from db.session import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False) # "student" or "teacher"
    
    progress = relationship("UserProgress", back_populates="user")
    sessions = relationship("QuizSession", back_populates="user")
    created_topics = relationship("Topic", back_populates="creator")

class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True) # None for global/seeded topics
    
    creator = relationship("User", back_populates="created_topics")
    questions = relationship("Question", back_populates="topic")
    progress = relationship("UserProgress", back_populates="topic")
    sessions = relationship("QuizSession", back_populates="topic")

class UserProgress(Base):
    __tablename__ = "user_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"))
    q_table = Column(JSON, nullable=False) # JSON representation of the 6x4 numpy array
    epsilon = Column(Float, default=0.3)
    episodes = Column(Integer, default=0)
    
    user = relationship("User", back_populates="progress")
    topic = relationship("Topic", back_populates="progress")

class QuizSession(Base):
    __tablename__ = "quiz_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"))
    score = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="sessions")
    topic = relationship("Topic", back_populates="sessions")
    responses = relationship("Response", back_populates="session")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"))
    question_text = Column(String, nullable=False)
    options = Column(JSON, nullable=False) # List of 4 options
    correct_answer = Column(String, nullable=False)
    difficulty = Column(String, nullable=False) # easy, medium, hard
    type = Column(String, nullable=False) # conceptual, application, problem-solving
    
    topic = relationship("Topic", back_populates="questions")
    responses = relationship("Response", back_populates="question")

class Response(Base):
    __tablename__ = "responses"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("quiz_sessions.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    selected_answer = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    
    session = relationship("QuizSession", back_populates="responses")
    question = relationship("Question", back_populates="responses")
