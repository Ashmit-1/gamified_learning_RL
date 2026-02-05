import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import httpx
from dotenv import load_dotenv

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

GENAI_API_KEY = os.getenv("GENAI_API_KEY")
GENAI_API_ENDPOINT = os.getenv("GENAI_API_ENDPOINT")
GENAI_MODEL = os.getenv("GENAI_MODEL", "llama-3.3-70b-versatile")

class QuizRequest(BaseModel):
    topic: str

class Question(BaseModel):
    id: int
    text: str
    options: List[str]
    correct_answer: str

class QuizResponse(BaseModel):
    questions: List[Question]

@app.post("/generate-quiz", response_model=QuizResponse)
async def generate_quiz(request: QuizRequest):
    if not GENAI_API_KEY or not GENAI_API_ENDPOINT:
        raise HTTPException(status_code=500, detail="GenAI API configuration missing.")

    prompt = f'''
    Generate a quiz with 10 multiple-choice questions about the topic: {request.topic}.
    Return the response ONLY as a JSON object with the following structure:
    {{
      "questions": [
        {{
          "id": 1,
          "text": "Question text here?",
          "options": ["Option A", "Option B", "Option C", "Option D"],
          "correct_answer": "Option A"
        }},
        ...
      ]
    }}
    Ensure there are exactly 10 questions.
    '''

    headers = {
        "Authorization": f"Bearer {GENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    # This structure works for OpenAI-compatible APIs. 
    # Adjust payload if using a different provider (like Gemini or Anthropic).
    payload = {
        "model": GENAI_MODEL,
        "messages": [
            {"role": "system", "content": "You are a quiz generator that outputs ONLY valid JSON. Your response must be a complete JSON object including all 10 questions requested. Do not truncate your output."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
        "response_format": {"type": "json_object"}
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(GENAI_API_ENDPOINT, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Extract content from the first choice
            content = data['choices'][0]['message']['content'].strip()
            # print(f"AI Response Raw: {content}") # Debugging
            
            # Robust JSON extraction: find the first '{' and last '}'
            try:
                start_index = content.find('{')
                end_index = content.rfind('}')
                if start_index != -1 and end_index != -1:
                    content = content[start_index:end_index + 1]
                
                quiz_data = json.loads(content)
                return quiz_data
            except json.JSONDecodeError as je:
                print(f"JSON Decode Error: {je}")
                # Try to fix common issues like trailing commas if necessary, 
                # but for now, let's just raise the error with more context
                raise HTTPException(status_code=500, detail=f"AI returned invalid JSON: {str(je)}")
            
    except Exception as e:
        print(f"Error generating quiz: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
