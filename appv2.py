from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional
from enum import Enum
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select
import os
from dotenv import load_dotenv

load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL, echo=True)

# Enums
class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Status(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

# Models - Student
class StudentBase(SQLModel):
    name: str = Field(index=True)
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

# Models - Todo
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

# Create tables function
def create_db_and_tables():
    print("Creating tables if not exist...")
    SQLModel.metadata.create_all(engine)
    print("✅ Tables created/ensured")

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Connecting to Neon PostgreSQL...")
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"Attempt {attempt}/{max_attempts} to connect to database...")
            create_db_and_tables()
            print("✅ Database setup completed successfully")
            break
        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {e}")
            if attempt == max_attempts:
                print("⚠️  All connection attempts failed. Starting without database...")
    
    yield  # This is where the app runs
    
    # Shutdown (optional cleanup)
    print("Shutting down...")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Student Todo Management System",
    version="1.0.0",
    description="Complete system with Student Management and Todo functionality",
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

# ========== STUDENT ROUTES ==========

@app.get("/")
async def root():
    return {
        "message": "Student Todo Management API",
        "features": {
            "students": {
                "create": "POST /students/",
                "read_all": "GET /students/",
                "read_one": "GET /students/{id}",
                "update": "PUT /students/{id}",
                "delete": "DELETE /students/{id}"
            },
            "todos": {
                "create": "POST /todos/",
                "read_all": "GET /todos/",
                "read_one": "GET /todos/{id}",
                "update": "PUT /todos/{id}",
                "delete": "DELETE /todos/{id}",
                "mark_complete": "PUT /todos/{id}/complete",
                "filter_by_student": "GET /todos/student/{student_id}"
            }
        },
        "docs": "http://localhost:8000/docs"
    }

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
        
        # Also delete associated todos
        todos = session.exec(select(Todo).where(Todo.student_id == student_id)).all()
        for todo in todos:
            session.delete(todo)
        
        session.delete(student)
        session.commit()
        return {"message": "Student and associated todos deleted successfully"}

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
        # Check if student exists
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        todos = session.exec(select(Todo).where(Todo.student_id == student_id)).all()
        return todos

# Print startup message
if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("Student Todo Management System - Neon PostgreSQL")
    print("=" * 60)
    print("Core Features Implemented:")
    print("1. ✅ Add Task (Create todo)")
    print("2. ✅ Delete Task (Remove todo)")
    print("3. ✅ Update Task (Modify todo)")
    print("4. ✅ View Task List (List all todos)")
    print("5. ✅ Mark as Complete (Toggle completion)")
    print("=" * 60)
    print("📖 Swagger UI: http://localhost:8000/docs")
    print("📚 ReDoc: http://localhost:8000/redoc")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)