from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from fastapi import FastAPI, HTTPException, Response, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select, text
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import secrets
import asyncio
import json
import hashlib

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file.")

engine = create_engine(DATABASE_URL, echo=True)

# ========== ENHANCED SESSION MANAGEMENT ==========
# Add version to invalidate sessions on restart
APP_VERSION = "2.1.0"  # Change this on major updates
SESSION_VERSION = hashlib.md5(APP_VERSION.encode()).hexdigest()[:8]

active_sessions: Dict[str, dict] = {}
app_start_time = None
app_restart_count = 0  # Track restarts

def create_session(user_data: dict) -> str:
    """Create a new session with 5-minute expiry and app version"""
    token = secrets.token_hex(32)
    expires_at = datetime.now() + timedelta(minutes=5)
    
    active_sessions[token] = {
        **user_data,
        "created_at": datetime.now(),
        "expires_at": expires_at,
        "last_active": datetime.now(),
        "app_version": APP_VERSION,  # Store app version with session
        "session_version": SESSION_VERSION
    }
    
    print(f"🆕 Session created for {user_data.get('email')}, expires at {expires_at}")
    return token

def get_session(token: str) -> Optional[dict]:
    """Get and validate session - also check app version"""
    if token not in active_sessions:
        return None
    
    session = active_sessions[token]
    
    # Check if expired
    if datetime.now() > session["expires_at"]:
        print(f"⌛ Session expired for {session.get('email')}")
        del active_sessions[token]
        return None
    
    # Check if session is from current app version
    if session.get("session_version") != SESSION_VERSION:
        print(f"🔄 Session version mismatch for {session.get('email')}. App restarted.")
        del active_sessions[token]
        return None
    
    # Update last active time
    session["last_active"] = datetime.now()
    return session

def delete_session(token: str):
    """Delete a session"""
    if token in active_sessions:
        email = active_sessions[token].get('email', 'unknown')
        del active_sessions[token]
        print(f"🗑️ Session deleted for {email}")

def cleanup_expired_sessions():
    """Clean up expired sessions periodically"""
    expired = []
    for token, session in active_sessions.items():
        if datetime.now() > session["expires_at"]:
            expired.append(token)
        elif session.get("session_version") != SESSION_VERSION:
            expired.append(token)
    
    for token in expired:
        del active_sessions[token]
    
    if expired:
        print(f"🧹 Cleaned up {len(expired)} expired/invalid sessions")

