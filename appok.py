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
    
    print(f"🆕 Session created for {user_data.get('email')}, expires at {expires_at}")
    return token

def get_session(token: str) -> Optional[dict]:
    """Get and validate session"""
    if token not in active_sessions:
        return None
    
    session = active_sessions[token]
    
    # Check if expired
    if datetime.now() > session["expires_at"]:
        print(f"⌛ Session expired for {session.get('email')}")
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
    
    for token in expired:
        del active_sessions[token]
    
    if expired:
        print(f"🧹 Cleaned up {len(expired)} expired sessions")

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
    global app_start_time
    print("\n" + "="*50)
    print("🚀 Student Management System Starting...")
    print("="*50)
    
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
    
    print("="*50)
    print("✅ Ready! Enhanced Endpoints:")
    print("   POST /login          - User login with 5-min session")
    print("   GET  /check-session  - Check session validity")
    print("   POST /logout         - Logout user")
    print("   GET  /health         - Backend health check")
    print("   GET  /status         - System status")
    print("   POST /students/      - Create student")
    print("   GET  /students/      - List students")
    print("   POST /todos/         - Create todo")
    print("   GET  /todos/         - List todos")
    print("   GET  /debug/users    - Debug: List all users")
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
        print(f"🔄 Active sessions: {len(active_sessions)}")

app = FastAPI(lifespan=lifespan)

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
            
            print(f"✅ Login successful for {matched_user['email']}")
            
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
    
    if session_token:
        delete_session(session_token)
    
    response.delete_cookie("session_token")
    
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

@app.get("/debug/user/{email}")
async def debug_user(email: str):
    """Debug: Check user details"""
    with Session(engine) as session:
        # Case-insensitive search
        query = text("""
            SELECT id, email, password 
            FROM usertable 
            WHERE LOWER(email) = LOWER(:email)
        """)
        result = session.execute(query, {"email": email})
        user = result.fetchone()
        
        if not user:
            # Try exact match
            query = text("SELECT id, email, password FROM usertable WHERE email = :email")
            result = session.execute(query, {"email": email})
            user = result.fetchone()
            
            if not user:
                return {"error": f"User '{email}' not found in database"}
        
        user_id, user_email, user_password = user
        
        return {
            "user": {
                "id": user_id,
                "email": user_email,
                "password_length": len(user_password),
                "password_masked": user_password[0] + "*" * (len(user_password) - 2) + user_password[-1] if len(user_password) > 2 else "***"
            },
            "note": "Password is stored in plain text (insecure - for development only)"
        }

@app.post("/admin/reset-password")
async def admin_reset_password(email: str = "admin@example.com", new_password: str = "admin123"):
    """Reset admin password (development only)"""
    with Session(engine) as session:
        # Check if user exists
        query = text("SELECT id FROM usertable WHERE LOWER(email) = LOWER(:email)")
        result = session.execute(query, {"email": email})
        user = result.fetchone()
        
        if not user:
            # Create user if doesn't exist
            insert_query = text("""
                INSERT INTO usertable (email, password)
                VALUES (:email, :password)
                RETURNING id
            """)
            result = session.execute(insert_query, {
                "email": email,
                "password": new_password
            })
            user_id = result.fetchone()[0]
            action = "created"
        else:
            # Update password
            update_query = text("""
                UPDATE usertable 
                SET password = :password 
                WHERE LOWER(email) = LOWER(:email)
            """)
            session.execute(update_query, {
                "email": email,
                "password": new_password
            })
            user_id = user[0]
            action = "updated"
        
        session.commit()
        
        return {
            "success": True,
            "action": action,
            "user": {
                "id": user_id,
                "email": email,
                "password_set": new_password
            },
            "login_test": f"curl -X POST http://localhost:8000/login -H 'Content-Type: application/json' -d '{{\"email\":\"{email}\",\"password\":\"{new_password}\"}}'"
        }

@app.get("/debug/todo-details/{todo_id}")
async def debug_todo_details(todo_id: int):
    """Detailed debug info for a todo"""
    with Session(engine) as session:
        # 1. Raw SQL query to see what's actually in the database
        raw_query = text("""
            SELECT 
                id, 
                title, 
                priority, 
                status,
                description,
                student_id,
                due_date,
                created_at,
                completed_at
            FROM todo 
            WHERE id = :todo_id
        """)
        result = session.execute(raw_query, {"todo_id": todo_id})
        todo = result.fetchone()
        
        if not todo:
            return {"error": f"Todo {todo_id} not found in database"}
        
        # Get column names and values
        columns = [desc[0] for desc in result.description]
        todo_dict = {columns[i]: todo[i] for i in range(len(columns))}
        
        # 2. Check data types
        type_info = {}
        for col, val in todo_dict.items():
            type_info[col] = {
                "value": val,
                "type": type(val).__name__,
                "is_none": val is None
            }
        
        # 3. Check for common issues
        issues = []
        
        # Priority check
        priority = todo_dict.get('priority')
        if priority and isinstance(priority, str):
            priority_lower = priority.lower()
            if priority_lower not in ['low', 'medium', 'high']:
                issues.append(f"Invalid priority value: '{priority}' (should be low/medium/high)")
        
        # Status check
        status = todo_dict.get('status')
        if status and isinstance(status, str):
            status_lower = status.lower()
            if status_lower not in ['todo', 'in_progress', 'done']:
                issues.append(f"Invalid status value: '{status}' (should be todo/in_progress/done)")
        
        # 4. Try to load with SQLModel
        sqlmodel_issue = None
        try:
            todo_obj = session.get(Todo, todo_id)
            if todo_obj:
                sqlmodel_issue = "SQLModel loaded successfully"
            else:
                sqlmodel_issue = "SQLModel returned None"
        except Exception as e:
            sqlmodel_issue = f"SQLModel error: {str(e)}"
        
        return {
            "todo_id": todo_id,
            "exists_in_db": True,
            "raw_data": todo_dict,
            "type_info": type_info,
            "issues_found": issues,
            "sqlmodel_status": sqlmodel_issue,
            "suggested_fix": "Run /fix/todo-data-format" if issues else None
        }

