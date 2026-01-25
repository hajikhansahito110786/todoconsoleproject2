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

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
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
            
            # Create tables if they don't exist
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
            
            # Create todo table
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
    print("   POST /login            - User login")
    print("   GET  /students/        - List all students")
    print("   POST /students/        - Create student")
    print("   GET  /students/{id}    - Get single student")
    print("   PUT  /students/{id}    - Update student")
    print("   DELETE /students/{id}  - Delete student")
    print("   GET  /todos/           - List all todos")
    print("   POST /todos/           - Create todo")
    print("   GET  /todos/{id}       - Get single todo")
    print("   PUT  /todos/{id}       - Update todo")
    print("   DELETE /todos/{id}     - Delete todo")
    print("="*50)
    
    yield
    
    print("\n" + "="*50)
    print("🛑 Shutdown complete")
    print("="*50)

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Added port 3001 for Next.js
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== SESSION MANAGEMENT ==========
def create_session(user_data: dict) -> str:
    token = secrets.token_hex(16)
    sessions[token] = {
        **user_data,
        "expires_at": datetime.now() + timedelta(minutes=30)  # Increased to 30 minutes
    }
    return token

def get_session(token: str) -> Optional[dict]:
    if token not in sessions:
        return None
    
    session_data = sessions[token]
    if datetime.now() > session_data["expires_at"]:
        del sessions[token]
        return None
    
    # Refresh session
    session_data["expires_at"] = datetime.now() + timedelta(minutes=30)
    return session_data

# ========== MIDDLEWARE FOR AUTH ==========
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Skip auth for login and public endpoints
    public_paths = ["/login", "/", "/health", "/test", "/check", "/docs", "/openapi.json"]
    
    if request.url.path in public_paths or request.url.path.startswith("/docs"):
        return await call_next(request)
    
    # Check session token
    session_token = request.cookies.get("session_token")
    if not session_token:
        return Response(
            content='{"detail": "Not authenticated"}',
            status_code=401,
            media_type="application/json"
        )
    
    session_data = get_session(session_token)
    if not session_data:
        return Response(
            content='{"detail": "Session expired"}',
            status_code=401,
            media_type="application/json"
        )
    
    # Add user info to request state
    request.state.user = session_data
    return await call_next(request)

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
            max_age=1800,  # 30 minutes
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

@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie("session_token")
    return {"success": True, "message": "Logged out"}

@app.get("/me")
async def get_current_user(request: Request):
    """Get current logged in user info"""
    return {
        "user": request.state.user,
        "authenticated": True
    }

# ========== STUDENT ROUTES ==========
@app.post("/students/")
async def create_student(request: StudentCreate):
    """Create a new student"""
    print(f"📝 Creating student: {request.name} ({request.email})")
    
    with Session(engine) as session:
        # Check if email already exists
        query = text("SELECT email FROM student WHERE email = :email")
        result = session.execute(query, {"email": request.email})
        existing = result.fetchone()
        
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create student
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

@app.get("/students/")
async def list_students():
    """List all students"""
    with Session(engine) as session:
        query = text("""
            SELECT id, name, email, created_at 
            FROM student 
            ORDER BY created_at DESC
        """)
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

@app.get("/students/{student_id}")
async def get_student(student_id: int):
    """Get a single student by ID"""
    with Session(engine) as session:
        query = text("""
            SELECT id, name, email, created_at
            FROM student 
            WHERE id = :student_id
        """)
        result = session.execute(query, {"student_id": student_id})
        student = result.fetchone()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        return {
            "id": student[0],
            "name": student[1],
            "email": student[2],
            "created_at": student[3]
        }

@app.put("/students/{student_id}")
async def update_student(student_id: int, request: StudentCreate):
    """Update a student"""
    with Session(engine) as session:
        # Check if student exists
        check_query = text("SELECT id FROM student WHERE id = :student_id")
        result = session.execute(check_query, {"student_id": student_id})
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Check if email is already taken by another student
        email_query = text("SELECT id FROM student WHERE email = :email AND id != :student_id")
        email_result = session.execute(email_query, {"email": request.email, "student_id": student_id})
        if email_result.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered by another student")
        
        # Update student
        update_query = text("""
            UPDATE student 
            SET name = :name, email = :email 
            WHERE id = :student_id
            RETURNING id, name, email, created_at
        """)
        
        result = session.execute(update_query, {
            "student_id": student_id,
            "name": request.name,
            "email": request.email
        })
        student = result.fetchone()
        session.commit()
        
        return {
            "id": student[0],
            "name": student[1],
            "email": student[2],
            "created_at": student[3]
        }

