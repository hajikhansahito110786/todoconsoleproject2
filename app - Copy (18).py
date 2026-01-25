from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlmodel import Field, Session, SQLModel, create_engine, select, text
import os
from dotenv import load_dotenv
import time
import socket
import hashlib
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Database configuration with SSL fix for Neon
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./student_chat.db")

# Add SSL mode if using Neon PostgreSQL
if "neon.tech" in DATABASE_URL and "sslmode" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# ========== LIFECYCLE MANAGER ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan for startup and shutdown"""
    print("\n" + "="*70)
    print("🚀 STUDENT MANAGEMENT CHAT BACKEND v3.3")
    print("="*70)
    
    # Create tables on startup
    create_tables()
    
    print("✅ Database initialized")
    print("✅ Audit tracking enabled")
    print("✅ Ready to accept requests")
    print("="*70)
    
    yield
    
    print("\n" + "="*70)
    print("🛑 Shutting down backend...")
    print("="*70)

# ========== AUDIT LOGGING ==========
def get_client_info(request: Request) -> dict:
    """Extract client information from request"""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Get computer name
    computer_name = "unknown"
    try:
        computer_name = socket.gethostname()
    except:
        fingerprint_data = f"{client_ip}-{user_agent}"
        computer_name = hashlib.md5(fingerprint_data.encode()).hexdigest()[:8]
    
    return {
        "ip_address": client_ip,
        "user_agent": user_agent,
        "computer_name": computer_name,
        "timestamp": datetime.now(timezone.utc)
    }

def log_audit_action(
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    details: Optional[str] = None,
    user_id: Optional[str] = None,
    request: Optional[Request] = None
):
    """Log an action to audit trail"""
    try:
        client_info = get_client_info(request) if request else {
            "ip_address": "system",
            "user_agent": "system",
            "computer_name": "system",
            "timestamp": datetime.now(timezone.utc)
        }
        
        with Session(engine) as session:
            audit_query = text("""
                INSERT INTO audit_log (
                    action, resource_type, resource_id, details,
                    user_id, ip_address, user_agent, computer_name, timestamp
                ) VALUES (
                    :action, :resource_type, :resource_id, :details,
                    :user_id, :ip_address, :user_agent, :computer_name, :timestamp
                )
            """)
            
            session.execute(audit_query, {
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details,
                "user_id": user_id,
                "ip_address": client_info["ip_address"],
                "user_agent": client_info["user_agent"],
                "computer_name": client_info["computer_name"],
                "timestamp": client_info["timestamp"]
            })
            session.commit()
            
            print(f"[AUDIT] {action} on {resource_type}:{resource_id} by {user_id or 'unknown'} from {client_info['ip_address']}")
            
    except Exception as e:
        print(f"[AUDIT ERROR] Failed to log action: {e}")

def get_audit_history(resource_type: str, resource_id: int) -> List[Dict[str, Any]]:
    """Get audit history for a specific resource"""
    try:
        with Session(engine) as session:
            query = text("""
                SELECT action, details, user_id, ip_address, computer_name, timestamp
                FROM audit_log 
                WHERE resource_type = :resource_type AND resource_id = :resource_id
                ORDER BY timestamp DESC
            """)
            result = session.execute(query, {
                "resource_type": resource_type,
                "resource_id": resource_id
            })
            logs = result.fetchall()
            
            audit_history = []
            for log in logs:
                action, details, user_id, ip_address, computer_name, timestamp = log
                
                # Format timestamp
                if timestamp and hasattr(timestamp, 'strftime'):
                    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    timestamp_str = str(timestamp)
                
                # Parse user info
                user_info = "Unknown"
                if user_id:
                    if "@" in user_id:
                        computer, ip = user_id.split("@")
                        user_info = f"{computer} ({ip})"
                    else:
                        user_info = user_id
                
                audit_history.append({
                    "action": action,
                    "details": details,
                    "user": user_info,
                    "ip_address": ip_address,
                    "computer_name": computer_name,
                    "timestamp": timestamp,
                    "timestamp_formatted": timestamp_str
                })
            
            return audit_history
    except Exception as e:
        print(f"Error getting audit history: {e}")
        return []

# ========== REQUEST MODELS ==========
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None

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
    completed_at: Optional[datetime] = None

# ========== DATABASE FUNCTIONS ==========
def create_tables():
    """Create all necessary tables if they don't exist"""
    try:
        with Session(engine) as session:
            # Test connection first
            session.execute(text("SELECT 1"))
            print("[SUCCESS] Connected to database")

            print("🔄 Creating tables if needed...")

            # Create student table (with both name and nameplz support)
            try:
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS student (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255),
                        nameplz VARCHAR(255),
                        email VARCHAR(255) UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by VARCHAR(255),
                        updated_by VARCHAR(255),
                        last_ip_address VARCHAR(50),
                        last_user_agent TEXT
                    )
                """))
                print("[SUCCESS] Created/verified student table")
            except Exception as e:
                print(f"[WARNING] Student table error: {e}")

            # Create todo table
            try:
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS todo (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        description TEXT,
                        priority VARCHAR(50) DEFAULT 'medium',
                        status VARCHAR(50) DEFAULT 'todo',
                        due_date TIMESTAMP,
                        student_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by VARCHAR(255),
                        updated_by VARCHAR(255),
                        last_ip_address VARCHAR(50),
                        last_user_agent TEXT
                    )
                """))
                print("[SUCCESS] Created/verified todo table")
            except Exception as e:
                print(f"[WARNING] Todo table error: {e}")

            # Create audit_log table
            try:
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id SERIAL PRIMARY KEY,
                        action VARCHAR(100) NOT NULL,
                        resource_type VARCHAR(100) NOT NULL,
                        resource_id INTEGER,
                        details TEXT,
                        user_id VARCHAR(100),
                        ip_address VARCHAR(50),
                        user_agent TEXT,
                        computer_name VARCHAR(100),
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                print("[SUCCESS] Created/verified audit_log table")
            except Exception as e:
                print(f"[WARNING] Audit log table error: {e}")

            session.commit()
            
    except Exception as e:
        print(f"[ERROR] Database setup error: {e}")
        print("[WARNING] Continuing with existing tables...")

