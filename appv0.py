# app.py - Use your actual Neon connection string
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlmodel import Session, SQLModel, Field, create_engine, select, Column
from typing import Optional, List
from datetime import datetime
from sqlalchemy import text, String, DateTime
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
import json
import time

# ========== DATABASE SETUP ==========
# USE YOUR EXACT NEON CONNECTION STRING
DATABASE_URL = "postgresql://neondb_owner:npg_rcbta9i6JCwR@ep-broad-field-adscc1ik-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"

print(f"Connecting to Neon PostgreSQL...")

# Create engine with retry logic
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,  # Check connection before using
    pool_recycle=300,    # Recycle connections every 5 minutes
    pool_size=5,         # Maintain 5 connections
    max_overflow=10,     # Allow up to 10 overflow connections
)

# ========== MODELS ==========
class Student(SQLModel, table=True):
    __tablename__ = "student"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nameplz: str = Field(sa_column=Column("nameplz", String(255)))
    
    email: Optional[str] = Field(
        default=None, 
        sa_column=Column("email", String(255), nullable=True)
    )
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column("created_at", DateTime, nullable=True)
    )

class StudentClass(SQLModel, table=True):
    __tablename__ = "studentclass"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id")
    class_name: str = Field(sa_column=Column(String(255)))
    class_code: str = Field(sa_column=Column(String(50)))
    semester: str = Field(sa_column=Column(String(50)))
    status: str = Field(default="pending", sa_column=Column(String(20)))
    priority: str = Field(default="medium", sa_column=Column(String(20)))
    description: Optional[str] = Field(
        default=None, 
        sa_column=Column(String(500), nullable=True)
    )
    due_date: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True)
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime)
    )

