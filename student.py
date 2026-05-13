from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StudentBase(BaseModel):
    name: str
    department: str
    gpa: float = 0.0
    enrolled_year: int

class StudentCreate(StudentBase):
    user_id: int

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    gpa: Optional[float] = None
    enrolled_year: Optional[int] = None

class StudentResponse(StudentBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True