# ========== DATA FETCHING FUNCTIONS ==========
def get_todo_counts():
    """Get todo statistics from database"""
    try:
        with Session(engine) as session:
            # Total todos
            total_query = text("SELECT COUNT(*) FROM todo")
            total_result = session.execute(total_query)
            total_todos = total_result.scalar() or 0
            
            # Todos by status
            status_query = text("""
                SELECT status, COUNT(*) as count 
                FROM todo 
                GROUP BY status
            """)
            status_result = session.execute(status_query)
            status_counts = {row[0]: row[1] for row in status_result.fetchall()}
            
            # Todos by priority
            priority_query = text("""
                SELECT priority, COUNT(*) as count 
                FROM todo 
                GROUP BY priority
            """)
            priority_result = session.execute(priority_query)
            priority_counts = {row[0]: row[1] for row in priority_result.fetchall()}
            
            # Student count
            student_query = text("SELECT COUNT(*) FROM student")
            student_result = session.execute(student_query)
            student_count = student_result.scalar() or 0
            
            return {
                "total": total_todos,
                "by_status": status_counts,
                "by_priority": priority_counts,
                "students": student_count
            }
    except Exception as e:
        print(f"Database error in get_todo_counts: {e}")
        return {
            "total": 0,
            "by_status": {},
            "by_priority": {},
            "students": 0
        }

def get_students_list():
    """Get students from database with COALESCE for name/nameplz"""
    try:
        with Session(engine) as session:
            query = text("""
                SELECT 
                    id, 
                    COALESCE(name, nameplz) as name, 
                    email, 
                    created_at, 
                    updated_at,
                    created_by, 
                    updated_by, 
                    last_ip_address, 
                    last_user_agent
                FROM student 
                ORDER BY created_at DESC
            """)
            result = session.execute(query)
            students = result.fetchall()
            
            formatted_students = []
            for student in students:
                student_id, name, email, created_at, updated_at, created_by, updated_by, last_ip, last_ua = student
                
                # Format timestamps
                created_at_str = created_at.strftime('%Y-%m-%d %H:%M') if created_at and hasattr(created_at, 'strftime') else str(created_at)[:16]
                updated_at_str = updated_at.strftime('%Y-%m-%d %H:%M') if updated_at and hasattr(updated_at, 'strftime') else str(updated_at)[:16]
                
                # Parse user info
                creator_info = "System"
                if created_by:
                    if "@" in created_by:
                        computer, ip = created_by.split("@")
                        creator_info = f"{computer} ({ip})"
                    else:
                        creator_info = created_by
                
                updater_info = "Not updated yet"
                if updated_by:
                    if "@" in updated_by:
                        computer, ip = updated_by.split("@")
                        updater_info = f"{computer} ({ip})"
                    else:
                        updater_info = updated_by
                
                # Get audit history
                audit_history = get_audit_history("student", student_id)
                
                formatted_students.append({
                    "id": student_id,
                    "name": name or "Unnamed",
                    "email": email,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "created_by": created_by or "System",
                    "updated_by": updated_by or "System",
                    "creator_info": creator_info,
                    "updater_info": updater_info,
                    "last_ip_address": last_ip,
                    "last_user_agent": last_ua,
                    "created_at_formatted": created_at_str,
                    "updated_at_formatted": updated_at_str,
                    "audit_history": audit_history[:5],
                    "total_audit_entries": len(audit_history)
                })
            
            return formatted_students
    except Exception as e:
        print(f"Database error in get_students_list: {e}")
        return []

