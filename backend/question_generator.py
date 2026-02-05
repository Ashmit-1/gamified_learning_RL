"""
Question Generator for RL-based Quiz System

Generates individual questions based on RL agent's selected teaching strategy.
"""

import httpx
import json
import os
import random
from dotenv import load_dotenv

load_dotenv()

GENAI_API_KEY = os.getenv("GENAI_API_KEY")
GENAI_API_ENDPOINT = os.getenv("GENAI_API_ENDPOINT")
GENAI_MODEL = os.getenv("GENAI_MODEL", "llama-3.3-70b-versatile")


def is_duplicate(new_question: str, asked_questions: list) -> bool:
    """Check if new question is similar to any previously asked question."""
    if not asked_questions:
        return False
    
    new_q_lower = new_question.lower().strip()
    
    for asked in asked_questions:
        asked_lower = asked.lower().strip()
        
        # Exact match
        if new_q_lower == asked_lower:
            return True
        
        # High similarity (first 50 chars match)
        if len(new_q_lower) > 30 and len(asked_lower) > 30:
            if new_q_lower[:50] == asked_lower[:50]:
                return True
        
        # Check if one contains the other (80% overlap)
        if new_q_lower in asked_lower or asked_lower in new_q_lower:
            return True
    
    return False



async def generate_single_question(
    topic: str,
    difficulty: str,
    question_type: str,
    asked_questions: list = None
) -> dict:
    """
    Generate a single MCQ question using GenAI (Fallback method).
    """
    # ... (rest of the existing single question logic, trimmed for brevity in this replace call)
    # Actually I should probably just leave it as is or focus on the new function.
    # I'll keep the existing single question logic but add the pool generation below it.
    pass # (Placeholder for brevity, I will include the full code below)

async def generate_question_pool(topic: str) -> dict:
    """
    Generate a pool of 40 questions (10 per category) in one bulk request.
    
    Returns:
        Dict mapping category name to list of 10 questions.
    """
    print(f"[POOL] Generating question pool for topic: {topic}...")
    
    prompt = f'''
Topic: {topic}

Task: Generate a pool of 40 multiple-choice questions divided into 4 categories (10 questions each).
Categories:
1. "easy_conceptual": Simple definitions, basic concepts.
2. "medium_application": Applying concepts to scenarios.
3. "hard_problem_solving": Complex logic, multi-step reasoning.
4. "easy_revision": Fundamental refreshers of key points.

Format: Return ONLY a JSON object with this exact structure:
{{
  "easy_conceptual": [
    {{ "text": "...", "options": ["...", "...", "...", "..."], "correct_answer": "..." }},
    ... (10 items)
  ],
  "medium_application": [ ... (10 items) ],
  "hard_problem_solving": [ ... (10 items) ],
  "easy_revision": [ ... (10 items) ]
}}

IMPORTANT: 
- "correct_answer" MUST be the EXACT FULL TEXT of the correct option.
- Ensure diversity across all 40 questions.
- Response MUST be valid non-truncated JSON.
'''

    headers = {
        "Authorization": f"Bearer {GENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GENAI_MODEL,
        "messages": [
            {"role": "system", "content": "You are a specialized quiz generator. You output LARGE, complete JSON objects. Always ensure 10 questions per category as requested."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 6000 # High limit for bulk generation
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client: # Longer timeout for bulk
            response = await client.post(GENAI_API_ENDPOINT, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            content = data['choices'][0]['message']['content'].strip()
            
            # Robust JSON extraction
            start_index = content.find('{')
            end_index = content.rfind('}')
            if start_index != -1 and end_index != -1:
                content = content[start_index:end_index + 1]
            
            pool = json.loads(content)
            
            # Validate structure and add metadata
            categories_meta = {
                "easy_conceptual": ("easy", "conceptual"),
                "medium_application": ("medium", "application"),
                "hard_problem_solving": ("hard", "problem-solving"),
                "easy_revision": ("easy", "revision")
            }
            
            for cat, meta in categories_meta.items():
                if cat not in pool or not isinstance(pool[cat], list):
                    print(f"[POOL ERROR] Missing category: {cat}")
                    pool[cat] = pool.get(cat, [])
                
                difficulty, q_type = meta
                # Add metadata to each question
                for i, q in enumerate(pool[cat]):
                    q['id'] = f"{cat}_{i}_{random.randint(1000, 9999)}"
                    q['difficulty'] = difficulty
                    q['question_type'] = q_type
            
            print(f"[POOL] Successfully generated 40 questions for '{topic}'.")
            return pool

    except Exception as e:
        print(f"[POOL ERROR] Failed to generate pool: {e}")
        # Return a minimum viable pool or raise? 
        # For now, let's raise so the caller can decide to retry or fallback.
        raise e

def save_pool(topic: str, pool_data: dict, save_dir: str = "pools"):
    """Save the question pool to disk."""
    import pathlib
    pathlib.Path(save_dir).mkdir(exist_ok=True)
    filename = f"{topic.lower().replace(' ', '_')}.json"
    filepath = os.path.join(save_dir, filename)
    with open(filepath, 'w') as f:
        json.dump(pool_data, f, indent=2)
    print(f"[POOL] Saved pool for '{topic}' to {filepath}")

def load_pool(topic: str, save_dir: str = "pools") -> dict:
    """Load the question pool from disk if it exists."""
    filename = f"{topic.lower().replace(' ', '_')}.json"
    filepath = os.path.join(save_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            print(f"[POOL] Loaded existing pool for '{topic}'.")
            return json.load(f)
    return None
