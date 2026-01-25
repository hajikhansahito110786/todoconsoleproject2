from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select, text
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import secrets

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file.")

engine = create_engine(DATABASE_URL, echo=True)
sessions: Dict[str, dict] = {}

# ========== MODELS ==========
class User(SQLModel, table=True):
    __tablename__ = "usertable"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    password: str

class Student(SQLModel, table=True):
    __tablename__ = "student"  # Table name is singular
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Todo(SQLModel, table=True):
    __tablename__ = "todo"
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: Optional[str] = None
    priority: str = Field(default="medium")
    status: str = Field(default="todo")
    due_date: Optional[datetime] = None
    student_id: Optional[int] = Field(default=None, foreign_key="student.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

# ========== REQUEST MODELS ==========
class LoginRequest(BaseModel):
    email: str
    password: str

class StudentCreate(BaseModel):
    name: str
    email: str

class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    status: str = "todo"
    due_date: Optional[datetime] = None
    student_id: Optional[int] = None

# ========== LIFESPAN ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*50)
    print("🚀 Student Management System Starting...")
    print("="*50)
    
    try:
        with Session(engine) as session:
            # Test connection first
            session.execute(text("SELECT 1"))
            print("✅ Connected to database")
            
            # Create tables if they don't exist (skip foreign key issues)
            print("🔄 Creating tables if needed...")
            
            # Create student table
            try:
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS student (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR NOT NULL,
                        email VARCHAR UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                print("✅ Created/verified student table")
            except Exception as e:
                print(f"⚠️ Student table error: {e}")
            
            # Create todo table (without foreign key to avoid issues)
            try:
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS todo (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR NOT NULL,
                        description TEXT,
                        priority VARCHAR DEFAULT 'medium',
                        status VARCHAR DEFAULT 'todo',
                        due_date TIMESTAMP,
                        student_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP
                    )
                """))
                print("✅ Created/verified todo table")
            except Exception as e:
                print(f"⚠️ Todo table error: {e}")
            
            session.commit()
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        print("⚠️ Continuing with existing tables...")
    
    print("="*50)
    print("✅ Ready! Endpoints:")
    print("   POST /login     - User login")
    print("   POST /students/ - Create student")  # Plural endpoint
    print("   GET  /students/ - List students")   # Plural endpoint
    print("   POST /todos/    - Create todo")
    print("   GET  /todos/    - List todos")
    print("="*50)
    
    yield
    
    print("\n" + "="*50)
    print("🛑 Shutdown complete")
    print("="*50)

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== SESSION MANAGEMENT ==========
def create_session(user_data: dict) -> str:
    token = secrets.token_hex(16)
    sessions[token] = {
        **user_data,
        "expires_at": datetime.now() + timedelta(minutes=5)
    }
    return token

def get_session(token: str) -> Optional[dict]:
    if token not in sessions:
        return None
    
    session_data = sessions[token]
    if datetime.now() > session_data["expires_at"]:
        del sessions[token]
        return None
    
    return session_data

# ========== AUTH ROUTES ==========
@app.post("/login")
async def login(request: LoginRequest, response: Response):
    print(f"📨 Login attempt: {request.email}")
    
    with Session(engine) as session:
        # Find user
        query = text("SELECT id, email, password FROM usertable WHERE email = :email")
        result = session.execute(query, {"email": request.email})
        user = result.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        user_id, user_email, user_password = user
        
        if user_password != request.password:
            raise HTTPException(status_code=401, detail="Incorrect password")
        
        # Create session
        session_token = create_session({
            "user_id": user_id,
            "email": user_email
        })
        
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=300,
            samesite="lax"
        )
        
        return {
            "success": True,
            "message": "Login successful",
            "session_token": session_token,
            "user": {
                "id": user_id,
                "email": user_email
            }
        }

# ========== STUDENT ROUTES (using plural endpoints) ==========
@app.post("/students/")  # Keep plural endpoint for frontend compatibility
async def create_student(request: StudentCreate):
    """Create a new student"""
    print(f"📝 Creating student: {request.name} ({request.email})")
    
    with Session(engine) as session:
        # Check if email already exists
        query = text("SELECT email FROM student WHERE email = :email")  # Table is singular
        result = session.execute(query, {"email": request.email})
        existing = result.fetchone()
        
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create student using raw SQL
        insert_query = text("""
            INSERT INTO student (name, email, created_at)  
            VALUES (:name, :email, :created_at)
            RETURNING id, name, email, created_at
        """)
        
        result = session.execute(insert_query, {
            "name": request.name,
            "email": request.email,
            "created_at": datetime.utcnow()
        })
        student = result.fetchone()
        session.commit()
        
        return {
            "id": student[0],
            "name": student[1],
            "email": student[2],
            "created_at": student[3]
        }

@app.get("/students/")  # Keep plural endpoint for frontend compatibility
async def list_students():
    """List all students"""
    with Session(engine) as session:
        query = text("SELECT id, name, email, created_at FROM student ORDER BY created_at DESC")  # Table is singular
        result = session.execute(query)
        students = result.fetchall()
        
        return [
            {
                "id": s[0],
                "name": s[1],
                "email": s[2],
                "created_at": s[3]
            }
            for s in students
        ]

# ========== TODO ROUTES ==========
@app.post("/todos/")
async def create_todo(request: TodoCreate):
    """Create a new todo"""
    print(f"📝 Creating todo: {request.title}")
    
    with Session(engine) as session:
        # Create todo using raw SQL
        insert_query = text("""
            INSERT INTO todo (title, description, priority, status, due_date, student_id, created_at)
            VALUES (:title, :description, :priority, :status, :due_date, :student_id, :created_at)
            RETURNING id, title, description, priority, status, due_date, student_id, created_at
        """)
        
        result = session.execute(insert_query, {
            "title": request.title,
            "description": request.description,
            "priority": request.priority,
            "status": request.status,
            "due_date": request.due_date,
            "student_id": request.student_id,
            "created_at": datetime.utcnow()
        })
        todo = result.fetchone()
        session.commit()
        
        return {
            "id": todo[0],
            "title": todo[1],
            "description": todo[2],
            "priority": todo[3],
            "status": todo[4],
            "due_date": todo[5],
            "student_id": todo[6],
            "created_at": todo[7]
        }

@app.get("/todos/")
async def list_todos():
    """List all todos"""
    with Session(engine) as session:
        query = text("""
            SELECT id, title, description, priority, status, due_date, student_id, created_at, completed_at
            FROM todo 
            ORDER BY created_at DESC
        """)
        result = session.execute(query)
        todo = result.fetchall()
        
        return [
            {
                "id": t[0],
                "title": t[1],
                "description": t[2],
                "priority": t[3],
                "status": t[4],
                "due_date": t[5],
                "student_id": t[6],
                "created_at": t[7],
                "completed_at": t[8]
            }
            for t in todo
        ]

# ========== UTILITY ROUTES ==========
@app.get("/")
async def root():
    return {
        "message": "Student Management API",
        "endpoints": {
            "auth": "POST /login",
            "students": {
                "create": "POST /students/",   # Plural
                "list": "GET /students/"       # Plural
            },
            "todos": {
                "create": "POST /todos/",
                "list": "GET /todos/"
            }
        }
    }

@app.get("/health")
async def health():
    try:
        with Session(engine) as session:
            session.execute(text("SELECT 1"))
            return {"status": "healthy", "database": "connected"}
    except:
        return {"status": "unhealthy", "database": "disconnected"}

@app.get("/test")
async def test():
    return {"message": "Backend is running!", "time": datetime.now().isoformat()}

@app.get("/check/{email}")
async def check(email: str):
    with Session(engine) as session:
        query = text("SELECT email FROM usertable WHERE email = :email")
        result = session.execute(query, {"email": email})
        exists = result.fetchone() is not None
        return {"exists": exists, "email": email}

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🎯 STUDENT MANAGEMENT SYSTEM")
    print("="*60)
    print("🌐 Backend: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("👤 Login: POST /login")
    print("👥 Students: POST /students/, GET /students/")  # Plural
    print("✅ Todos: POST /todos/, GET /todos/")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)