from pydantic import BaseModel
from datetime import datetime

class UserSchema(BaseModel):
    username:str
    created_at:datetime=datetime.utcnow()