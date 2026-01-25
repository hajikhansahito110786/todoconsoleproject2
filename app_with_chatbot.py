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
import asyncio
import json
import httpx
import openai

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file.")

engine = create_engine(DATABASE_URL, echo=True)

# ========== ENHANCED SESSION MANAGEMENT ==========
active_sessions: Dict[str, dict] = {}
app_start_time = None

def create_session(user_data: dict) -> str:
    """Create a new session with 5-minute expiry"""
    token = secrets.token_hex(32)
    expires_at = datetime.now() + timedelta(minutes=5)

    active_sessions[token] = {
        **user_data,
        "created_at": datetime.now(),
        "expires_at": expires_at,
        "last_active": datetime.now()
    }

    print(f"[NEW] Session created for {user_data.get('email')}, expires at {expires_at}")
    return token

def get_session(token: str) -> Optional[dict]:
    """Get and validate session"""
    if token not in active_sessions:
        return None

    session = active_sessions[token]

    # Check if expired
    if datetime.now() > session["expires_at"]:
        print(f"[EXPIRED] Session expired for {session.get('email')}")
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
        print(f"[DELETED] Session deleted for {email}")

def cleanup_expired_sessions():
    """Clean up expired sessions periodically"""
    expired = []
    for token, session in active_sessions.items():
        if datetime.now() > session["expires_at"]:
            expired.append(token)

    for token in expired:
        del active_sessions[token]

    if expired:
        print(f"[CLEANUP] Cleaned up {len(expired)} expired sessions")

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

class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None)
    action: str  # Action performed (login, create_todo, update_todo, etc.)
    resource_type: str  # Type of resource (user, todo, student)
    resource_id: Optional[int] = Field(default=None)  # ID of the resource
    details: Optional[str] = None  # Additional details about the action
    ip_address: Optional[str] = None  # IP address of the requester
    user_agent: Optional[str] = None  # User agent string
    timestamp: datetime = Field(default_factory=datetime.utcnow)

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

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[int] = None

# ========== AUDIT LOGGING FUNCTIONS ==========
def log_audit_action(user_id: Optional[int], action: str, resource_type: str,
                     resource_id: Optional[int] = None, details: Optional[str] = None,
                     ip_address: Optional[str] = None, user_agent: Optional[str] = None):
    """Log an action to the audit trail"""
    try:
        with Session(engine) as session:
            audit_entry = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent
            )
            session.add(audit_entry)
            session.commit()
            print(f"[AUDIT] Logged action: {action} on {resource_type}:{resource_id} by user:{user_id}")
    except Exception as e:
        print(f"[AUDIT ERROR] Failed to log action: {e}")

# ========== LIFESPAN ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    global app_start_time
    print("\n" + "="*50)
    print("APP Student Management System Starting...")
    print("="*50)

    app_start_time = datetime.now()

    try:
        with Session(engine) as session:
            # Test connection first
            session.execute(text("SELECT 1"))
            print("[SUCCESS] Connected to database")

            # Create tables if they don't exist
            print("🔄 Creating tables if needed...")

            # Create usertable if not exists
            try:
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS usertable (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL
                    )
                """))
                print("[SUCCESS] Created/verified usertable")
            except Exception as e:
                print(f"[WARNING] Usertable error: {e}")

            # Create student table
            try:
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS student (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                print("[SUCCESS] Created/verified student table")
            except Exception as e:
                print(f"[WARNING] Student table error: {e}")

            # Create todo table
            try:
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS todo (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT,
                        priority TEXT DEFAULT 'medium',
                        status TEXT DEFAULT 'todo',
                        due_date TEXT,
                        student_id INTEGER,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        completed_at TEXT
                    )
                """))
                print("[SUCCESS] Created/verified todo table")
            except Exception as e:
                print(f"[WARNING] Todo table error: {e}")

            # Create audit_log table
            try:
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        action TEXT NOT NULL,
                        resource_type TEXT NOT NULL,
                        resource_id INTEGER,
                        details TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                print("[SUCCESS] Created/verified audit_log table")
            except Exception as e:
                print(f"[WARNING] Audit log table error: {e}")

            session.commit()

    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        print("[WARNING] Continuing with existing tables...")

    # Start session cleanup task
    asyncio.create_task(session_cleanup_task())

    print("="*50)
    print("[READY] Enhanced Endpoints:")
    print("   POST /login          - User login with 5-min session")
    print("   GET  /check-session  - Check session validity")
    print("   POST /logout         - Logout user")
    print("   GET  /health         - Backend health check")
    print("   GET  /status         - System status")
    print("   POST /students/      - Create student")
    print("   GET  /students/      - List students")
    print("   POST /todos/         - Create todo")
    print("   GET  /todos/         - List todos")
    print("   POST /chat           - AI chatbot endpoint")
    print("   GET  /debug/users    - Debug: List all users")
    print("   GET  /audit-logs     - Retrieve audit logs")
    print("="*50)

    yield

    print("\n" + "="*50)
    print("🛑 Shutdown complete")
    print("="*50)


