# models.py - Update with custom validators
from sqlmodel import Field, SQLModel, create_engine, Session
from typing import Optional, Any
from datetime import datetime
from enum import Enum
import os
from dotenv import load_dotenv
from pydantic import validator

load_dotenv()

database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL environment variable is not set!")

# Enums that accept both cases
class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    
    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive lookups"""
        if isinstance(value, str):
            for member in cls:
                if member.value == value.lower():
                    return member
        return None

class Status(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    
    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive lookups"""
        if isinstance(value, str):
            value_lower = value.lower()
            # Handle different formats
            if value_lower in ['todo', 'todos']:
                return cls.TODO
            elif value_lower in ['in_progress', 'inprogress', 'progress']:
                return cls.IN_PROGRESS
            elif value_lower in ['done', 'completed']:
                return cls.DONE
        return None

# Unified Student Model
class Student(SQLModel, table=True):
    __tablename__ = "student"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(index=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

# Unified Todo Model with case handling
class Todo(SQLModel, table=True):
    __tablename__ = "todo"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    priority: str = Field(default="medium")  # Changed from Priority enum to string
    status: str = Field(default="todo")      # Changed from Status enum to string
    due_date: Optional[datetime] = Field(default=None)
    student_id: Optional[int] = Field(default=None, foreign_key="student.id")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    
    # Validators to normalize case
    @validator('priority', pre=True)
    def normalize_priority(cls, v):
        if v is None:
            return "medium"
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower in ['low', 'medium', 'high']:
                return v_lower
            # Try to map common variations
            if v_lower == 'med':
                return 'medium'
            if v_lower == 'hi':
                return 'high'
        return "medium"  # Default
    
    @validator('status', pre=True)
    def normalize_status(cls, v):
        if v is None:
            return "todo"
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower in ['todo', 'in_progress', 'done']:
                return v_lower
            # Try to map common variations
            if v_lower in ['todos', 'pending']:
                return 'todo'
            if v_lower in ['inprogress', 'progress', 'working']:
                return 'in_progress'
            if v_lower in ['completed', 'finished']:
                return 'done'
        return "todo"  # Default

# Create engine
try:
    engine = create_engine(database_url, echo=True)
except Exception as e:
    print(f"Error creating database engine: {e}")
    raise

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session