def get_todos_list():
    """Get todos from database with audit info"""
    try:
        with Session(engine) as session:
            query = text("""
                SELECT 
                    t.id, t.title, t.description, t.priority, t.status,
                    t.due_date, t.student_id, t.created_at, t.completed_at,
                    t.updated_at, t.created_by, t.updated_by,
                    t.last_ip_address, t.last_user_agent,
                    COALESCE(s.name, s.nameplz) as student_name, 
                    s.email as student_email
                FROM todo t
                LEFT JOIN student s ON t.student_id = s.id
                ORDER BY t.created_at DESC
            """)
            result = session.execute(query)
            todos = result.fetchall()
            
            formatted_todos = []
            for todo in todos:
                todo_id, title, description, priority, status, due_date, student_id, created_at, completed_at, updated_at, created_by, updated_by, last_ip, last_ua, student_name, student_email = todo
                
                # Format timestamps
                created_at_str = created_at.strftime('%Y-%m-%d %H:%M') if created_at and hasattr(created_at, 'strftime') else str(created_at)[:16]
                updated_at_str = updated_at.strftime('%Y-%m-%d %H:%M') if updated_at and hasattr(updated_at, 'strftime') else str(updated_at)[:16]
                completed_at_str = completed_at.strftime('%Y-%m-%d %H:%M') if completed_at and hasattr(completed_at, 'strftime') else str(completed_at)[:16] if completed_at else None
                
                # Parse user info
                creator_info = "System"
                if created_by:
                    if "@" in created_by:
                        computer, ip = created_by.split("@")
                        creator_info = f"{computer} ({ip})"
                    else:
                        creator_info = created_by
                
                updater_info = "Not updated yet"
                if updated_by:
                    if "@" in updated_by:
                        computer, ip = updated_by.split("@")
                        updater_info = f"{computer} ({ip})"
                    else:
                        updater_info = updated_by
                
                # Get audit history
                audit_history = get_audit_history("todo", todo_id)
                
                formatted_todos.append({
                    "id": todo_id,
                    "title": title,
                    "description": description,
                    "priority": priority,
                    "status": status,
                    "due_date": due_date,
                    "student_id": student_id,
                    "student_name": student_name,
                    "student_email": student_email,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "completed_at": completed_at,
                    "created_by": created_by or "System",
                    "updated_by": updated_by or "System",
                    "creator_info": creator_info,
                    "updater_info": updater_info,
                    "last_ip_address": last_ip,
                    "last_user_agent": last_ua,
                    "created_at_formatted": created_at_str,
                    "updated_at_formatted": updated_at_str,
                    "completed_at_formatted": completed_at_str,
                    "audit_history": audit_history[:5],
                    "total_audit_entries": len(audit_history)
                })
            
            return formatted_todos
    except Exception as e:
        print(f"Database error in get_todos_list: {e}")
        return []

def get_recent_audit_logs(limit=10):
    """Get recent audit logs"""
    try:
        with Session(engine) as session:
            query = text("""
                SELECT id, action, resource_type, resource_id, details,
                       user_id, ip_address, computer_name, timestamp
                FROM audit_log 
                ORDER BY timestamp DESC 
                LIMIT :limit
            """)
            result = session.execute(query, {"limit": limit})
            logs = result.fetchall()
            
            formatted_logs = []
            for log in logs:
                formatted_logs.append({
                    "id": log[0],
                    "action": log[1],
                    "resource_type": log[2],
                    "resource_id": log[3],
                    "details": log[4],
                    "user_id": log[5] or "Anonymous",
                    "ip_address": log[6],
                    "computer_name": log[7],
                    "timestamp": log[8]
                })
            return formatted_logs
    except Exception as e:
        print(f"Database error in get_recent_audit_logs: {e}")
        return []

# ========== FASTAPI APP ==========
app = FastAPI(lifespan=lifespan)

# ========== CORS CONFIGURATION ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3000/",
        "http://127.0.0.1:3000/"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# ========== REQUEST LOGGING MIDDLEWARE ==========
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = time.time()
    
    # Handle preflight OPTIONS requests
    if request.method == "OPTIONS":
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response
    
    try:
        response = await call_next(request)
    except Exception as e:
        print(f"[ERROR] {request.method} {request.url.path} - {str(e)[:100]}")
        from fastapi.responses import JSONResponse
        error_response = JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)[:200]}
        )
        error_response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
        error_response.headers["Access-Control-Allow-Credentials"] = "true"
        return error_response
    
    process_time = time.time() - start_time
    
    # Add CORS headers to all responses
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response

# ========== STUDENT ROUTES ==========
@app.get("/students/")
async def list_students():
    """List all students with audit info"""
    print("📋 Getting students list with audit info...")
    try:
        students = get_students_list()
        print(f"✅ Found {len(students)} students")
        return students
    except Exception as e:
        print(f"❌ Error getting students: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get students: {str(e)}")

@app.get("/students")
async def list_students_no_slash():
    """List all students (without slash)"""
    return await list_students()