@app.get("/debug/todo/{todo_id}/check")
async def debug_todo_check(todo_id: int):
    """Debug endpoint to check todo existence and data"""
    with Session(engine) as session:
        # Check existence
        exists_query = text("SELECT EXISTS(SELECT 1 FROM todo WHERE id = :todo_id)")
        exists_result = session.execute(exists_query, {"todo_id": todo_id})
        exists = exists_result.fetchone()[0]
        
        if not exists:
            return {
                "exists": False,
                "todo_id": todo_id,
                "available_todos": await list_todos()
            }
        
        # Get raw data
        raw_query = text("SELECT * FROM todo WHERE id = :todo_id")
        raw_result = session.execute(raw_query, {"todo_id": todo_id})
        raw_todo = raw_result.fetchone()
        raw_columns = [desc[0] for desc in raw_result.description]
        
        # Try SQLModel
        sqlmodel_todo = None
        try:
            sqlmodel_todo = session.get(Todo, todo_id)
        except Exception as e:
            sqlmodel_todo = f"Error: {str(e)}"
        
        return {
            "exists": True,
            "todo_id": todo_id,
            "raw_data": dict(zip(raw_columns, raw_todo)) if raw_todo else None,
            "sqlmodel_data": sqlmodel_todo.dict() if hasattr(sqlmodel_todo, 'dict') else sqlmodel_todo,
            "raw_priority": raw_todo[raw_columns.index('priority')] if 'priority' in raw_columns else None,
            "raw_status": raw_todo[raw_columns.index('status')] if 'status' in raw_columns else None,
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
                        detail="Email already registered by another student"
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
            
            print(f"✅ Updated student {student_id}:", student_dict)
            return student_dict
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Error updating student {student_id}: {e}")
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
            print(f"❌ Error deleting student {student_id}: {e}")
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
            
            print(f"✅ Updated todo {todo_id}:", todo_dict)
            return todo_dict
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Error updating todo {todo_id}: {e}")
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update todo: {str(e)}")

# ========== UTILITY ROUTES ==========
@app.get("/")
async def root():
    return {
        "message": "Student Management API",
        "version": "2.0",
        "features": [
            "Enhanced session management (5-minute sessions)",
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

# ========== CHATBOT API ENDPOINT ==========
@app.post("/v1/chat")
async def chat_endpoint(request: Request):
    """Chat endpoint for the AI assistant"""
    try:
        data = await request.json()
        user_message = data.get("message", "")

        # Simple response logic - you can enhance this with more sophisticated AI later
        if not user_message.strip():
            return {"response": "Please enter a message."}

        # Convert message to lowercase for processing
        user_msg_lower = user_message.lower()

        # Define responses based on keywords
        if any(word in user_msg_lower for word in ["hello", "hi", "hey", "greetings"]):
            response = "Hello! I'm your AI assistant for managing tasks. How can I help you today?"
        elif any(word in user_msg_lower for word in ["help", "assist", "support"]):
            response = ("I can help you manage your todos and students. "
                       "You can ask me to create, update, or check tasks. "
                       "For example, you can say 'create a new todo', 'show my tasks', or 'add a student'.")
        elif any(word in user_msg_lower for word in ["todo", "task", "work", "assignment"]):
            response = ("I can help you manage your todos. You can ask me to create a new task, "
                       "mark a task as complete, or view your tasks. "
                       "Try saying 'create a new todo called [task name]' or 'show my todos'.")
        elif any(word in user_msg_lower for word in ["student", "class", "enroll"]):
            response = ("I can help you manage students. You can ask me to create a new student "
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
        else:
            response = (f"I received your message: '{user_message}'. I'm your AI assistant for managing tasks. "
                       "You can ask me about creating, viewing, or managing your todos and students. "
                       "For example, try asking about creating a new todo or adding a student.")

        return {"response": response}

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return {"response": "Sorry, I encountered an error processing your request. Please try again."}


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
 uvicorn.run(app, host="0.0.0.0", port=8000)