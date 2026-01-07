from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional
from enum import Enum
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ========== DATABASE SETUP ==========
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL is not set in .env file")
    print("💡 Please check your .env file")
    exit(1)

# Clean up the URL (just in case)
DATABASE_URL = DATABASE_URL.strip()
print(f"✅ Using database: {DATABASE_URL[:50]}...")

# Create engine
try:
    engine = create_engine(DATABASE_URL, echo=True)
    print("✅ Database engine created successfully!")
except Exception as e:
    print(f"❌ ERROR creating database engine: {e}")
    exit(1)

# ========== MODELS ==========
class StudentBase(SQLModel):
    nameplz: str = Field(index=True)
    email: str = Field(index=True)

class Student(StudentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class StudentCreate(StudentBase):
    pass

class StudentRead(StudentBase):
    id: int
    created_at: Optional[datetime]

class StudentUpdate(SQLModel):
    name: Optional[str] = None
    email: Optional[str] = None

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Status(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class TodoBase(SQLModel):
    title: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    priority: Priority = Field(default=Priority.MEDIUM)
    status: Status = Field(default=Status.TODO)
    due_date: Optional[datetime] = Field(default=None)
    student_id: Optional[int] = Field(default=None, foreign_key="student.id")

class Todo(TodoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

class TodoCreate(TodoBase):
    pass

class TodoRead(TodoBase):
    id: int
    created_at: Optional[datetime]
    completed_at: Optional[datetime]

class TodoUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None
    due_date: Optional[datetime] = None
    student_id: Optional[int] = None
    completed_at: Optional[datetime] = None

# ========== DATABASE FUNCTIONS ==========
def create_db_and_tables():
    """Create all database tables if they don't exist"""
    print("📊 Creating database tables...")
    SQLModel.metadata.create_all(engine)
    print("✅ Tables created successfully!")

# ========== LIFESPAN ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    print("\n" + "="*50)
    print("🚀 Starting Student Todo Management System")
    print("="*50)
    
    # Create tables on startup
    create_db_and_tables()
    
    yield  # App runs here
    
    print("\n" + "="*50)
    print("🛑 Shutting down...")
    print("="*50)

# ========== FASTAPI APP ==========
app = FastAPI(
    title="Student Todo Management System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== HEALTH CHECK ==========
@app.get("/")
async def root():
    return {
        "message": "Student Todo Management API",
        "status": "running",
        "endpoints": {
            "students": "/students",
            "todos": "/todos",
            "docs": "/docs",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        with Session(engine) as session:
            session.exec(select(1))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

# ========== STUDENT ROUTES ==========
@app.post("/students/", response_model=StudentRead)
async def create_student(student: StudentCreate):
    with Session(engine) as session:
        db_student = Student.model_validate(student)
        session.add(db_student)
        session.commit()
        session.refresh(db_student)
        return db_student

@app.get("/students/", response_model=List[StudentRead])
async def read_students():
    with Session(engine) as session:
        students = session.exec(select(Student)).all()
        return students

@app.get("/students/{student_id}", response_model=StudentRead)
async def read_student(student_id: int):
    with Session(engine) as session:
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        return student

@app.put("/students/{student_id}", response_model=StudentRead)
async def update_student(student_id: int, student_update: StudentUpdate):
    with Session(engine) as session:
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        update_data = student_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(student, field, value)
        
        session.add(student)
        session.commit()
        session.refresh(student)
        return student

@app.delete("/students/{student_id}")
async def delete_student(student_id: int):
    with Session(engine) as session:
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        session.delete(student)
        session.commit()
        return {"message": "Student deleted successfully"}

# ========== TODO ROUTES ==========
@app.post("/todos/", response_model=TodoRead)
async def create_todo(todo: TodoCreate):
    with Session(engine) as session:
        db_todo = Todo.model_validate(todo)
        session.add(db_todo)
        session.commit()
        session.refresh(db_todo)
        return db_todo

@app.get("/todos/", response_model=List[TodoRead])
async def read_todos():
    with Session(engine) as session:
        todos = session.exec(select(Todo)).all()
        return todos

@app.get("/todos/{todo_id}", response_model=TodoRead)
async def read_todo(todo_id: int):
    with Session(engine) as session:
        todo = session.get(Todo, todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        return todo

@app.put("/todos/{todo_id}", response_model=TodoRead)
async def update_todo(todo_id: int, todo_update: TodoUpdate):
    with Session(engine) as session:
        todo = session.get(Todo, todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        update_data = todo_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(todo, field, value)
        
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int):
    with Session(engine) as session:
        todo = session.get(Todo, todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        session.delete(todo)
        session.commit()
        return {"message": "Todo deleted successfully"}

@app.put("/todos/{todo_id}/complete", response_model=TodoRead)
async def mark_todo_complete(todo_id: int):
    with Session(engine) as session:
        todo = session.get(Todo, todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        todo.status = Status.DONE
        todo.completed_at = datetime.utcnow()
        
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo

@app.get("/todos/student/{student_id}", response_model=List[TodoRead])
async def get_todos_by_student(student_id: int):
    with Session(engine) as session:
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        todos = session.exec(select(Todo).where(Todo.student_id == student_id)).all()
        return todos

# ========== MAIN ==========
if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🎯 STUDENT TODO MANAGEMENT SYSTEM")
    print("="*60)
    print("✅ All 5 Core Todo Features:")
    print("   1. Add Task")
    print("   2. Delete Task")
    print("   3. Update Task")
    print("   4. View Task List")
    print("   5. Mark as Complete")
    print("="*60)
    print("📖 API Documentation: http://localhost:8000/docs")
    print("👨‍💻 Frontend: http://localhost:3000")
    print("🏥 Health Check: http://localhost:8000/health")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)