@app.get("/students/{student_id}/audit")
async def get_student_audit(student_id: int):
    """Get audit history for a specific student"""
    try:
        audit_history = get_audit_history("student", student_id)
        return {
            "student_id": student_id,
            "audit_history": audit_history,
            "total_entries": len(audit_history),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit history: {str(e)}")

@app.post("/students/")
async def create_student(request: StudentCreate, api_request: Request):
    """Create a new student with full audit tracking"""
    print(f"📝 Creating student: {request.name} ({request.email})")
    
    # Extract user info
    client_info = get_client_info(api_request)
    user_identifier = f"{client_info['computer_name']}@{client_info['ip_address']}"
    
    with Session(engine) as session:
        try:
            # Check if email already exists
            query = text("SELECT email FROM student WHERE email = :email")
            result = session.execute(query, {"email": request.email})
            existing = result.fetchone()

            if existing:
                raise HTTPException(status_code=400, detail="Email already registered")

            # Create student with full audit info
            insert_query = text("""
                INSERT INTO student (
                    name, nameplz, email, created_at, updated_at, 
                    created_by, updated_by, last_ip_address, last_user_agent
                ) VALUES (
                    :name, :nameplz, :email, :created_at, :updated_at,
                    :created_by, :updated_by, :last_ip_address, :last_user_agent
                )
                RETURNING id, name, email, created_at
            """)

            result = session.execute(insert_query, {
                "name": request.name,  # Store in both name and nameplz
                "nameplz": request.name,
                "email": request.email,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "created_by": user_identifier,
                "updated_by": user_identifier,
                "last_ip_address": client_info["ip_address"],
                "last_user_agent": client_info["user_agent"]
            })
            student = result.fetchone()
            session.commit()

            # Log the action
            log_audit_action(
                action="CREATE_STUDENT",
                resource_type="student",
                resource_id=student[0],
                details=f"Created student: '{request.name}' with email '{request.email}'",
                user_id=user_identifier,
                request=api_request
            )

            print(f"✅ Student created with ID: {student[0]}")
            return {
                "id": student[0],
                "name": student[1],
                "email": student[2],
                "created_at": student[3],
                "created_by": user_identifier,
                "ip_address": client_info["ip_address"],
                "computer_name": client_info["computer_name"]
            }

        except Exception as e:
            print(f"❌ Error creating student: {e}")
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create student: {str(e)}")

@app.post("/students")
async def create_student_no_slash(request: StudentCreate, api_request: Request):
    """Create a new student (without slash)"""
    return await create_student(request, api_request)

# ========== TODO ROUTES ==========
@app.get("/todos/")
async def list_todos():
    """List all todos with audit info"""
    print("📋 Getting todos list with audit info...")
    try:
        todos = get_todos_list()
        print(f"✅ Found {len(todos)} todos")
        return todos
    except Exception as e:
        print(f"❌ Error getting todos: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get todos: {str(e)}")

@app.get("/todos")
async def list_todos_no_slash():
    """List all todos (without slash)"""
    return await list_todos()

@app.get("/todos/{todo_id}/audit")
async def get_todo_audit(todo_id: int):
    """Get audit history for a specific todo"""
    try:
        audit_history = get_audit_history("todo", todo_id)
        return {
            "todo_id": todo_id,
            "audit_history": audit_history,
            "total_entries": len(audit_history),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit history: {str(e)}")

@app.post("/todos/")
async def create_todo(request: TodoCreate, api_request: Request):
    """Create a new todo with full audit tracking"""
    print(f"📝 Creating todo: {request.title}")
    
    # Extract user info
    client_info = get_client_info(api_request)
    user_identifier = f"{client_info['computer_name']}@{client_info['ip_address']}"
    
    with Session(engine) as session:
        try:
            # Check if student exists (if student_id is provided)
            if request.student_id:
                student_query = text("SELECT id FROM student WHERE id = :student_id")
                student_result = session.execute(student_query, {"student_id": request.student_id})
                student = student_result.fetchone()
                
                if not student:
                    raise HTTPException(status_code=404, detail=f"Student with ID {request.student_id} not found")

            # Create todo with full audit info
            insert_query = text("""
                INSERT INTO todo (
                    title, description, priority, status, due_date, 
                    student_id, created_at, updated_at,
                    created_by, updated_by, last_ip_address, last_user_agent
                ) VALUES (
                    :title, :description, :priority, :status, :due_date,
                    :student_id, :created_at, :updated_at,
                    :created_by, :updated_by, :last_ip_address, :last_user_agent
                )
                RETURNING id
            """)

            result = session.execute(insert_query, {
                "title": request.title,
                "description": request.description,
                "priority": request.priority.lower(),
                "status": request.status.lower(),
                "due_date": request.due_date,
                "student_id": request.student_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "created_by": user_identifier,
                "updated_by": user_identifier,
                "last_ip_address": client_info["ip_address"],
                "last_user_agent": client_info["user_agent"]
            })
            todo_id = result.scalar()
            session.commit()

            # Log the action
            log_audit_action(
                action="CREATE_TODO",
                resource_type="todo",
                resource_id=todo_id,
                details=f"Created todo: '{request.title}' with priority {request.priority}, status {request.status}" +
                       (f" (Assigned to student {request.student_id})" if request.student_id else ""),
                user_id=user_identifier,
                request=api_request
            )

            print(f"✅ Todo created with ID: {todo_id} by {user_identifier}")
            
            # Return the created todo with audit info
            todo = await get_todo_with_audit(todo_id)
            return todo

        except Exception as e:
            print(f"❌ Error creating todo: {e}")
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create todo: {str(e)}")

async def get_todo_with_audit(todo_id: int):
    """Get a single todo by ID with audit info"""
    try:
        todos = get_todos_list()
        for todo in todos:
            if todo["id"] == todo_id:
                return todo
        raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get todo: {str(e)}")

@app.get("/todos/{todo_id}")
async def get_todo(todo_id: int):
    """Get a single todo by ID"""
    return await get_todo_with_audit(todo_id)

@app.post("/todos")
async def create_todo_no_slash(request: TodoCreate, api_request: Request):
    """Create a new todo (without slash)"""
    return await create_todo(request, api_request)

@app.put("/todos/{todo_id}")
async def update_todo(todo_id: int, request: TodoUpdate, api_request: Request):
    """Update a todo with audit logging"""
    print(f"📝 Updating todo {todo_id}")
    
    # Extract user info
    client_info = get_client_info(api_request)
    user_identifier = f"{client_info['computer_name']}@{client_info['ip_address']}"
    
    with Session(engine) as session:
        try:
            # 1. Check if todo exists
            check_query = text("SELECT id, title FROM todo WHERE id = :todo_id")
            check_result = session.execute(check_query, {"todo_id": todo_id})
            todo_record = check_result.fetchone()
            
            if not todo_record:
                raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")

            old_title = todo_record[1]

            # 2. Check if student exists (if updating student_id)
            if request.student_id is not None:
                student_query = text("SELECT id FROM student WHERE id = :student_id")
                student_result = session.execute(student_query, {"student_id": request.student_id})
                student = student_result.fetchone()
                
                if not student and request.student_id != 0:  # 0 means unassign
                    raise HTTPException(status_code=404, detail=f"Student with ID {request.student_id} not found")

            # 3. Build update query dynamically
            update_fields = ["updated_at = :updated_at", "updated_by = :updated_by"]
            params = {"todo_id": todo_id, "updated_at": datetime.now(timezone.utc), "updated_by": user_identifier}

            # Track changes for audit log
            changes = []

            # Add updated fields
            if request.title is not None:
                update_fields.append("title = :title")
                params["title"] = request.title
                changes.append(f"title: '{old_title}' → '{request.title}'")
            
            if request.description is not None:
                update_fields.append("description = :description")
                params["description"] = request.description
                changes.append("description updated")
            
            if request.priority is not None:
                update_fields.append("priority = :priority")
                params["priority"] = request.priority.lower()
                changes.append(f"priority: {request.priority}")
            
            if request.status is not None:
                update_fields.append("status = :status")
                params["status"] = request.status.lower()
                changes.append(f"status: {request.status}")
                
                # Set completed_at if status is 'done'
                if request.status.lower() == 'done':
                    update_fields.append("completed_at = :completed_at")
                    params["completed_at"] = datetime.now(timezone.utc)
                elif request.status.lower() != 'done':
                    update_fields.append("completed_at = NULL")
            
            if request.due_date is not None:
                update_fields.append("due_date = :due_date")
                params["due_date"] = request.due_date
                changes.append(f"due_date: {request.due_date}")
            
            if request.student_id is not None:
                if request.student_id == 0:  # Unassign student
                    update_fields.append("student_id = NULL")
                    changes.append("student unassigned")
                else:
                    update_fields.append("student_id = :student_id")
                    params["student_id"] = request.student_id
                    changes.append(f"assigned to student_id: {request.student_id}")
            
            if request.completed_at is not None:
                update_fields.append("completed_at = :completed_at")
                params["completed_at"] = request.completed_at
                changes.append(f"completed_at: {request.completed_at}")

            if len(update_fields) <= 2:  # Only updated_at and updated_by
                raise HTTPException(status_code=400, detail="No fields to update")

            # 4. Execute update
            update_query = text(f"""
                UPDATE todo
                SET {', '.join(update_fields)}
                WHERE id = :todo_id
                RETURNING id
            """)

            session.execute(update_query, params)
            session.commit()

            # 5. Log the action
            log_audit_action(
                action="UPDATE_TODO",
                resource_type="todo",
                resource_id=todo_id,
                details=f"Updated todo #{todo_id}: {', '.join(changes) if changes else 'No changes specified'}",
                user_id=user_identifier,
                request=api_request
            )

            # 6. Return updated todo
            return await get_todo(todo_id)

        except HTTPException:
            raise
        except Exception as e:
            print(f"[ERROR] Error updating todo {todo_id}: {e}")
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update todo: {str(e)}")

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int, api_request: Request):
    """Delete a todo with audit logging"""
    # Extract user info
    client_info = get_client_info(api_request)
    user_identifier = f"{client_info['computer_name']}@{client_info['ip_address']}"
    
    with Session(engine) as session:
        try:
            # First get todo details for audit log
            get_query = text("SELECT title FROM todo WHERE id = :todo_id")
            get_result = session.execute(get_query, {"todo_id": todo_id})
            todo = get_result.fetchone()
            
            if not todo:
                raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")
            
            todo_title = todo[0]

            # Delete the todo
            delete_query = text("DELETE FROM todo WHERE id = :todo_id")
            session.execute(delete_query, {"todo_id": todo_id})
            session.commit()

            # Log the action
            log_audit_action(
                action="DELETE_TODO",
                resource_type="todo",
                resource_id=todo_id,
                details=f"Deleted todo: '{todo_title}' (ID: {todo_id})",
                user_id=user_identifier,
                request=api_request
            )

            return {
                "success": True,
                "message": f"Todo '{todo_title}' deleted successfully",
                "todo_id": todo_id
            }

        except HTTPException:
            raise
        except Exception as e:
            session.rollback()
            print(f"[ERROR] Error deleting todo {todo_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete todo: {str(e)}")

# ========== AUDIT LOG ENDPOINTS ==========
@app.get("/audit-logs")
async def get_audit_logs(limit: int = 50, page: int = 1):
    """Get all audit logs"""
    try:
        with Session(engine) as session:
            offset = (page - 1) * limit
            query = text("""
                SELECT id, action, resource_type, resource_id, details,
                       user_id, ip_address, computer_name, timestamp
                FROM audit_log 
                ORDER BY timestamp DESC 
                LIMIT :limit OFFSET :offset
            """)
            result = session.execute(query, {"limit": limit, "offset": offset})
            logs = result.fetchall()
            
            # Count total logs
            count_query = text("SELECT COUNT(*) FROM audit_log")
            total_count = session.execute(count_query).scalar() or 0
            
            formatted_logs = []
            for log in logs:
                log_id, action, resource_type, resource_id, details, user_id, ip_address, computer_name, timestamp = log
                
                # Format timestamp
                if timestamp and hasattr(timestamp, 'strftime'):
                    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    timestamp_str = str(timestamp)
                
                # Parse user info
                user_info = "Unknown"
                if user_id:
                    if "@" in user_id:
                        computer, ip = user_id.split("@")
                        user_info = f"{computer} ({ip})"
                    else:
                        user_info = user_id
                
                formatted_logs.append({
                    "id": log_id,
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "details": details,
                    "user": user_info,
                    "user_id": user_id,
                    "ip_address": ip_address,
                    "computer_name": computer_name,
                    "timestamp": timestamp,
                    "timestamp_formatted": timestamp_str
                })
            
            return {
                "logs": formatted_logs,
                "total": total_count,
                "page": page,
                "limit": limit,
                "pages": (total_count + limit - 1) // limit
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit logs: {str(e)}")

@app.get("/recent-activity")
async def get_recent_activity(limit: int = 20):
    """Get recent user activity across the system"""
    try:
        # Get recent audit logs
        with Session(engine) as session:
            query = text("""
                SELECT id, action, resource_type, resource_id, details,
                       user_id, ip_address, computer_name, timestamp
                FROM audit_log 
                ORDER BY timestamp DESC 
                LIMIT :limit
            """)
            result = session.execute(query, {"limit": limit})
            logs = result.fetchall()
            
            recent_activity = []
            for log in logs:
                log_id, action, resource_type, resource_id, details, user_id, ip_address, computer_name, timestamp = log
                
                # Format timestamp
                if timestamp and hasattr(timestamp, 'strftime'):
                    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M')
                    time_ago = get_time_ago(timestamp)
                else:
                    timestamp_str = str(timestamp)
                    time_ago = "Unknown time ago"
                
                # Parse user info
                user_info = "Unknown"
                if user_id:
                    if "@" in user_id:
                        computer, ip = user_id.split("@")
                        user_info = f"{computer} ({ip})"
                    else:
                        user_info = user_id
                
                # Get emoji for action
                action_emoji = {
                    "CREATE": "🆕",
                    "UPDATE": "✏️",
                    "DELETE": "🗑️",
                    "CREATE_STUDENT": "👨‍🎓",
                    "CREATE_TODO": "📝",
                    "UPDATE_TODO": "✏️",
                    "DELETE_TODO": "🗑️"
                }.get(action, "📋")
                
                recent_activity.append({
                    "id": log_id,
                    "action": action,
                    "action_emoji": action_emoji,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "details": details,
                    "user": user_info,
                    "ip_address": ip_address,
                    "computer_name": computer_name,
                    "timestamp": timestamp,
                    "timestamp_formatted": timestamp_str,
                    "time_ago": time_ago
                })
            
            return {
                "recent_activity": recent_activity,
                "count": len(recent_activity),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent activity: {str(e)}")

def get_time_ago(timestamp: datetime) -> str:
    """Calculate time ago string"""
    now = datetime.now(timezone.utc)
    diff = now - timestamp
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"

# ========== CHAT ENDPOINT ==========
# ========== CHAT ENDPOINT ==========
@app.post("/chat")
async def chat_endpoint(request: ChatRequest, api_request: Request):
    """Chat endpoint that can show audit info"""
    start_time = time.time()  # Add this line at the beginning
    user_msg = request.message.lower()
    
    # Extract user info for audit
    client_info = get_client_info(api_request)
    user_identifier = f"{client_info['computer_name']}@{client_info['ip_address']}"
    
    print(f"[CHAT] {datetime.now().strftime('%H:%M:%S')} - Received: '{request.message}' from {user_identifier}")
    
    # Log chat interaction
    log_audit_action(
        action="CHAT_INTERACTION",
        resource_type="chat",
        details=f"Chat message: '{request.message[:100]}...'",
        user_id=user_identifier,
        request=api_request
    )
    
    # Get real data from database - THIS IS THE KEY FIX
    counts = get_todo_counts()
    students = get_students_list()
    todos = get_todos_list()  # Get todos from database
    
    # Response generation - FIXED VERSION
    if "who created" in user_msg or "who made" in user_msg or "who added" in user_msg:
        if "student" in user_msg:
            if len(students) == 0:
                response = "👨‍🎓 No students found in the system yet."
            else:
                response = "👨‍🎓 **Students and Their Creators:**\n\n"
                for student in students[:10]:  # Show first 10
                    response += f"**{student['name']}** (ID: {student['id']})\n"
                    response += f"   • Created by: {student.get('creator_info', 'Unknown')}\n"
                    response += f"   • Created on: {student.get('created_at_formatted', 'Unknown')}\n"
                    response += f"   • Email: {student['email']}\n\n"
                response += f"📊 Total students: {len(students)}"
        
        elif "todo" in user_msg:
            if len(todos) == 0:
                response = "📝 No todos found in the system yet."
            else:
                response = "📝 **Todos and Their Creators:**\n\n"
                for todo in todos[:10]:  # Show first 10
                    response += f"**{todo['title']}** (ID: {todo['id']})\n"
                    response += f"   • Created by: {todo.get('creator_info', 'Unknown')}\n"
                    response += f"   • Created on: {todo.get('created_at_formatted', 'Unknown')}\n"
                    response += f"   • Status: {todo['status']} | Priority: {todo['priority']}\n"
                    if todo.get('student_name'):
                        response += f"   • Assigned to: {todo['student_name']}\n"
                    response += "\n"
                response += f"📊 Total todos: {len(todos)}"
        
        else:
            response = "🤔 I can tell you who created students or todos. Try asking:\n"
            response += "• 'Who created the students?'\n"
            response += "• 'Who made the todos?'\n"
            response += "• 'Show me recent activity'\n"
    
    elif "recent activity" in user_msg or "what happened" in user_msg:
        try:
            # Get recent activity
            activity_response = await get_recent_activity(10)
            
            if len(activity_response.get("recent_activity", [])) == 0:
                response = "📊 No recent activity found. The system is quiet!"
            else:
                response = "📊 **Recent System Activity:**\n\n"
                for activity in activity_response["recent_activity"][:10]:
                    response += f"{activity.get('action_emoji', '📋')} **{activity.get('action', 'Unknown').replace('_', ' ')}**\n"
                    response += f"   • Resource: {activity.get('resource_type', 'Unknown')} #{activity.get('resource_id', '?')}\n"
                    response += f"   • User: {activity.get('user', 'Unknown')}\n"
                    response += f"   • Time: {activity.get('time_ago', 'Unknown')}\n"
                    if activity.get('details'):
                        response += f"   • Details: {activity['details'][:80]}...\n"
                    response += "\n"
                
                response += f"📈 Total activities tracked: {activity_response.get('count', 0)}"
        except Exception as e:
            print(f"[CHAT ERROR] Failed to get recent activity: {e}")
            response = "⚠️ Could not retrieve recent activity due to a system error."
    
    elif "hello" in user_msg or "hi" in user_msg or "hey" in user_msg:
        response = f"👋 Hello! I'm your Student Management Assistant. We have {counts['students']} students and {counts['total']} todos in the system."
    
    elif ("show" in user_msg or "list" in user_msg or "view" in user_msg) and "todo" in user_msg:
        if counts['total'] == 0:
            response = "📭 You have no todos yet! Create your first todo by saying 'create todo' or using the 'Add New Todo' button."
        else:
            response = "📋 **Your Recent Todos:**\n\n"
            for todo in todos[:5]:
                status_icon = "📝" if todo["status"] == "todo" else "🔄" if todo["status"] == "in_progress" else "✅"
                priority_icon = "🔴" if todo["priority"] == "high" else "🟡" if todo["priority"] == "medium" else "🟢"
                response += f"{status_icon} **{todo['title']}**\n"
                response += f"   • ID: {todo['id']} | Status: {todo['status']} | Priority: {priority_icon} {todo['priority']}\n"
                if todo.get('description'):
                    response += f"   • Description: {todo['description'][:50]}...\n"
                response += "\n"
            
            response += f"📊 **Statistics:**\n"
            for status, count in counts['by_status'].items():
                response += f"   • {status}: {count}\n"
            
            response += f"\n👨‍🎓 **Students:** {counts['students']}\n"
            response += "💡 **Tip:** Use the 'Todos' page for full management!"
    
    elif "create" in user_msg and "todo" in user_msg:
        response = """🆕 **Create a New Todo**

**Steps:**
1. Go to **Todos** page
2. Click **"Add New Todo"** button (green)
3. Fill in the form:
   - **Title** (required): Brief task description
   - **Description**: Details and instructions
   - **Priority**: 🔴 High / 🟡 Medium / 🟢 Low
   - **Status**: 📝 todo / 🔄 in_progress / ✅ done
   - **Due Date**: Set deadline (optional)
   - **Assign to Student**: Select from dropdown (optional)
4. Click **"Create Todo"**

🎯 Your new todo will appear in the todos list immediately!"""
    
    elif "show" in user_msg and "student" in user_msg:
        if len(students) == 0:
            response = "👨‍🎓 No students found. Add students first!"
        else:
            response = "👨‍🎓 **Students List:**\n\n"
            for student in students[:5]:
                response += f"**{student['name']}**\n"
                response += f"   • Email: {student['email']}\n"
                response += f"   • ID: {student['id']}\n"
                response += f"   • Joined: {student.get('created_at_formatted', 'Unknown')}\n"
                response += "\n"
            
            response += f"📊 **Total Students:** {counts['students']}\n"
            response += "💡 **Tip:** Assign todos to students for better tracking!"
    
    elif "how many" in user_msg and "todo" in user_msg:
        response = f"""📊 **System Statistics**

**Todo Breakdown:**
• Total Todos: {counts['total']}
• By Status: {', '.join([f'{status}: {count}' for status, count in counts['by_status'].items()])}
• By Priority: {', '.join([f'{priority}: {count}' for priority, count in counts['by_priority'].items()])}

**Students:** {counts['students']}

**Completion Rate:** {round((counts['by_status'].get('done', 0) / counts['total'] * 100) if counts['total'] > 0 else 0)}%"""
    
    elif "help" in user_msg or "what can you do" in user_msg:
        response = f"""🆘 **Student Management System Help**

**📊 Current Stats:**
• Students: {counts['students']}
• Todos: {counts['total']}
• System: Online ✅

**🤖 AVAILABLE COMMANDS:**
• "show todo" - View todos with details
• "create todo" - Learn how to add new tasks
• "show students" - View student list
• "how many todos" - See statistics
• "who created the students?" - See creator info
• "who made the todos?" - See creator info
• "recent activity" - View system activity
• "help" - This help message

**📱 APP FEATURES:**
1. **Todo Management** - Create, view, update, delete todos
2. **Student Management** - Add, edit, view students
3. **Audit Tracking** - See who created/updated everything
4. **Progress Tracking** - Monitor completion rates
5. **Priority System** - Organize by importance

What would you like to do?"""
    
    elif "thank" in user_msg:
        response = "You're welcome! 😊 Is there anything else I can help you with regarding student or todo management?"
    
    else:
        response = f"""🤖 **Student Management Assistant**

I understand you asked: *"{request.message}"*

**Quick Help:**
• To manage **todos**: Say "show todo" or "create todo"
• To manage **students**: Say "show students"
• For **statistics**: Say "how many todos"
• For **audit info**: Say "who created the students?" or "who made the todos?"
• For **help**: Say "help"

**Current System Status:**
📊 Todos: {counts['total']} | 👨‍🎓 Students: {counts['students']}

How can I assist you with student management today?"""
    
    # Calculate response time
    response_time = time.time() - start_time
    print(f"[CHAT] Response generated in {response_time:.2f}s")
    
    return {"response": response}

# Add v1 endpoint for frontend compatibility
@app.post("/v1/chat")
async def v1_chat(request: ChatRequest):
    """v1 endpoint for frontend compatibility - SIMPLE VERSION"""
    print(f"[V1 CHAT] Received: '{request.message}'")
    
    # Get basic data
    counts = get_todo_counts()
    
    # Simple response for v1 compatibility
    response = f"""🤖 Student Management Assistant

I understand: "{request.message}"

Current Stats:
• Students: {counts['students']}
• Todos: {counts['total']}

Try asking:
• "Show todos"
• "Show students"
• "How many todos"
• "Help" for more commands"""
    
    return {"response": response}

# Add this endpoint to test chat connectivity
@app.get("/test-chat")
async def test_chat():
    """Test endpoint to verify chat is working"""
    return {
        "status": "chat_ready",
        "message": "Chat endpoint is working",
        "endpoints": {
            "chat": "POST /chat",
            "v1_chat": "POST /v1/chat",
            "test": "GET /test-chat"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ========== HEALTH & TEST ENDPOINTS ==========
@app.get("/health")
async def health():
    """Health check endpoint"""
    counts = get_todo_counts()
    
    # Get recent activity count
    try:
        with Session(engine) as session:
            audit_count_query = text("SELECT COUNT(*) FROM audit_log")
            audit_count = session.execute(audit_count_query).scalar() or 0
    except:
        audit_count = 0
    
    return {
        "status": "healthy",
        "service": "student-chat-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "3.3",
        "statistics": {
            "students": counts['students'],
            "todos": counts['total'],
            "audit_logs": audit_count
        },
        "features": [
            "Full audit tracking",
            "IP address logging",
            "User identification",
            "Activity monitoring",
            "Dual column support (name/nameplz)"
        ]
    }

@app.get("/test-cors")
async def test_cors(request: Request):
    """Test CORS endpoint"""
    return {
        "message": "CORS test successful!",
        "your_ip": request.client.host if request.client else "unknown",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cors": "enabled",
        "allowed_origins": ["http://localhost:3000", "http://127.0.0.1:3000"]
    }

@app.get("/")
async def root():
    """Root endpoint"""
    counts = get_todo_counts()
    
    return {
        "message": "Student Management API with Audit Tracking",
        "version": "3.3",
        "status": "running",
        "statistics": {
            "students": counts['students'],
            "todos": counts['total']
        },
        "features": [
            "Full audit logging for all actions",
            "IP address tracking",
            "Computer name identification",
            "User action history",
            "Dual column support (name/nameplz) for backward compatibility"
        ],
        "endpoints": {
            "students": [
                "GET /students - List students with creator info",
                "POST /students - Create new student",
                "GET /students/{id}/audit - Student audit history"
            ],
            "todos": [
                "GET /todos - List todos with creator info",
                "POST /todos - Create new todo",
                "GET /todos/{id} - Get single todo",
                "PUT /todos/{id} - Update todo",
                "DELETE /todos/{id} - Delete todo",
                "GET /todos/{id}/audit - Todo audit history"
            ],
            "audit": [
                "GET /audit-logs - All audit logs",
                "GET /recent-activity - Recent system activity"
            ],
            "chat": ["POST /chat", "POST /v1/chat"],
            "monitoring": ["GET /health", "GET /test-cors"]
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 STUDENT MANAGEMENT CHAT BACKEND v3.3 WITH AUDIT TRACKING")
    print("="*70)
    print("🕵️‍♂️ **Audit Tracking Features:**")
    print("  • See who created each student and todo")
    print("  • Track IP addresses and computer names")
    print("  • View complete audit history")
    print("  • Monitor all system activity")
    print("  • Dual column support (name/nameplz)")
    print("\n📡 **Key Endpoints:**")
    print("  • GET  /students - Students with creator info")
    print("  • GET  /todos - Todos with creator info")
    print("  • GET  /audit-logs - All audit logs")
    print("  • GET  /recent-activity - Recent system activity")
    print("\n💬 **Chat Commands:**")
    print("  • 'Who created the students?'")
    print("  • 'Who made the todos?'")
    print("  • 'Show me recent activity'")
    print("="*70)
    print("✅ Starting server...")
    print("="*70)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info"
    )