from sqlmodel import Field, SQLModel, create_engine, Session, select
from typing import Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Debug: Print the database URL to see if it's loaded
database_url = os.getenv("DATABASE_URL")
print(f"Database URL loaded: {database_url}")  # Debug line

if not database_url:
    raise ValueError("DATABASE_URL environment variable is not set!")

# Student Model
class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
# Student Class/Todo Model
class StudentClass(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id")
    class_name: str
    class_code: str
    semester: str
    status: str = Field(default="pending")  # pending, in-progress, completed
    priority: str = Field(default="medium")  # low, medium, high
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
# Create engine
try:
    engine = create_engine(database_url, echo=True)
    print("Database engine created successfully!")
except Exception as e:
    print(f"Error creating database engine: {e}")
    raise

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    print("Database tables created successfully!")

def get_session():
    with Session(engine) as session:
        yield session