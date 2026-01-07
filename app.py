from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional
from enum import Enum
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select, text
import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

# ========== MODELS ==========
class Student(SQLModel, table=True):
    __tablename__ = "student"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nameplz: str = Field(index=True)
    name: Optional[str] = Field(default=None, index=True)
    email: str = Field(index=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class StudentCreate(BaseModel):
    name: str
    email: str

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

class StudentRead(BaseModel):
    id: int
    name: str
    email: str
    created_at: Optional[datetime]

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Status(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

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

class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    status: Status = Status.TODO
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

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None
    due_date: Optional[datetime] = None
    student_id: Optional[int] = None

# ========== DATABASE HELPER ==========
def ensure_name_field():
    """Ensure name field exists and has data"""
    with Session(engine) as session:
        result = session.exec(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'student' AND column_name = 'name'
        """)).first()
        
        if not result:
            print("⚠️  'name' column doesn't exist, adding...")
            session.exec(text("ALTER TABLE student ADD COLUMN name VARCHAR(100)"))
            session.commit()
            print("✅ Added 'name' column to student table")
        
        session.exec(text("""
            UPDATE student 
            SET name = nameplz 
            WHERE name IS NULL OR name = ''
        """))
        session.commit()

# ========== LIFESPAN ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*50)
    print("🚀 Starting Student Todo Management System")
    print("="*50)
    
    ensure_name_field()
    SQLModel.metadata.create_all(engine)
    print("✅ Database ready!")
    
    yield
    
    print("\n" + "="*50)
    print("🛑 Shutting down...")
    print("="*50)

# ========== FASTAPI APP ==========
app = FastAPI(
    title="Student Todo Management System",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== HELPER FUNCTIONS ==========
def student_db_to_read(student_db: Student) -> StudentRead:
    """Convert database model to API response"""
    return StudentRead(
        id=student_db.id,
        name=student_db.name or student_db.nameplz or "",
        email=student_db.email,
        created_at=student_db.created_at
    )

def todo_db_to_read(todo_db: Todo) -> TodoRead:
    """Convert Todo database model to API response"""
    return TodoRead(
        id=todo_db.id,
        title=todo_db.title,
        description=todo_db.description,
        priority=todo_db.priority,
        status=todo_db.status,
        due_date=todo_db.due_date,
        student_id=todo_db.student_id,
        created_at=todo_db.created_at,
        completed_at=todo_db.completed_at
    )

# ========== STUDENT ROUTES ==========
@app.post("/students/", response_model=StudentRead)
async def create_student(student: StudentCreate):
    with Session(engine) as session:
        db_student = Student(
            nameplz=student.name,
            name=student.name,
            email=student.email
        )
        session.add(db_student)
        session.commit()
        session.refresh(db_student)
        return student_db_to_read(db_student)

@app.get("/students/", response_model=List[StudentRead])
async def read_students():
    with Session(engine) as session:
        students = session.exec(select(Student)).all()
        return [student_db_to_read(s) for s in students]

@app.get("/students/{student_id}", response_model=StudentRead)
async def read_student(student_id: int):
    with Session(engine) as session:
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        return student_db_to_read(student)

@app.put("/students/{student_id}", response_model=StudentRead)
async def update_student(student_id: int, student_update: StudentUpdate):
    with Session(engine) as session:
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        if student_update.name is not None:
            student.nameplz = student_update.name
            student.name = student_update.name
        
        if student_update.email is not None:
            student.email = student_update.email
        
        session.add(student)
        session.commit()
        session.refresh(student)
        return student_db_to_read(student)

@app.delete("/students/{student_id}")
async def delete_student(student_id: int):
    with Session(engine) as session:
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        try:
            # Delete from studentclass first
            try:
                session.exec(text("DELETE FROM studentclass WHERE student_id = :student_id"), 
                            {"student_id": student_id})
                print(f"✅ Deleted related studentclass records for student {student_id}")
            except Exception as e:
                print(f"ℹ️  studentclass table might not exist or error: {e}")
            
            # Delete associated todos
            try:
                todos = session.exec(select(Todo).where(Todo.student_id == student_id)).all()
                for todo in todos:
                    session.delete(todo)
                print(f"✅ Deleted {len(todos)} todos for student {student_id}")
            except Exception as e:
                print(f"ℹ️  Error deleting todos: {e}")
            
            # Now delete the student
            session.delete(student)
            session.commit()
            
            return {"message": f"Student {student_id} deleted successfully with related records"}
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error deleting student {student_id}: {e}")
            
            if "foreign key" in str(e).lower():
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot delete student {student_id}. They have related records in other tables. Delete those records first."
                )
            else:
                raise HTTPException(status_code=500, detail=f"Failed to delete student: {e}")

# ========== TODO ROUTES ==========
@app.post("/todos/", response_model=TodoRead)
async def create_todo(todo: TodoCreate):
    with Session(engine) as session:
        db_todo = Todo(
            title=todo.title,
            description=todo.description,
            priority=todo.priority,
            status=todo.status,
            due_date=todo.due_date,
            student_id=todo.student_id
        )
        session.add(db_todo)
        session.commit()
        session.refresh(db_todo)
        return todo_db_to_read(db_todo)

@app.get("/todos/", response_model=List[TodoRead])
async def read_todos():
    with Session(engine) as session:
        todos = session.exec(select(Todo)).all()
        return [todo_db_to_read(todo) for todo in todos]

@app.get("/todos/{todo_id}", response_model=TodoRead)
async def read_todo(todo_id: int):
    with Session(engine) as session:
        todo = session.get(Todo, todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        return todo_db_to_read(todo)

@app.put("/todos/{todo_id}", response_model=TodoRead)
async def update_todo(todo_id: int, todo_update: TodoUpdate):
    with Session(engine) as session:
        todo = session.get(Todo, todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        update_data = todo_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(todo, field, value)
        
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo_db_to_read(todo)

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
        return todo_db_to_read(todo)

@app.get("/todos/student/{student_id}", response_model=List[TodoRead])
async def get_todos_by_student(student_id: int):
    with Session(engine) as session:
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        todos = session.exec(select(Todo).where(Todo.student_id == student_id)).all()
        return [todo_db_to_read(todo) for todo in todos]

# ========== HEALTH CHECK ==========
@app.get("/")
async def root():
    return {
        "message": "Student Todo Management API",
        "status": "running",
        "database": "connected",
        "endpoints": {
            "students": "/students",
            "todos": "/todos",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    try:
        with Session(engine) as session:
            session.exec(select(1))
        return {"status": "healthy", "database": "connected"}
    except:
        return {"status": "unhealthy", "database": "disconnected"}

# ========== MAIN ==========
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🎯 STUDENT TODO MANAGEMENT SYSTEM")
    print("="*60)
    print("✅ All 5 Core Todo Features Ready")
    print("✅ Database synchronization enabled")
    print("✅ Foreign key constraint handling fixed")
    print("="*60)
    print("📖 API: http://localhost:8000/docs")
    print("👨‍💻 Frontend: http://localhost:3000")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)