@app.delete("/students/{student_id}")
async def delete_student(student_id: int):
    """Delete a student"""
    with Session(engine) as session:
        # Check if student exists
        check_query = text("SELECT id FROM student WHERE id = :student_id")
        result = session.execute(check_query, {"student_id": student_id})
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Student not found")
        
        # First, update todos to remove student_id reference
        update_todos_query = text("UPDATE todo SET student_id = NULL WHERE student_id = :student_id")
        session.execute(update_todos_query, {"student_id": student_id})
        
        # Delete the student
        delete_query = text("DELETE FROM student WHERE id = :student_id")
        session.execute(delete_query, {"student_id": student_id})
        session.commit()
        
        return {"success": True, "message": f"Student {student_id} deleted successfully"}

# ========== TODO ROUTES ==========
@app.post("/todos/")
async def create_todo(request: TodoCreate):
    """Create a new todo"""
    print(f"📝 Creating todo: {request.title}")
    
    with Session(engine) as session:
        # If student_id is provided, verify student exists
        if request.student_id:
            student_query = text("SELECT id FROM student WHERE id = :student_id")
            student_result = session.execute(student_query, {"student_id": request.student_id})
            if not student_result.fetchone():
                raise HTTPException(status_code=400, detail="Student not found")
        
        # Create todo
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
async def list_todos(student_id: Optional[int] = None):
    """List all todos, optionally filtered by student_id"""
    with Session(engine) as session:
        if student_id:
            query = text("""
                SELECT t.id, t.title, t.description, t.priority, t.status, 
                       t.due_date, t.student_id, t.created_at, t.completed_at,
                       s.name as student_name, s.email as student_email
                FROM todo t
                LEFT JOIN student s ON t.student_id = s.id
                WHERE t.student_id = :student_id
                ORDER BY t.created_at DESC
            """)
            params = {"student_id": student_id}
        else:
            query = text("""
                SELECT t.id, t.title, t.description, t.priority, t.status, 
                       t.due_date, t.student_id, t.created_at, t.completed_at,
                       s.name as student_name, s.email as student_email
                FROM todo t
                LEFT JOIN student s ON t.student_id = s.id
                ORDER BY t.created_at DESC
            """)
            params = {}
        
        result = session.execute(query, params)
        todos = result.fetchall()
        
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
                "completed_at": t[8],
                "student_name": t[9] if len(t) > 9 else None,
                "student_email": t[10] if len(t) > 10 else None
            }
            for t in todos
        ]

@app.get("/todos/{todo_id}")
async def get_todo(todo_id: int):
    """Get a single todo by ID"""
    with Session(engine) as session:
        query = text("""
            SELECT t.id, t.title, t.description, t.priority, t.status, 
                   t.due_date, t.student_id, t.created_at, t.completed_at,
                   s.name as student_name, s.email as student_email
            FROM todo t
            LEFT JOIN student s ON t.student_id = s.id
            WHERE t.id = :todo_id
        """)
        result = session.execute(query, {"todo_id": todo_id})
        todo = result.fetchone()
        
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        return {
            "id": todo[0],
            "title": todo[1],
            "description": todo[2],
            "priority": todo[3],
            "status": todo[4],
            "due_date": todo[5],
            "student_id": todo[6],
            "created_at": todo[7],
            "completed_at": todo[8],
            "student_name": todo[9] if len(todo) > 9 else None,
            "student_email": todo[10] if len(todo) > 10 else None
        }

