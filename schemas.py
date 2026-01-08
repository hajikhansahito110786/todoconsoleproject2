from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
from models import Priority, Status # Import enums from models.py

# Student Schemas
class StudentCreate(BaseModel):
    name: str
    email: EmailStr

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None # Use EmailStr for consistency

class StudentRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True) # Address Pydantic v2 warning

# Todo Schemas
class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    status: Status = Status.TODO
    due_date: Optional[datetime] = None
    student_id: Optional[int] = None

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None
    due_date: Optional[datetime] = None
    student_id: Optional[int] = None

class TodoRead(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: Priority
    status: Status
    due_date: Optional[datetime]
    student_id: Optional[int]
    created_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True) # Address Pydantic v2 warning
