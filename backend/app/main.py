from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.db.session import engine, Base, SessionLocal
from backend.app.db.models import Topic
from backend.app.routers import auth, student, teacher
import uvicorn

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Adaptive Quiz Platform")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(student.router)
app.include_router(teacher.router)

@app.on_event("startup")
def startup_event():
    # Seed some initial topics if they don't exist
    db = SessionLocal()
    if db.query(Topic).count() == 0:
        topics = ["Mathematics", "Computer Science", "Physics", "Chemistry"]
        for t in topics:
            db.add(Topic(name=t))
        db.commit()
    db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to AI Adaptive Quiz Backend"}

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
