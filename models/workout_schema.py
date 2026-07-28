from pydantic import BaseModel
from datetime import datetime

class WorkoutSchema(BaseModel):
    user_id: str
    exercise_name: str
    reps: int = 0
    sets: int = 0
    time: float = 0
    created_at: datetime = datetime.utcnow()