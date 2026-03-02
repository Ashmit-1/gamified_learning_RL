import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from core.config import settings
from typing import Dict, Any

class LLMService:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name=settings.MODEL_NAME,
            temperature=0.7
        )
        self.parser = JsonOutputParser()
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert educational content creator. 
Create high-quality MCQ questions based on the provided parameters. 
Your output must be a valid JSON object with the following structure:
{{
  "question": str,
  "options": [4 unique options],
  "correct_answer": str (must match one of the options),
  "difficulty": str (matches input difficulty),
  "type": str (matches input type)
}}
Do not include any other text in your response, only the JSON."""),
            ("user", "Create a {type} question for the topic '{topic}' with {difficulty} difficulty level. The student has a mastery level of {mastery}.")
        ])

    def generate_question(self, topic: str, difficulty: str, q_type: str, mastery: str) -> Dict[str, Any]:
        chain = self.prompt | self.llm | self.parser
        
        try:
            result = chain.invoke({
                "topic": topic,
                "difficulty": difficulty,
                "type": q_type,
                "mastery": mastery
            })
            return result
        except Exception as e:
            print(f"Error generating question: {e}")
            # Fallback (simple mock for demo if LLM fails)
            return {
                "question": f"What is 2+2? (Fallback for topic {topic})",
                "options": ["3", "4", "5", "6"],
                "correct_answer": "4",
                "difficulty": difficulty,
                "type": q_type
            }

llm_service = LLMService()