# ========== FASTAPI APP ==========
app = FastAPI(
    title="Student Todo App",
    description="API for managing students and their classes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ========== CUSTOM OPENAPI ==========
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Student Todo App",
        version="1.0.0",
        description="API for managing students and their classes",
        routes=app.routes,
    )
    
    openapi_schema["servers"] = [
        {"url": "http://localhost:8000", "description": "Local server"},
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ========== CORS ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== CREATE TABLES ==========
def setup_database(force_recreate: bool = False):
    """Setup database with retry logic and optional recreation"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries} to connect to database...")
            
            with Session(engine) as session:
                if force_recreate:
                    print("Dropping all tables...")
                    SQLModel.metadata.drop_all(engine)
                    print("All tables dropped.")
                    SQLModel.metadata.create_all(engine) # Create all tables after dropping
                    print("✅ All tables created.")
                else:
                    # In normal operation, ensure tables exist.
                    # create_all only creates tables that don't exist.
                    SQLModel.metadata.create_all(engine) 
                    print("✅ Tables ensured to exist (created if not present).")
                
            print("✅ Database setup completed successfully")
            return
            
        except Exception as e:
            print(f"⚠️ Database connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Waiting {retry_delay} seconds before retry...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("❌ All database connection attempts failed")
                print("💡 Tip: Check your Neon dashboard to ensure the database is active")

# ========== SESSION WITH RETRY ==========
def get_session():
    """Get database session with retry logic"""
    max_retries = 2
    
    for attempt in range(max_retries):
        try:
            with Session(engine) as session:
                yield session
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise HTTPException(
                    status_code=500,
                    detail=f"Database connection failed after {max_retries} attempts: {str(e)}"
                )
            time.sleep(1)

# ========== SCHEMAS ==========
class StudentCreate(BaseModel):
    nameplz: str
    email: EmailStr
    
    @field_validator('nameplz')
    def validate_nameplz(cls, v):
        return v
    
    model_config = ConfigDict(from_attributes=True)

class StudentRead(BaseModel):
    id: int
    nameplz: str
    email: Optional[str] = None
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class StudentUpdate(BaseModel):
    nameplz: Optional[str] = None
    email: Optional[EmailStr] = None

    model_config = ConfigDict(from_attributes=True)

class StudentClassCreate(BaseModel):
    student_id: int
    class_name: str
    class_code: str
    semester: str
    status: Optional[str] = "pending"
    priority: Optional[str] = "medium"
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class StudentClassRead(BaseModel):
    id: int
    student_id: int
    class_name: str
    class_code: str
    semester: str
    status: str
    priority: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ClassUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

# ========== STARTUP ==========
@app.on_event("startup")
def on_startup():
    setup_database(force_recreate=False)

# ========== ENDPOINTS ==========
@app.get("/")
async def root():
    return {
        "message": "Student Todo App API",
        "database": "Neon PostgreSQL",
        "docs": "/docs",
        "redoc": "/redoc",
        "connection": "Using your Neon connection string"
    }

@app.get("/health")
async def health_check(session: Session = Depends(get_session)):
    try:
        session.exec(text("SELECT 1"))
        return {"status": "healthy", "database": "Neon PostgreSQL"}
    except Exception as e:
        return {"status": "unhealthy", "database": "error", "error": str(e)}

# ========== STUDENT ENDPOINTS ==========
@app.post("/students/", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
async def create_student(student: StudentCreate, session: Session = Depends(get_session)):
    try:
        existing = session.exec(
            select(Student).where(Student.email == student.email)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        
        db_student = Student(
            nameplz=student.nameplz, # Use nameplz here
            email=student.email
        )
        
        session.add(db_student)
        session.commit()
        session.refresh(db_student)
        
        return db_student
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/students/", response_model=List[StudentRead])
async def read_students(session: Session = Depends(get_session)):
    try:
        students = session.exec(select(Student)).all()
        return students
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/students/{student_id}", response_model=StudentRead)
async def read_student(student_id: int, session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    print(f"DEBUG: Attempted to retrieve student with ID {student_id}. Result: {student}") # Added for debugging
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.patch("/students/{student_id}", response_model=StudentRead)
async def update_student(
    student_id: int,
    student_update: StudentUpdate,
    session: Session = Depends(get_session)
):
    db_student = session.get(Student, student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    update_data = student_update.model_dump(exclude_unset=True)
    if "nameplz" in update_data: # Update nameplz if present
        db_student.nameplz = update_data["nameplz"]
    if "email" in update_data:
        db_student.email = update_data["email"]

    session.add(db_student)
    session.commit()
    session.refresh(db_student)
    return db_student

@app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(student_id: int, session: Session = Depends(get_session)):
    # Also delete related classes
    class_statement = select(StudentClass).where(StudentClass.student_id == student_id)
    classes_to_delete = session.exec(class_statement).all()
    for cls in classes_to_delete:
        session.delete(cls)

    db_student = session.get(Student, student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")

    session.delete(db_student)
    session.commit()
    return

@app.post("/classes/", response_model=StudentClassRead, status_code=status.HTTP_201_CREATED)
async def create_class(class_data: StudentClassCreate, session: Session = Depends(get_session)):
    try:
        student = session.get(Student, class_data.student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        db_class = StudentClass(**class_data.model_dump())
        session.add(db_class)
        session.commit()
        session.refresh(db_class)
        return db_class
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/classes/", response_model=List[StudentClassRead])
async def read_classes(session: Session = Depends(get_session)):
    try:
        classes = session.exec(select(StudentClass)).all()
        return classes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.patch("/classes/{class_id}", response_model=StudentClassRead)
async def update_class(
    class_id: int,
    update_data: ClassUpdate,
    session: Session = Depends(get_session)
):
    try:
        class_item = session.get(StudentClass, class_id)
        if not class_item:
            raise HTTPException(status_code=404, detail="Class not found")
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(class_item, field, value)
            
        session.add(class_item)
        session.commit()
        session.refresh(class_item)
        
        return class_item
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(class_id: int, session: Session = Depends(get_session)):
    class_item = session.get(StudentClass, class_id)
    if not class_item:
        raise HTTPException(status_code=404, detail="Class not found")
    
    session.delete(class_item)
    session.commit()
    return

@app.get("/dashboard")
async def dashboard(session: Session = Depends(get_session)):
    try:
        total_students = session.exec(select(Student)).all()
        total_classes = session.exec(select(StudentClass)).all()
        
        pending = len([c for c in total_classes if c.status == "pending"])
        in_progress = len([c for c in total_classes if c.status == "in-progress"])
        completed = len([c for c in total_classes if c.status == "completed"])
        
        return {
            "total_students": len(total_students),
            "total_classes": len(total_classes),
            "by_status": {
                "pending": pending,
                "in_progress": in_progress,
                "completed": completed
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ========== RUN APP ==========
if __name__ == "__main__":
    print("\n" + "="*50)
    print("Student Todo App - Neon PostgreSQL")
    print("="*50)
    print("Using your actual Neon connection string")
    print("📖 Swagger UI: http://localhost:8000/docs")
    print("📚 ReDoc: http://localhost:8000/redoc")
    print("📄 OpenAPI: http://localhost:8000/openapi.json")
    print("="*50 + "\n")
    
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)