@app.put("/todos/{todo_id}")
async def update_todo(todo_id: int, request: TodoUpdate):
    """Update a todo"""
    with Session(engine) as session:
        # First check if todo exists
        check_query = text("SELECT id FROM todo WHERE id = :todo_id")
        result = session.execute(check_query, {"todo_id": todo_id})
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Todo not found")
        
        # If student_id is provided, verify student exists
        if request.student_id is not None:
            if request.student_id == 0:  # Allow 0 or null to clear student
                request.student_id = None
            elif request.student_id:
                student_query = text("SELECT id FROM student WHERE id = :student_id")
                student_result = session.execute(student_query, {"student_id": request.student_id})
                if not student_result.fetchone():
                    raise HTTPException(status_code=400, detail="Student not found")
        
        # Build update query dynamically based on provided fields
        update_fields = []
        params = {"todo_id": todo_id}
        
        if request.title is not None:
            update_fields.append("title = :title")
            params["title"] = request.title
        
        if request.description is not None:
            update_fields.append("description = :description")
            params["description"] = request.description
        
        if request.priority is not None:
            update_fields.append("priority = :priority")
            params["priority"] = request.priority
        
        if request.status is not None:
            update_fields.append("status = :status")
            params["status"] = request.status
            
            # Set completed_at if status is "done"
            if request.status == "done":
                update_fields.append("completed_at = :completed_at")
                params["completed_at"] = datetime.utcnow()
            elif request.status != "done":
                update_fields.append("completed_at = NULL")
        
        if request.due_date is not None:
            update_fields.append("due_date = :due_date")
            params["due_date"] = request.due_date
        
        if request.student_id is not None:
            update_fields.append("student_id = :student_id")
            params["student_id"] = request.student_id
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_query = text(f"""
            UPDATE todo 
            SET {', '.join(update_fields)}
            WHERE id = :todo_id
            RETURNING id, title, description, priority, status, due_date, student_id, created_at, completed_at
        """)
        
        result = session.execute(update_query, params)
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
            "created_at": todo[7],
            "completed_at": todo[8]
        }

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int):
    """Delete a todo"""
    with Session(engine) as session:
        # First check if todo exists
        check_query = text("SELECT id FROM todo WHERE id = :todo_id")
        result = session.execute(check_query, {"todo_id": todo_id})
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Todo not found")
        
        # Delete the todo
        delete_query = text("DELETE FROM todo WHERE id = :todo_id")
        session.execute(delete_query, {"todo_id": todo_id})
        session.commit()
        
        return {"success": True, "message": f"Todo {todo_id} deleted successfully"}

# ========== DASHBOARD STATS ==========
@app.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    with Session(engine) as session:
        # Student count
        student_query = text("SELECT COUNT(*) FROM student")
        student_result = session.execute(student_query)
        student_count = student_result.fetchone()[0]
        
        # Todo counts by status
        todo_query = text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'todo' THEN 1 END) as todo_count,
                COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress_count,
                COUNT(CASE WHEN status = 'done' THEN 1 END) as done_count
            FROM todo
        """)
        todo_result = session.execute(todo_query)
        todo_stats = todo_result.fetchone()
        
        return {
            "students": {
                "total": student_count
            },
            "todos": {
                "total": todo_stats[0],
                "todo": todo_stats[1],
                "in_progress": todo_stats[2],
                "done": todo_stats[3]
            }
        }

# ========== UTILITY ROUTES ==========
@app.get("/")
async def root():
    return {
        "message": "Student Management API",
        "version": "2.0",
        "endpoints": {
            "auth": ["POST /login", "POST /logout", "GET /me"],
            "students": ["GET /students/", "POST /students/", "GET /students/{id}", "PUT /students/{id}", "DELETE /students/{id}"],
            "todos": ["GET /todos/", "POST /todos/", "GET /todos/{id}", "PUT /todos/{id}", "DELETE /todos/{id}"],
            "dashboard": ["GET /dashboard/stats"]
        }
    }

@app.get("/health")
async def health():
    try:
        with Session(engine) as session:
            session.execute(text("SELECT 1"))
            return {"status": "healthy", "database": "connected", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.get("/test")
async def test():
    return {
        "message": "Backend is running!",
        "time": datetime.now().isoformat(),
        "endpoints": [
            "/login",
            "/students",
            "/todos",
            "/docs"
        ]
    }

@app.get("/check/{email}")
async def check(email: str):
    with Session(engine) as session:
        # Check in usertable
        user_query = text("SELECT email FROM usertable WHERE email = :email")
        user_result = session.execute(user_query, {"email": email})
        user_exists = user_result.fetchone() is not None
        
        # Check in student table
        student_query = text("SELECT email FROM student WHERE email = :email")
        student_result = session.execute(student_query, {"email": email})
        student_exists = student_result.fetchone() is not None
        
        return {
            "user_exists": user_exists,
            "student_exists": student_exists,
            "email": email
        }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🎯 STUDENT MANAGEMENT SYSTEM - COMPLETE API")
    print("="*60)
    print("🌐 Backend: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("👤 Auth: POST /login, POST /logout, GET /me")
    print("👥 Students: Full CRUD endpoints")
    print("✅ Todos: Full CRUD endpoints")
    print("📊 Dashboard: GET /dashboard/stats")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)