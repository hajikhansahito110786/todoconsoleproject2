from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional
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

# Models
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
    nameplz: Optional[str] = None
    email: Optional[str] = None

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
    title="Student Todo App - Neon PostgreSQL",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/")
async def root():
    return {
        "message": "Student Todo API",
        "docs": "http://localhost:8000/docs",
        "students_endpoint": "http://localhost:8000/students/"
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
        
        # Update only provided fields
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

# Print startup message
if __name__ == "__main__":
    import uvicorn
    print("==================================================")
    print("Student Todo App - Neon PostgreSQL")
    print("==================================================")
    print("Using your actual Neon connection string")
    print("📖 Swagger UI: http://localhost:8000/docs")
    print("📚 ReDoc: http://localhost:8000/redoc")
    print("📄 OpenAPI: http://localhost:8000/openapi.json")
    print("==================================================")
    uvicorn.run(app, host="0.0.0.0", port=8000)