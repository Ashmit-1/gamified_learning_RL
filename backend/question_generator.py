"""
Question Generator for RL-based Quiz System

Generates individual questions based on RL agent's selected teaching strategy.
"""

import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

GENAI_API_KEY = os.getenv("GENAI_API_KEY")
GENAI_API_ENDPOINT = os.getenv("GENAI_API_ENDPOINT")
GENAI_MODEL = os.getenv("GENAI_MODEL", "openai/gpt-oss-20b")


async def generate_single_question(
    topic: str,
    difficulty: str,
    question_type: str
) -> dict:
    """
    Generate a single MCQ question using GenAI.
    
    Args:
        topic: The subject topic
        difficulty: "easy", "medium", or "hard"
        question_type: "conceptual", "application", "problem-solving", or "revision"
        
    Returns:
        Dict with question data: {id, text, options, correct_answer}
    """
    prompt = f'''
Generate ONE {difficulty} {question_type} multiple-choice question about: {topic}.

Question difficulty: {difficulty}
Question type: {question_type}

Return ONLY a JSON object with this structure:
{{
  "text": "Question text here?",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "correct_answer": "Option A"
}}

Guidelines:
- {difficulty} questions should be {'basic understanding' if difficulty == 'easy' else 'application-based' if difficulty == 'medium' else 'advanced problem-solving'}
- {question_type} questions should test {'fundamental concepts' if question_type == 'conceptual' else 'practical application' if question_type == 'application' else 'complex scenarios' if question_type == 'problem-solving' else 'previously learned material'}
- Provide exactly 4 options
- Make options plausible but clearly distinguishable
'''

    headers = {
        "Authorization": f"Bearer {GENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GENAI_MODEL,
        "messages": [
            {"role": "system", "content": "You are a quiz generator that outputs ONLY valid JSON. Your response must be a complete, non-truncated JSON object. Ensure all strings are properly closed and the JSON is well-formed."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5, # Reduced temperature for more stable JSON
        "max_tokens": 1000
    }



    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(GENAI_API_ENDPOINT, headers=headers, json=payload)
            
            if response.status_code != 200:
                print(f"[API ERROR] Status: {response.status_code}")
                print(f"[API ERROR] Body: {response.text}")
                response.raise_for_status()

            data = response.json()
            content = data['choices'][0]['message']['content'].strip()
            
            # Robust JSON extraction
            start_index = content.find('{')
            end_index = content.rfind('}')
            if start_index != -1 and end_index != -1:
                content = content[start_index:end_index + 1]
            
            if not content:
                raise ValueError("Empty content returned from AI after filtering")

            try:
                question_data = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"[JSON ERROR] Failed to parse: {content}")
                raise e
            
            # Add metadata
            question_data['id'] = f"q_{difficulty}_{question_type}"
            question_data['difficulty'] = difficulty
            question_data['question_type'] = question_type
            
            return question_data
            
    except Exception as e:
        print(f"Error generating question: {type(e).__name__} - {e}")
        # Return fallback question

        return {
            "id": "fallback",
            "text": f"[Fallback] What is an important concept in {topic}?",
            "options": ["Concept A", "Concept B", "Concept C", "Concept D"],
            "correct_answer": "Concept A",
            "difficulty": difficulty,
            "question_type": question_type
        }
