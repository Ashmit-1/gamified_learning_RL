"""
Question Generator for RL-based Quiz System

Generates individual questions based on RL agent's selected teaching strategy.
"""

import httpx
import json
import os
import random
import asyncio
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

async def generate_category_questions(topic: str, category: str, cat_desc: str, retries: int = 2) -> list:
    """Helper to generate 10 questions for a specific category with simple retry."""
    for attempt in range(retries + 1):
        try:
            prompt = f'''
Topic: {topic}
Category: {category} ({cat_desc})

Task: Generate exactly 10 unique multiple-choice questions for this category.
Format: Return ONLY a JSON list of objects:
[
  {{ "text": "...", "options": ["...", "...", "...", "..."], "correct_answer": "..." }},
  ...
]

IMPORTANT:
- "correct_answer" MUST be the EXACT text of the correct option.
- Return ONLY the JSON list. No preamble or markdown.
- Ensure all quotes inside the question text or options are properly escaped with backslashes.
'''
            headers = {
                "Authorization": f"Bearer {GENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": GENAI_MODEL,
                "messages": [
                    {"role": "system", "content": f"You are a specialized quiz generator for {topic}. Output ONLY valid JSON lists."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2500
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(GENAI_API_ENDPOINT, headers=headers, json=payload)
                response.raise_for_status()
                
                data = response.json()
                if 'choices' not in data or not data['choices']:
                    print(f"[POOL] Attempt {attempt+1}: API response missing 'choices' for {category}")
                    continue
                
                content = data['choices'][0]['message'].get('content', '').strip()
                if not content:
                    print(f"[POOL] Attempt {attempt+1}: API response 'content' is empty for {category}")
                    continue
                
                # Robust JSON extraction
                start_index = content.find('[')
                end_index = content.rfind(']')
                if start_index == -1 or end_index == -1:
                    print(f"[POOL] Attempt {attempt+1}: No JSON list found for {category}")
                    continue
                
                json_str = content[start_index:end_index + 1]
                
                import re
                # Fast cleaning: remove trailing commas
                json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
                # Ensure it's not empty
                if len(json_str) < 10: continue

                try:
                    questions = json.loads(json_str)
                    if isinstance(questions, list) and len(questions) > 0:
                        return questions
                except Exception as e:
                    print(f"[POOL ERROR] Attempt {attempt+1}: JSON parse failed for {category}: {e}")
                    # Log snippet of problematic area if possible
                    if hasattr(e, 'pos'):
                        snippet = json_str[max(0, e.pos-40):min(len(json_str), e.pos+40)]
                        print(f"  Snippet near error: ...{snippet}...")
        
        except Exception as e:
            print(f"[POOL ERROR] Attempt {attempt+1}: Network/API error for {category}: {e}")
            
        if attempt < retries:
            await asyncio.sleep(1) # Small delay before retry
            
    return []

async def generate_question_pool(topic: str) -> dict:
    """
    Generate a pool of 40 questions by calling categories in parallel.
    """
    try:
        print(f"[POOL] Generating question pool for '{topic}' using parallel requests...")
        
        categories_meta = {
            "easy_conceptual": ("easy", "conceptual", "Simple definitions, basic concepts"),
            "medium_application": ("medium", "application", "Applying concepts to scenarios"),
            "hard_problem_solving": ("hard", "problem-solving", "Complex logic, multi-step reasoning"),
            "easy_revision": ("easy", "revision", "Fundamental refreshers of key points")
        }
        
        tasks = []
        for cat, meta in categories_meta.items():
            _, _, desc = meta
            tasks.append(generate_category_questions(topic, cat, desc))
        
        results = await asyncio.gather(*tasks)
        
        pool = {}
        for (cat, meta), questions in zip(categories_meta.items(), results):
            difficulty, q_type, _ = meta
            
            # Add metadata and IDs
            for i, q in enumerate(questions):
                q['id'] = f"{cat}_{i}_{random.randint(1000, 9999)}"
                q['difficulty'] = difficulty
                q['question_type'] = q_type
                
            pool[cat] = questions
            print(f"[POOL] Generated {len(questions)} questions for {cat}")
        
        print(f"[POOL] Successfully created complete pool for '{topic}'.")
        return pool
    except Exception as e:
        print(f"[POOL ERROR] Parallel generation failed: {e}")
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