async def session_cleanup_task():
    """Background task to clean expired sessions"""
    while True:
        await asyncio.sleep(60)  # Run every minute
        cleanup_expired_sessions()
        print(f"[REFRESH] Active sessions: {len(active_sessions)}")

app = FastAPI(lifespan=lifespan)

# ========== AUDIT LOG ENDPOINTS ==========
@app.get("/audit-logs")
async def get_audit_logs():
    """Retrieve audit logs"""
    try:
        with Session(engine) as session:
            query = text("""
                SELECT id, user_id, action, resource_type, resource_id, details,
                       ip_address, user_agent, timestamp
                FROM audit_log
                ORDER BY timestamp DESC
                LIMIT 100
            """)
            result = session.execute(query)
            audit_logs = result.fetchall()

            return [
                {
                    "id": log[0],
                    "user_id": log[1],
                    "action": log[2],
                    "resource_type": log[3],
                    "resource_id": log[4],
                    "details": log[5],
                    "ip_address": log[6],
                    "user_agent": log[7],
                    "timestamp": log[8]
                }
                for log in audit_logs
            ]
    except Exception as e:
        print(f"[ERROR] Failed to retrieve audit logs: {e}")
        return []

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== ENHANCED AUTH ROUTES ==========
@app.post("/login")
async def login(request: LoginRequest, response: Response, request_obj: Request = None):
    """Login with user table lookup (loops through all users)"""
    print(f"[REQUEST] Login attempt: {request.email}")

    with Session(engine) as session:
        try:
            # Loop through all users to find match
            query = text("SELECT id, email, password FROM usertable")
            result = session.execute(query)
            all_users = result.fetchall()

            if not all_users:
                # Log failed login attempt
                log_audit_action(
                    user_id=None,
                    action="login_failed_no_users",
                    resource_type="user",
                    details=f"Login attempt for {request.email}, no users found in database",
                    ip_address=request_obj.client.host if request_obj and request_obj.client else None,
                    user_agent=request_obj.headers.get("user-agent") if request_obj else None
                )

                raise HTTPException(status_code=404, detail="No users found in database")

            print(f"Found {len(all_users)} users in database")

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

                        # Log failed login attempt
                        log_audit_action(
                            user_id=user_id,
                            action="login_failed_invalid_password",
                            resource_type="user",
                            details=f"Failed login attempt for {request.email}",
                            ip_address=request_obj.client.host if request_obj and request_obj.client else None,
                            user_agent=request_obj.headers.get("user-agent") if request_obj else None
                        )

                        raise HTTPException(status_code=401, detail="Invalid password")

            if not matched_user:
                print(f"[ERROR] No user found with email: {request.email}")

                # Log failed login attempt
                log_audit_action(
                    user_id=None,
                    action="login_failed_invalid_email",
                    resource_type="user",
                    details=f"Failed login attempt for {request.email} - email not found",
                    ip_address=request_obj.client.host if request_obj and request_obj.client else None,
                    user_agent=request_obj.headers.get("user-agent") if request_obj else None
                )

                raise HTTPException(status_code=401, detail="Invalid email")

            # Create session
            session_token = create_session({
                "user_id": matched_user["id"],
                "email": matched_user["email"],
                "login_time": datetime.now()
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

            print(f"[SUCCESS] Login successful for {matched_user['email']}")

            # Log successful login
            log_audit_action(
                user_id=matched_user["id"],
                action="login_success",
                resource_type="user",
                details=f"Successful login for {matched_user['email']}",
                ip_address=request_obj.client.host if request_obj and request_obj.client else None,
                user_agent=request_obj.headers.get("user-agent") if request_obj else None
            )

            return {
                "success": True,
                "message": "Login successful",
                "session_token": session_token,
                "session_expires_in": 300,  # 5 minutes
                "user": {
                    "id": matched_user["id"],
                    "email": matched_user["email"]
                }
            }

        except HTTPException:
            raise
        except Exception as e:
            print(f"[ERROR] Login error: {e}")

            # Log system error during login
            log_audit_action(
                user_id=None,
                action="login_system_error",
                resource_type="user",
                details=f"System error during login for {request.email}: {str(e)}",
                ip_address=request_obj.client.host if request_obj and request_obj.client else None,
                user_agent=request_obj.headers.get("user-agent") if request_obj else None
            )

            raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/check-session")
async def check_session(request: Request):
    """Check if session is valid"""
    session_token = request.cookies.get("session_token")

    if not session_token:
        return {
            "authenticated": False,
            "message": "No session token",
            "active_sessions": len(active_sessions)
        }

    session_data = get_session(session_token)

    if not session_data:
        return {
            "authenticated": False,
            "message": "Session expired or invalid",
            "active_sessions": len(active_sessions)
        }

    # Calculate time remaining
    expires_at = session_data["expires_at"]
    time_remaining = (expires_at - datetime.now()).total_seconds()

    return {
        "authenticated": True,
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
        "active_sessions": len(active_sessions)
    }

@app.post("/logout")
async def logout(request: Request, response: Response):
    """Logout and clear session"""
    session_token = request.cookies.get("session_token")

    # Get session data before deleting it to log the action
    session_data = get_session(session_token) if session_token else None
    user_id = session_data.get("user_id") if session_data else None

    if session_token:
        delete_session(session_token)

    response.delete_cookie("session_token")

    # Log the logout action
    log_audit_action(
        user_id=user_id,
        action="logout",
        resource_type="user",
        details=f"User logged out",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return {
        "success": True,
        "message": "Logged out successfully",
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
            "start_time": app_start_time.isoformat() if app_start_time else "unknown",
            "uptime_seconds": (datetime.now() - app_start_time).total_seconds() if app_start_time else "unknown"
        },
        "sessions": {
            "total": len(active_sessions),
            "active": [
                {
                    "email": s.get("email"),
                    "created": s.get("created_at").isoformat() if s.get("created_at") else "unknown",
                    "expires": s.get("expires_at").isoformat() if s.get("expires_at") else "unknown",
                    "time_remaining_seconds": (s.get("expires_at") - datetime.now()).total_seconds() if s.get("expires_at") else 0
                }
                for s in active_sessions.values()
            ]
        }
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
            "users": [
                {"id": u[0], "email": u[1]}
                for u in users
            ]
        }

# ========== STUDENT ROUTES ==========
@app.post("/students/")
async def create_student(request: StudentCreate, request_obj: Request = None):
    """Create a new student"""
    print(f"📝 Creating student: {request.name} ({request.email})")

    # Get user ID from session if available
    user_id = None
    if request_obj:
        session_token = request_obj.cookies.get("session_token")
        if session_token:
            session_data = get_session(session_token)
            if session_data:
                user_id = session_data.get("user_id")

    with Session(engine) as session:
        # Check if email already exists
        query = text("SELECT email FROM student WHERE email = :email")
        result = session.execute(query, {"email": request.email})
        existing = result.fetchone()

        if existing:
            # Log failed attempt due to duplicate email
            log_audit_action(
                user_id=user_id,
                action="create_student_failed_duplicate",
                resource_type="student",
                details=f"Failed to create student {request.name} - email {request.email} already exists",
                ip_address=request_obj.client.host if request_obj and request_obj.client else None,
                user_agent=request_obj.headers.get("user-agent") if request_obj else None
            )

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

        # Log successful student creation
        log_audit_action(
            user_id=user_id,
            action="create_student",
            resource_type="student",
            resource_id=student[0] if student else None,
            details=f"Created student {request.name} with email {request.email}",
            ip_address=request_obj.client.host if request_obj and request_obj.client else None,
            user_agent=request_obj.headers.get("user-agent") if request_obj else None
        )

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
        query = text("SELECT id, name, email, created_at FROM student ORDER BY created_at DESC")
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
        query = text("SELECT * FROM student WHERE id = :student_id")
        result = session.execute(query, {"student_id": student_id})
        student = result.fetchone()

        if not student:
            raise HTTPException(status_code=404, detail=f"Student {student_id} not found")

        if hasattr(student, '_mapping'):
            student_dict = dict(student._mapping)
        else:
            student_dict = dict(zip(result.keys(), student))

        return student_dict

@app.put("/students/{student_id}")
async def update_student(student_id: int, request: dict):
    """Update a student"""
    print(f"📝 Updating student {student_id} with data:", request)

    with Session(engine) as session:
        try:
            # 1. Check if student exists
            check_query = text("SELECT id FROM student WHERE id = :student_id")
            check_result = session.execute(check_query, {"student_id": student_id})
            if not check_result.fetchone():
                raise HTTPException(status_code=404, detail=f"Student {student_id} not found")

            # 2. Check if email is already taken by another student
            if 'email' in request and request['email']:
                email_check_query = text("""
                    SELECT id FROM student
                    WHERE email = :email AND id != :student_id
                """)
                email_check_result = session.execute(email_check_query, {
                    "email": request['email'],
                    "student_id": student_id
                })
                if email_check_result.fetchone():
                    raise HTTPException(
                        status_code=400,
                        detail="Email already taken by another student"
                    )

            # 3. Build update query
            update_fields = []
            params = {"student_id": student_id}

            allowed_fields = ['name', 'email']

            for field in allowed_fields:
                if field in request and request[field] is not None:
                    update_fields.append(f"{field} = :{field}")
                    params[field] = request[field]

            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields to update")

            # 4. Execute update
            update_query = text(f"""
                UPDATE student
                SET {', '.join(update_fields)}
                WHERE id = :student_id
                RETURNING *
            """)

            result = session.execute(update_query, params)
            session.commit()

            # 5. Get updated student
            get_query = text("SELECT * FROM student WHERE id = :student_id")
            get_result = session.execute(get_query, {"student_id": student_id})
            updated_row = get_result.fetchone()

            if hasattr(updated_row, '_mapping'):
                student_dict = dict(updated_row._mapping)
            else:
                student_dict = dict(zip(get_result.keys(), updated_row))

            print(f"[SUCCESS] Updated student {student_id}:", student_dict)
            return student_dict

        except HTTPException:
            raise
        except Exception as e:
            print(f"[ERROR] Error updating student {student_id}: {e}")
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update student: {str(e)}")

@app.delete("/students/{student_id}")
async def delete_student(student_id: int):
    """Delete a student"""
    with Session(engine) as session:
        try:
            # Check if student exists
            check_query = text("SELECT id FROM student WHERE id = :student_id")
            check_result = session.execute(check_query, {"student_id": student_id})
            if not check_result.fetchone():
                raise HTTPException(status_code=404, detail=f"Student {student_id} not found")

            # First, update todos to remove student_id reference
            update_todos_query = text("""
                UPDATE todo
                SET student_id = NULL
                WHERE student_id = :student_id
            """)
            session.execute(update_todos_query, {"student_id": student_id})

            # Delete the student
            delete_query = text("DELETE FROM student WHERE id = :student_id")
            session.execute(delete_query, {"student_id": student_id})

            session.commit()

            return {
                "success": True,
                "message": f"Student {student_id} deleted successfully",
                "todo_references_cleared": True
            }

        except Exception as e:
            session.rollback()
            print(f"[ERROR] Error deleting student {student_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete student: {str(e)}")

@app.get("/debug/student/{student_id}")
async def debug_student(student_id: int):
    """Debug endpoint for student"""
    with Session(engine) as session:
        # Get student
        query = text("SELECT * FROM student WHERE id = :student_id")
        result = session.execute(query, {"student_id": student_id})
        student = result.fetchone()

        if not student:
            return {"error": f"Student {student_id} not found"}

        # Get todos assigned to this student
        todos_query = text("""
            SELECT id, title, status, priority
            FROM todo
            WHERE student_id = :student_id
            ORDER BY created_at DESC
        """)
        todos_result = session.execute(todos_query, {"student_id": student_id})
        todos = todos_result.fetchall()

        # Convert student to dict
        if hasattr(student, '_mapping'):
            student_dict = dict(student._mapping)
        else:
            student_dict = dict(zip(result.keys(), student))

        return {
            "student": student_dict,
            "assigned_todos": [
                {"id": t[0], "title": t[1], "status": t[2], "priority": t[3]}
                for t in todos
            ],
            "todo_count": len(todos)
        }

# ========== TODO ROUTES ==========
@app.post("/todos/")
async def create_todo(request: TodoCreate, request_obj: Request = None):
    """Create a new todo"""
    print(f"📝 Creating todo: {request.title}")

    # Get user ID from session if available
    user_id = None
    if request_obj:
        session_token = request_obj.cookies.get("session_token")
        if session_token:
            session_data = get_session(session_token)
            if session_data:
                user_id = session_data.get("user_id")

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

        # Log successful todo creation
        log_audit_action(
            user_id=user_id,
            action="create_todo",
            resource_type="todo",
            resource_id=todo[0] if todo else None,
            details=f"Created todo '{request.title}' with priority {request.priority} and status {request.status}",
            ip_address=request_obj.client.host if request_obj and request_obj.client else None,
            user_agent=request_obj.headers.get("user-agent") if request_obj else None
        )

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

@app.get("/todos/{todo_id}")
async def get_todo(todo_id: int):
    """Get single todo with SQLAlchemy 2.0 compatibility"""
    with Session(engine) as session:
        try:
            # Method 1: Try with mapping
            query = text("SELECT * FROM todo WHERE id = :todo_id")
            result = session.execute(query, {"todo_id": todo_id})
            row = result.fetchone()

            if not row:
                # Try alternative query
                alt_query = text("""
                    SELECT t.*, s.name as student_name, s.email as student_email
                    FROM todo t
                    LEFT JOIN student s ON t.student_id = s.id
                    WHERE t.id = :todo_id
                """)
                alt_result = session.execute(alt_query, {"todo_id": todo_id})
                alt_row = alt_result.fetchone()

                if not alt_row:
                    raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")

                # Convert to dict
                if hasattr(alt_row, '_mapping'):
                    todo_dict = dict(alt_row._mapping)
                else:
                    todo_dict = dict(zip(alt_result.keys(), alt_row))
            else:
                # Convert to dict
                if hasattr(row, '_mapping'):
                    todo_dict = dict(row._mapping)
                else:
                    todo_dict = dict(zip(result.keys(), row))

            # Normalize priority and status to lowercase
            if 'priority' in todo_dict and todo_dict['priority']:
                todo_dict['priority'] = str(todo_dict['priority']).lower()

            if 'status' in todo_dict and todo_dict['status']:
                todo_dict['status'] = str(todo_dict['status']).lower()

            return todo_dict

        except HTTPException:
            raise
        except Exception as e:
            print(f"Error getting todo {todo_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error: {str(e)}"
            )

@app.put("/todos/{todo_id}")
async def update_todo(todo_id: int, request: dict):
    """Update a todo - SQLAlchemy 2.0 compatible"""
    print(f"📝 Updating todo {todo_id} with data:", request)

    with Session(engine) as session:
        try:
            # 1. Check if todo exists
            check_query = text("SELECT id FROM todo WHERE id = :todo_id")
            check_result = session.execute(check_query, {"todo_id": todo_id})
            if not check_result.fetchone():
                raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")

            # 2. Build update query dynamically
            update_fields = []
            params = {"todo_id": todo_id}

            allowed_fields = ['title', 'description', 'priority', 'status', 'due_date', 'student_id']

            for field in allowed_fields:
                if field in request and request[field] is not None:
                    update_fields.append(f"{field} = :{field}")
                    params[field] = request[field]

            # Handle status change - set completed_at if status becomes 'done'
            if 'status' in request and request['status']:
                status_lower = str(request['status']).lower()
                if status_lower == 'done':
                    update_fields.append("completed_at = :completed_at")
                    params["completed_at"] = datetime.utcnow()
                elif status_lower != 'done':
                    update_fields.append("completed_at = NULL")

            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields to update")

            # 3. Execute update
            update_query = text(f"""
                UPDATE todo
                SET {', '.join(update_fields)}
                WHERE id = :todo_id
                RETURNING *
            """)

            print(f"Executing query: {update_query}")
            print(f"With params: {params}")

            result = session.execute(update_query, params)
            session.commit()

            # 4. Get updated todo
            get_query = text("SELECT * FROM todo WHERE id = :todo_id")
            get_result = session.execute(get_query, {"todo_id": todo_id})
            updated_row = get_result.fetchone()

            if not updated_row:
                raise HTTPException(status_code=500, detail="Failed to retrieve updated todo")

            # 5. Convert to dict (SQLAlchemy 2.0 compatible)
            if hasattr(updated_row, '_mapping'):
                todo_dict = dict(updated_row._mapping)
            else:
                todo_dict = dict(zip(get_result.keys(), updated_row))

            print(f"[SUCCESS] Updated todo {todo_id}:", todo_dict)
            return todo_dict

        except HTTPException:
            raise
        except Exception as e:
            print(f"[ERROR] Error updating todo {todo_id}: {e}")
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update todo: {str(e)}")

# ========== CONTEXT-AWARE CHATBOT API ENDPOINT ==========
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Context-aware chat endpoint for the AI assistant with database integration"""
    try:
        user_message = request.message
        user_id = request.user_id

        if not user_message.strip():
            return {"response": "Please enter a message."}

        # Get AI service preference from environment variable
        ai_service = os.getenv("AI_SERVICE", "fallback")  # Default to fallback responses

        # Convert message to lowercase for processing
        user_msg_lower = user_message.lower()

        # Get database context if available
        student_count = 0
        todo_count = 0

        try:
            with Session(engine) as session:
                # Count students
                student_query = text("SELECT COUNT(*) FROM student")
                student_result = session.execute(student_query)
                student_count = student_result.scalar()

                # Count todos
                todo_query = text("SELECT COUNT(*) FROM todo")
                todo_result = session.execute(todo_query)
                todo_count = todo_result.scalar()
        except Exception as db_error:
            print(f"Database context error (non-critical): {db_error}")
            # Continue with zero counts

        # Define responses based on keywords with database context
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
            # Enhanced fallback to rule-based responses with database context
            if any(word in user_msg_lower for word in ["hello", "hi", "hey", "greetings"]):
                response = f"Hello! I'm your AI assistant for managing tasks. Currently, you have {student_count} students and {todo_count} todos in the system. How can I help you today?"
            elif any(word in user_msg_lower for word in ["help", "assist", "support"]):
                response = (f"I can help you manage your {student_count} students and {todo_count} todos. "
                           "You can ask me to create, update, or check tasks. "
                           "For example, you can say 'create a new todo', 'show my tasks', or 'add a student'.")
            elif any(word in user_msg_lower for word in ["todo", "task", "work", "assignment"]):
                response = (f"I can help you manage your {todo_count} todos. You can ask me to create a new task, "
                           "mark a task as complete, or view your tasks. "
                           "Try saying 'create a new todo called [task name]' or 'show my todos'.")
            elif any(word in user_msg_lower for word in ["student", "class", "enroll"]):
                response = (f"I can help you manage your {student_count} students. You can ask me to create a new student "
                           "or check student information. Try saying 'add a student named [name] with email [email]'.")
            elif any(word in user_msg_lower for word in ["create", "add", "new"]):
                if any(word in user_msg_lower for word in ["todo", "task", "work", "assignment"]):
                    response = ("To create a new todo, go to the 'Todos' section and click 'Add New Todo'. "
                               "You can specify the title, description, priority, and assign it to a student.")
                elif any(word in user_msg_lower for word in ["student", "class", "person"]):
                    response = ("To create a new student, go to the 'Students' section and click 'Add New Student'. "
                               "You'll need to provide the student's name and email address.")
                else:
                    response = ("You can create new todos or students through the interface. "
                               "Would you like to create a new todo or student?")
            elif any(word in user_msg_lower for word in ["complete", "done", "finish"]):
                response = ("You can mark tasks as complete in the todos section of the application. "
                           "Find the task you want to mark as complete and click the checkbox next to it.")
            elif any(word in user_msg_lower for word in ["view", "see", "show", "list"]):
                response = ("You can view your todos and students in their respective sections of the application. "
                           "Click on 'Todos' or 'Students' in the navigation menu to see all items.")
            elif any(word in user_msg_lower for word in ["thank", "thanks"]):
                response = "You're welcome! Is there anything else I can help you with?"
            elif "create todo" in user_msg_lower or "add todo" in user_msg_lower:
                response = ("To create a new todo, navigate to the 'Todos' section and click 'Add New Todo'. "
                           "Fill in the title, description, priority level, and assign it to a student if needed.")
            elif "create student" in user_msg_lower or "add student" in user_msg_lower:
                response = ("To create a new student, navigate to the 'Students' section and click 'Add New Student'. "
                           "Enter the student's name and email address, then click 'Create'.")
            elif "delete" in user_msg_lower and any(word in user_msg_lower for word in ["todo", "task"]):
                response = ("To delete a todo, go to the 'Todos' section, find the task you want to delete, "
                           "and click the delete button associated with that task.")
            elif "delete" in user_msg_lower and any(word in user_msg_lower for word in ["student"]):
                response = ("To delete a student, go to the 'Students' section, find the student you want to delete, "
                           "and click the delete button associated with that student. Note that deleting a student "
                           "will remove them from any assigned tasks but won't delete the tasks themselves.")
            elif "update" in user_msg_lower or "edit" in user_msg_lower:
                response = ("To update a todo or student, go to the respective section, find the item you want to edit, "
                           "and click the edit button. Make your changes and save them.")
            elif "priority" in user_msg_lower:
                response = ("Todos can have three priority levels: Low, Medium, or High. "
                           "When creating or editing a todo, you can select the appropriate priority level.")
            elif "status" in user_msg_lower:
                response = ("Todos have three status options: 'To Do', 'In Progress', and 'Done'. "
                           "You can update the status as you work on your tasks.")
            elif "due date" in user_msg_lower:
                response = ("When creating or editing a todo, you can optionally set a due date. "
                           "This helps you keep track of upcoming deadlines.")
            elif "count" in user_msg_lower or "how many" in user_msg_lower:
                response = f"You currently have {student_count} students and {todo_count} todos in the system."
            else:
                response = (f"I received your message: '{user_message}'. I'm your AI assistant for managing tasks. "
                           f"Currently, you have {student_count} students and {todo_count} todos in the system. "
                           "You can ask me about creating, viewing, or managing your todos and students. "
                           "For example, try asking about creating a new todo or adding a student.")

            return {"response": response}

        # Use AI service if configured
        if ai_service == "openai" and os.getenv("OPENAI_API_KEY"):
            # Use OpenAI API
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            # Prepare context about the application with database stats
            system_prompt = f"""
            You are an AI assistant for a student management system that handles todos and students.
            The system has the following capabilities:
            - Creating, reading, updating, and deleting students
            - Creating, reading, updating, and deleting todos
            - Managing task priorities (low, medium, high)
            - Managing task statuses (to do, in progress, done)
            - Assigning todos to students

            Current database statistics:
            - Students: {student_count}
            - Todos: {todo_count}

            Respond to user queries about these capabilities. If they ask about creating or managing
            students or todos, provide specific instructions on how to do so in the application.
            Include the current statistics when relevant to the user's query.
            """

            try:
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ]
                )

                response = completion.choices[0].message.content

            except Exception as e:
                print(f"OpenAI API error: {e}")
                response = f"I encountered an error processing your request: {str(e)}. Please check your API key."

        elif ai_service == "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
            # Use Anthropic API (Claude)
            import anthropic

            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            # Prepare context about the application with database stats
            system_prompt = f"""
            You are an AI assistant for a student management system that handles todos and students.
            The system has the following capabilities:
            - Creating, reading, updating, and deleting students
            - Creating, reading, updating, and deleting todos
            - Managing task priorities (low, medium, high)
            - Managing task statuses (to do, in progress, done)
            - Assigning todos to students

            Current database statistics:
            - Students: {student_count}
            - Todos: {todo_count}

            Respond to user queries about these capabilities. If they ask about creating or managing
            students or todos, provide specific instructions on how to do so in the application.
            Include the current statistics when relevant to the user's query.
            """

            try:
                message = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1000,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_message}
                    ]
                )

                response = message.content[0].text

            except Exception as e:
                print(f"Anthropic API error: {e}")
                response = f"I encountered an error processing your request: {str(e)}. Please check your API key."

        elif ai_service == "google" and os.getenv("GOOGLE_API_KEY"):
            # Use Google Gemini API
            import google.generativeai as genai

            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel('gemini-pro')

            # Prepare context about the application with database stats
            context = f"""
            You are an AI assistant for a student management system that handles todos and students.
            The system has the following capabilities:
            - Creating, reading, updating, and deleting students
            - Creating, reading, updating, and deleting todos
            - Managing task priorities (low, medium, high)
            - Managing task statuses (to do, in progress, done)
            - Assigning todos to students

            Current database statistics:
            - Students: {student_count}
            - Todos: {todo_count}

            Respond to user queries about these capabilities. If they ask about creating or managing
            students or todos, provide specific instructions on how to do so in the application.
            Include the current statistics when relevant to the user's query.
            """

            try:
                full_prompt = f"{context}\n\nUser query: {user_message}"
                response = model.generate_content(full_prompt)

                if response.text:
                    response = response.text
                else:
                    response = "I couldn't generate a response. Please try again."

            except Exception as e:
                print(f"Google API error: {e}")
                response = f"I encountered an error processing your request: {str(e)}. Please check your API key."

        else:
            # Fallback to enhanced rule-based responses with database context
            response = f"I'm sorry, but I couldn't connect to the AI service. Please make sure your API key is set correctly. You asked: '{user_message}' Currently, you have {student_count} students and {todo_count} todos in the system."

        return {"response": response}

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return {"response": "Sorry, I encountered an error processing your request. Please try again."}

# ========== UTILITY ROUTES ==========
@app.get("/")
async def root():
    return {
        "message": "Student Management API with AI Chatbot and Audit Trail",
        "version": "4.0",
        "features": [
            "Enhanced session management (5-minute sessions)",
            "Continuous backend health monitoring",
            "User table lookup with loop iteration",
            "Protected student and todo management",
            "AI-powered chatbot with multiple service support",
            "Audit trails for all user actions",
            "Default login requirement for all operations"
        ],
        "endpoints": {
            "auth": ["POST /login", "GET /check-session", "POST /logout"],
            "monitoring": ["GET /health", "GET /status"],
            "students": ["GET /students/", "POST /students/", "GET /students/{id}", "PUT /students/{id}", "DELETE /students/{id}"],
            "todos": ["GET /todos/", "POST /todos/", "GET /todos/{id}", "PUT /todos/{id}"],
            "chatbot": ["POST /chat"],
            "audit": ["GET /audit-logs"],
            "debug": ["GET /debug/users", "GET /debug/user/{email}", "GET /debug/todo-details/{id}"]
        }
    }

@app.get("/test")
async def test():
    return {
        "message": "Backend is running with enhanced features!",
        "time": datetime.now().isoformat(),
        "active_sessions": len(active_sessions),
        "session_expiry_minutes": 5
    }

@app.get("/check/{email}")
async def check(email: str):
    with Session(engine) as session:
        query = text("SELECT email FROM usertable WHERE email = :email")
        result = session.execute(query, {"email": email})
        exists = result.fetchone() is not None
        return {"exists": exists, "email": email}

# ========== REQUEST LOGGING MIDDLEWARE ==========
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging"""
    start_time = datetime.now()

    # Log request
    print(f"\n[REQUEST] {request.method} {request.url.path}")
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
    uvicorn.run(app, host="0.0.0.0", port=8000)