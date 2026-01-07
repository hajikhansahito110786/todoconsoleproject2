from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Student Schemas
class StudentBase(BaseModel):
    name: str
    email: EmailStr

class StudentCreate(StudentBase):
    pass

class StudentRead(StudentBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Student Class/Todo Schemas
class StudentClassBase(BaseModel):
    class_name: str
    class_code: str
    semester: str
    status: Optional[str] = "pending"
    priority: Optional[str] = "medium"
    description: Optional[str] = None
    due_date: Optional[datetime] = None

class StudentClassCreate(StudentClassBase):
    student_id: int

class StudentClassUpdate(BaseModel):
    class_name: Optional[str] = None
    class_code: Optional[str] = None
    semester: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None

class StudentClassRead(StudentClassBase):
    id: int
    student_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Combined schemas
class StudentWithClasses(StudentRead):
    classes: list[StudentClassRead] = []
    
    class Config:
        from_attributes = True