# ========== AUTH DEPENDENCY ==========
async def require_auth(request: Request):
    """Dependency to require authentication"""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please login.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    session_data = get_session(session_token)
    
    if not session_data:
        # Clear invalid cookie
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid. Please login again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return session_data

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
    global app_start_time, app_restart_count
    
    # Clear all sessions on restart
    active_sessions.clear()
    app_restart_count += 1
    
    print("\n" + "="*60)
    print(f"🚀 Student Management System Starting...")
    print(f"   Version: {APP_VERSION}")
    print(f"   Restart Count: {app_restart_count}")
    print(f"   Session Version: {SESSION_VERSION}")
    print("="*60)
    
    app_start_time = datetime.now()
    
    try:
        with Session(engine) as session:
            # Test connection first
            session.execute(text("SELECT 1"))
            print("✅ Connected to database")
            
            # Create tables if they don't exist
            print("🔄 Creating tables if needed...")
            
            # Create usertable if not exists
            try:
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS usertable (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR UNIQUE NOT NULL,
                        password VARCHAR NOT NULL
                    )
                """))
                print("✅ Created/verified usertable")
            except Exception as e:
                print(f"⚠️ Usertable error: {e}")
            
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
    
    # Start session cleanup task
    asyncio.create_task(session_cleanup_task())
    
    print("="*60)
    print("✅ Ready! Enhanced Endpoints:")
    print("   POST /login          - User login with 5-min session")
    print("   GET  /check-session  - Check session validity")
    print("   POST /logout         - Logout user")
    print("   GET  /health         - Backend health check")
    print("   GET  /status         - System status")
    print("   POST /students/      - Create student (requires auth)")
    print("   GET  /students/      - List students (requires auth)")
    print("   POST /todos/         - Create todo (requires auth)")
    print("   GET  /todos/         - List todos (requires auth)")
    print("   GET  /debug/users    - Debug: List all users")
    print("="*60)
    print("⚠️  IMPORTANT: All sessions cleared on app restart!")
    print("="*60)
    
    yield
    
    print("\n" + "="*60)
    print("🛑 Shutdown complete - clearing all sessions")
    print("="*60)

async def session_cleanup_task():
    """Background task to clean expired sessions"""
    while True:
        await asyncio.sleep(60)  # Run every minute
        cleanup_expired_sessions()
        print(f"🔄 Active sessions: {len(active_sessions)}")

app = FastAPI(lifespan=lifespan, title="Student Management API", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== ENHANCED AUTH ROUTES ==========
@app.post("/login")
async def login(request: LoginRequest, response: Response):
    """Login with user table lookup (loops through all users)"""
    print(f"📨 Login attempt: {request.email}")
    
    with Session(engine) as session:
        try:
            # Loop through all users to find match
            query = text("SELECT id, email, password FROM usertable")
            result = session.execute(query)
            all_users = result.fetchall()
            
            if not all_users:
                raise HTTPException(status_code=404, detail="No users found in database")
            
            print(f"🔍 Found {len(all_users)} users in database")
            
            matched_user = None
            for user in all_users:
                user_id, user_email, user_password = user
                print(f"  Checking: {user_email}")
                
                # Case-insensitive email comparison
                if user_email.lower() == request.email.lower():
                    print(f"  ✓ Email matches: {user_email}")
                    
                    # Password check
                    if user_password == request.password:
                        print(f"  ✓ Password matches for {user_email}")
                        matched_user = {
                            "id": user_id,
                            "email": user_email,
                            "password": user_password
                        }
                        break
                    else:
                        print(f"  ✗ Password mismatch for {user_email}")
                        raise HTTPException(status_code=401, detail="Invalid password")
            
            if not matched_user:
                print(f"❌ No user found with email: {request.email}")
                raise HTTPException(status_code=401, detail="Invalid email")
            
            # Create session
            session_token = create_session({
                "user_id": matched_user["id"],
                "email": matched_user["email"],
                "login_time": datetime.now(),
                "app_restart_count": app_restart_count
            })
            
            # Set session cookie
            response.set_cookie(
                key="session_token",
                value=session_token,
                httponly=True,
                max_age=300,  # 5 minutes in seconds
                samesite="lax",
                path="/"
            )
            
            print(f"✅ Login successful for {matched_user['email']}")
            
            return {
                "success": True,
                "message": "Login successful",
                "session_token": session_token,
                "session_expires_in": 300,  # 5 minutes
                "app_version": APP_VERSION,
                "app_restart_count": app_restart_count,
                "user": {
                    "id": matched_user["id"],
                    "email": matched_user["email"]
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Login error: {e}")
            raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/check-session")
async def check_session(request: Request):
    """Check if session is valid"""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        return {
            "authenticated": False,
            "message": "No session token",
            "app_version": APP_VERSION,
            "app_restart_count": app_restart_count,
            "requires_login": True
        }
    
    session_data = get_session(session_token)
    
    if not session_data:
        return {
            "authenticated": False,
            "message": "Session expired or invalid. App may have restarted.",
            "app_version": APP_VERSION,
            "app_restart_count": app_restart_count,
            "session_app_restart_count": session_data.get("app_restart_count") if session_data else None,
            "requires_login": True
        }
    
    # Calculate time remaining
    expires_at = session_data["expires_at"]
    time_remaining = (expires_at - datetime.now()).total_seconds()
    
    return {
        "authenticated": True,
        "app_version": APP_VERSION,
        "app_restart_count": app_restart_count,
        "session_app_restart_count": session_data.get("app_restart_count"),
        "user": {
            "id": session_data.get("user_id"),
            "email": session_data.get("email")
        },
        "session": {
            "created_at": session_data.get("created_at"),
            "expires_at": expires_at,
            "time_remaining_seconds": int(time_remaining),
            "time_remaining_minutes": round(time_remaining / 60, 1)
        },
        "active_sessions": len(active_sessions),
        "requires_login": False
    }

@app.post("/logout")
async def logout(request: Request, response: Response):
    """Logout and clear session"""
    session_token = request.cookies.get("session_token")
    
    if session_token:
        delete_session(session_token)
    
    response.delete_cookie("session_token")
    
    return {
        "success": True,
        "message": "Logged out successfully",
        "app_version": APP_VERSION,
        "active_sessions": len(active_sessions)
    }

# ========== BACKEND HEALTH MONITOR ==========
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    start_time = datetime.now()
    
    try:
        # Check database connection
        with Session(engine) as session:
            session.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    response_time = (datetime.now() - start_time).total_seconds() * 1000
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "app_version": APP_VERSION,
        "app_restart_count": app_restart_count,
        "database": db_status,
        "response_time_ms": round(response_time, 2),
        "active_sessions": len(active_sessions),
        "uptime_seconds": (datetime.now() - app_start_time).total_seconds() if app_start_time else "unknown"
    }

@app.get("/status")
async def system_status():
    """System status with sessions info"""
    return {
        "backend": {
            "status": "running",
            "version": APP_VERSION,
            "restart_count": app_restart_count,
            "start_time": app_start_time.isoformat() if app_start_time else "unknown",
            "uptime_seconds": (datetime.now() - app_start_time).total_seconds() if app_start_time else "unknown"
        },
        "sessions": {
            "total": len(active_sessions),
            "session_version": SESSION_VERSION,
            "active": [
                {
                    "email": s.get("email"),
                    "created": s.get("created_at").isoformat() if s.get("created_at") else "unknown",
                    "expires": s.get("expires_at").isoformat() if s.get("expires_at") else "unknown",
                    "time_remaining_seconds": (s.get("expires_at") - datetime.now()).total_seconds() if s.get("expires_at") else 0,
                    "app_restart_count": s.get("app_restart_count")
                }
                for s in active_sessions.values()
            ]
        }
    }

# ========== PROTECTED ROUTES ==========
# These routes now require authentication

@app.post("/students/")
async def create_student(request: StudentCreate, auth=Depends(require_auth)):
    """Create a new student (requires auth)"""
    print(f"📝 Creating student: {request.name} ({request.email}) as {auth.get('email')}")
    
    with Session(engine) as session:
        # Check if email already exists
        query = text("SELECT email FROM student WHERE email = :email")
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
            "created_at": student[3],
            "created_by": auth.get("email")
        }

@app.get("/students/")
async def list_students(auth=Depends(require_auth)):
    """List all students (requires auth)"""
    print(f"👤 {auth.get('email')} listing students")
    
    with Session(engine) as session:
        query = text("SELECT id, name, email, created_at FROM student ORDER BY created_at DESC")
        result = session.execute(query)
        students = result.fetchall()
        
        return {
            "authenticated_user": auth.get("email"),
            "students": [
                {
                    "id": s[0],
                    "name": s[1],
                    "email": s[2],
                    "created_at": s[3]
                }
                for s in students
            ]
        }

@app.post("/todos/")
async def create_todo(request: TodoCreate, auth=Depends(require_auth)):
    """Create a new todo (requires auth)"""
    print(f"📝 Creating todo: {request.title} as {auth.get('email')}")
    
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
            "created_at": todo[7],
            "created_by": auth.get("email")
        }

@app.get("/todos/")
async def list_todos(auth=Depends(require_auth)):
    """List all todos (requires auth)"""
    print(f"👤 {auth.get('email')} listing todos")
    
    with Session(engine) as session:
        query = text("""
            SELECT id, title, description, priority, status, due_date, student_id, created_at, completed_at
            FROM todo 
            ORDER BY created_at DESC
        """)
        result = session.execute(query)
        todo = result.fetchall()
        
        return {
            "authenticated_user": auth.get("email"),
            "todos": [
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
        }

# ========== DEBUG ENDPOINTS ==========
@app.get("/debug/users")
async def debug_users():
    """Debug: Show all users in usertable"""
    with Session(engine) as session:
        query = text("SELECT id, email FROM usertable ORDER BY id")
        result = session.execute(query)
        users = result.fetchall()
        
        return {
            "total_users": len(users),
            "app_version": APP_VERSION,
            "users": [
                {"id": u[0], "email": u[1]}
                for u in users
            ]
        }

# ========== UTILITY ROUTES ==========
@app.get("/")
async def root():
    return {
        "message": "Student Management API",
        "version": APP_VERSION,
        "restart_count": app_restart_count,
        "session_version": SESSION_VERSION,
        "requires_login": True,
        "features": [
            "Enhanced session management (5-minute sessions)",
            "Automatic logout on app restart",
            "Continuous backend health monitoring",
            "User table lookup with loop iteration",
            "Protected student and todo management"
        ],
        "endpoints": {
            "auth": ["POST /login", "GET /check-session", "POST /logout"],
            "monitoring": ["GET /health", "GET /status"],
            "students": ["GET /students/", "POST /students/", "GET /students/{id}", "PUT /students/{id}", "DELETE /students/{id}"],
            "todos": ["GET /todos/", "POST /todos/", "GET /todos/{id}", "PUT /todos/{id}"],
            "debug": ["GET /debug/users", "GET /debug/user/{email}", "GET /debug/todo-details/{id}"]
        }
    }

# ... [Keep the rest of your routes as they are, just add auth dependency to protected ones]
# Remember to add `auth=Depends(require_auth)` to other protected routes like:
# - PUT /students/{student_id}
# - DELETE /students/{student_id}
# - GET /students/{student_id}
# - PUT /todos/{todo_id}
# - GET /todos/{todo_id}
# - etc.

# ========== REQUEST LOGGING MIDDLEWARE ==========
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging"""
    start_time = datetime.now()
    
    # Log request
    print(f"\n📨 {request.method} {request.url.path}")
    print(f"   Client: {request.client.host if request.client else 'unknown'}")
    
    # Try to log request body for POST/PUT requests
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
            if body:
                try:
                    body_json = json.loads(body)
                    print(f"   Body: {json.dumps(body_json, indent=2)}")
                except:
                    print(f"   Body (raw): {body.decode()[:200]}...")
        except:
            pass
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = (datetime.now() - start_time).total_seconds() * 1000
    print(f"   Response: {response.status_code} ({process_time:.2f}ms)")
    
    return response

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🎯 STUDENT MANAGEMENT SYSTEM - ENHANCED VERSION")
    print("="*60)
    print(f"🌐 Backend: http://localhost:8000")
    print(f"📖 Docs: http://localhost:8000/docs")
    print(f"🔐 Auth: POST /login (5-minute sessions)")
    print(f"👥 Students: Full CRUD operations (requires login)")
    print(f"✅ Todos: Full CRUD operations (requires login)")
    print(f"🩺 Health: GET /health (continuous monitoring)")
    print(f"📊 Status: GET /status (session info)")
    print("="*60)
    print("⚠️  IMPORTANT FEATURES:")
    print(f"   • Version: {APP_VERSION}")
    print("   • User table lookup with loop iteration")
    print("   • 5-minute auto-expiring sessions")
    print("   • Automatic logout on app restart")
    print("   • Continuous backend health checks")
    print("   • Always requires login for protected routes")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)