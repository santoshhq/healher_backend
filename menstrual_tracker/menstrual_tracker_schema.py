from pydantic import BaseModel
from typing import List, Optional

class Cycle(BaseModel):
    userId: str
    startDate: str
    endDate: Optional[str] = None
    cycleLength: int
    periodLength: int

class DailyLog(BaseModel):
    userId: str
    date: str
    flow: str
    symptoms: List[str]
    mood: str
    sleep: float
    water: float
    exercise: bool