from sqlmodel import Field, SQLModel, create_engine, Session
from typing import Optional
from datetime import datetime
from enum import Enum
import os
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL environment variable is not set!")

# Enums from app.py
class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Status(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

# Unified Student Model (without nameplz)
class Student(SQLModel, table=True):
    __tablename__ = "student"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(index=True) # Should probably be unique, but following app.py for now
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

# Unified Todo Model
class Todo(SQLModel, table=True):
    __tablename__ = "todo"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    priority: Priority = Field(default=Priority.MEDIUM)
    status: Status = Field(default=Status.TODO)
    due_date: Optional[datetime] = Field(default=None)
    student_id: Optional[int] = Field(default=None, foreign_key="student.id")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    
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
