from pydantic import BaseModel
from typing import List, Tuple, Dict

class RLState(BaseModel):
    mastery_level: int
    recent_accuracy: int

class RLActionParams(BaseModel):
    difficulty: str
    type: str

class QTableData(BaseModel):
    q_table: List[List[float]]
    epsilon: float
    episodes: int
