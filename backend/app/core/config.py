import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Adaptive Quiz Platform"
    
    # Database settings
    DB_USER: str = os.getenv("USER", "postgres")
    DB_PASSWORD: str = os.getenv("PASSWORD", "postgres")
    DB_HOST: str = os.getenv("HOST", "localhost")
    DB_PORT: str = os.getenv("PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "quiz_db")
    
    # DATABASE_URL: str = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    DATABASE_URL:str = f"postgresql://postgres.fplsbmkcbzanmudfxvfz:{DB_PASSWORD}@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"
    
    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-it-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 1 week
    
    # Groq settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "llama3-8b-8192")

    class Config:
        case_sensitive = True

settings = Settings()
