from fastapi import FastAPI, HTTPException, Request, Header
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
    print("🚀 STUDENT MANAGEMENT CHAT BACKEND v3.6")
    print("📧 FEATURE: User email tracking in database")
    print("🔧 FIX: Error handling for audit history")
    print("="*70)
    
    # Create tables on startup
    create_tables()
    
    print("✅ Database initialized")
    print("✅ Audit tracking enabled")
    print("✅ User email tracking enabled")
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
    
    # Create a unique client identifier
    fingerprint_data = f"{client_ip}-{user_agent}"
    client_id = hashlib.md5(fingerprint_data.encode()).hexdigest()[:12]
    
    return {
        "ip_address": client_ip,
        "user_agent": user_agent,
        "computer_name": f"client-{client_id}",
        "timestamp": datetime.now(timezone.utc)
    }

def get_user_email_from_request(request: Request) -> str:
    """Extract user email from request headers"""
    # Try to get from custom headers (sent by Next.js frontend)
    user_email = request.headers.get("x-user-email", "")
    
    # If no email in headers, use anonymous identifier
    if not user_email:
        client_info = get_client_info(request)
        user_email = f"anonymous@{client_info['computer_name']}"
    
    return user_email

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
            # Try different column combinations
            column_queries = [
                # Try with all columns
                "SELECT action, details, user_id, ip_address, user_agent, computer_name, timestamp",
                # Try without computer_name
                "SELECT action, details, user_id, ip_address, user_agent, timestamp",
                # Try minimal columns
                "SELECT action, details, user_id, timestamp"
            ]
            
            logs = []
            for column_query in column_queries:
                try:
                    query = text(f"""
                        {column_query}
                        FROM audit_log 
                        WHERE resource_type = :resource_type AND resource_id = :resource_id
                        ORDER BY timestamp DESC
                    """)
                    result = session.execute(query, {
                        "resource_type": resource_type,
                        "resource_id": resource_id
                    })
                    logs = result.fetchall()
                    if logs:
                        break  # Use the first successful query
                except Exception as e:
                    continue  # Try next column combination
            
            audit_history = []
            for log in logs:
                # Handle different column counts
                if len(log) == 7:  # All columns
                    action, details, user_id, ip_address, user_agent, computer_name, timestamp = log
                elif len(log) == 6:  # Without computer_name
                    action, details, user_id, ip_address, user_agent, timestamp = log
                    computer_name = "unknown"
                elif len(log) == 4:  # Minimal columns
                    action, details, user_id, timestamp = log
                    ip_address = "unknown"
                    user_agent = "unknown"
                    computer_name = "unknown"
                else:
                    continue  # Skip malformed rows
                
                # Format timestamp
                if timestamp and hasattr(timestamp, 'strftime'):
                    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    timestamp_str = str(timestamp)
                
                # Parse user info
                user_info = "Unknown"
                if user_id:
                    # If it's an email, show just the email
                    if "@" in user_id and "." in user_id:
                        user_info = user_id
                    elif "@" in user_id:
                        computer, ip = user_id.split("@")
                        user_info = f"{computer} ({ip})"
                    else:
                        user_info = user_id
                
                audit_history.append({
                    "action": action,
                    "details": details,
                    "user": user_info,
                    "user_email": user_id if "@" in user_id and "." in user_id else None,
                    "ip_address": ip_address,
                    "computer_name": computer_name,
                    "timestamp": timestamp,
                    "timestamp_formatted": timestamp_str
                })
            
            return audit_history
    except Exception as e:
        print(f"Error getting audit history for {resource_type}:{resource_id}: {e}")
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

            # Create student table
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
                
                # Parse user info - show email if it's an email
                creator_info = "System"
                if created_by:
                    if "@" in created_by and "." in created_by:  # It's an email
                        creator_info = created_by
                    elif "@" in created_by:
                        computer, ip = created_by.split("@")
                        creator_info = f"{computer} ({ip})"
                    else:
                        creator_info = created_by
                
                updater_info = "Not updated yet"
                if updated_by:
                    if "@" in updated_by and "." in updated_by:  # It's an email
                        updater_info = updated_by
                    elif "@" in updated_by:
                        computer, ip = updated_by.split("@")
                        updater_info = f"{computer} ({ip})"
                    else:
                        updater_info = updated_by
                
                # Get audit history - handle errors gracefully
                audit_history = []
                try:
                    audit_history = get_audit_history("student", student_id)
                except Exception as e:
                    print(f"Warning: Could not get audit history for student {student_id}: {e}")
                    audit_history = []
                
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
                    "creator_email": created_by if "@" in created_by and "." in created_by else None,
                    "updater_email": updated_by if "@" in updated_by and "." in updated_by else None,
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
        # Try to get basic student data even if audit fails
        try:
            with Session(engine) as session:
                query = text("""
                    SELECT 
                        id, 
                        COALESCE(name, nameplz) as name, 
                        email, 
                        created_at, 
                        created_by
                    FROM student 
                    ORDER BY created_at DESC
                """)
                result = session.execute(query)
                students = result.fetchall()
                
                return [{
                    "id": s[0],
                    "name": s[1] or "Unnamed",
                    "email": s[2],
                    "created_at": s[3],
                    "created_by": s[4] or "System",
                    "audit_history": []
                } for s in students]
        except:
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
                
                # Format timestamps (FIXED: changed %Y-%m-d to %Y-%m-%d)
                created_at_str = created_at.strftime('%Y-%m-%d %H:%M') if created_at and hasattr(created_at, 'strftime') else str(created_at)[:16]
                updated_at_str = updated_at.strftime('%Y-%m-%d %H:%M') if updated_at and hasattr(updated_at, 'strftime') else str(updated_at)[:16]
                completed_at_str = completed_at.strftime('%Y-%m-%d %H:%M') if completed_at and hasattr(completed_at, 'strftime') else str(completed_at)[:16] if completed_at else None
                
                # Parse user info - show email if it's an email
                creator_info = "System"
                if created_by:
                    if "@" in created_by and "." in created_by:  # It's an email
                        creator_info = created_by
                    elif "@" in created_by:
                        computer, ip = created_by.split("@")
                        creator_info = f"{computer} ({ip})"
                    else:
                        creator_info = created_by
                
                updater_info = "Not updated yet"
                if updated_by:
                    if "@" in updated_by and "." in updated_by:  # It's an email
                        updater_info = updated_by
                    elif "@" in updated_by:
                        computer, ip = updated_by.split("@")
                        updater_info = f"{computer} ({ip})"
                    else:
                        updater_info = updated_by
                
                # Get audit history - handle errors gracefully
                audit_history = []
                try:
                    audit_history = get_audit_history("todo", todo_id)
                except Exception as e:
                    print(f"Warning: Could not get audit history for todo {todo_id}: {e}")
                    audit_history = []
                
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
                    "creator_email": created_by if "@" in created_by and "." in created_by else None,
                    "updater_email": updated_by if "@" in updated_by and "." in updated_by else None,
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
        # Try to get basic todo data even if audit fails
        try:
            with Session(engine) as session:
                query = text("""
                    SELECT 
                        id, title, description, priority, status,
                        created_at, created_by, student_id
                    FROM todo 
                    ORDER BY created_at DESC
                """)
                result = session.execute(query)
                todos = result.fetchall()
                
                return [{
                    "id": t[0],
                    "title": t[1],
                    "description": t[2],
                    "priority": t[3],
                    "status": t[4],
                    "created_at": t[5],
                    "created_by": t[6] or "System",
                    "student_id": t[7],
                    "audit_history": []
                } for t in todos]
        except:
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
        return response
    
    try:
        response = await call_next(request)
    except Exception as e:
        print(f"[ERROR] {request.method} {request.url.path} - {str(e)[:100]}")
        raise
    
    process_time = time.time() - start_time
    
    print(f"[{request.method}] {request.url.path} - {response.status_code} - {process_time:.2f}s")
    
    return response

# ========== STUDENT ROUTES (WITH SLASH) ==========
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

@app.post("/students/")
async def create_student(
    request: StudentCreate, 
    api_request: Request,
    x_user_email: Optional[str] = Header(None, alias="x-user-email")
):
    """Create a new student with full audit tracking"""
    print(f"📝 Creating student: {request.name} ({request.email})")
    
    # Get user email from headers or request
    user_email = x_user_email or api_request.headers.get("x-user-email") or get_user_email_from_request(api_request)
    
    # Extract client info
    client_info = get_client_info(api_request)
    
    # Use user email as identifier if available, otherwise use computer identifier
    user_identifier = user_email if "@" in user_email and "." in user_email else f"{client_info['computer_name']}@{client_info['ip_address']}"
    
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
                "name": request.name,
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

            print(f"✅ Student created with ID: {student[0]} by {user_identifier}")
            return {
                "id": student[0],
                "name": student[1],
                "email": student[2],
                "created_at": student[3],
                "created_by": user_identifier,
                "creator_email": user_identifier if "@" in user_identifier and "." in user_identifier else None,
                "ip_address": client_info["ip_address"],
                "computer_name": client_info["computer_name"]
            }

        except Exception as e:
            print(f"❌ Error creating student: {e}")
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create student: {str(e)}")

# ========== STUDENT ROUTES (WITHOUT SLASH) ==========
@app.get("/students")
async def list_students_no_slash():
    """List all students (without slash)"""
    return await list_students()

@app.post("/students")
async def create_student_no_slash(
    request: StudentCreate, 
    api_request: Request,
    x_user_email: Optional[str] = Header(None, alias="x-user-email")
):
    """Create a new student (without slash)"""
    return await create_student(request, api_request, x_user_email)

# ========== SINGLE STUDENT ENDPOINTS ==========
@app.get("/students/{student_id}")
async def get_student(student_id: int):
    """Get a single student by ID"""
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
                WHERE id = :student_id
            """)
            result = session.execute(query, {"student_id": student_id})
            student = result.fetchone()
            
            if not student:
                raise HTTPException(status_code=404, detail="Student not found")
            
            student_id, name, email, created_at, updated_at, created_by, updated_by, last_ip, last_ua = student
            
            # Format timestamps
            created_at_str = created_at.strftime('%Y-%m-%d %H:%M') if created_at and hasattr(created_at, 'strftime') else str(created_at)[:16]
            updated_at_str = updated_at.strftime('%Y-%m-%d %H:%M') if updated_at and hasattr(updated_at, 'strftime') else str(updated_at)[:16]
            
            return {
                "id": student_id,
                "name": name or "Unnamed",
                "email": email,
                "created_at": created_at,
                "updated_at": updated_at,
                "created_by": created_by or "System",
                "updated_by": updated_by or "System",
                "last_ip_address": last_ip,
                "last_user_agent": last_ua,
                "created_at_formatted": created_at_str,
                "updated_at_formatted": updated_at_str
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get student: {str(e)}")

@app.put("/students/{student_id}")
async def update_student(
    student_id: int,
    request: StudentCreate,
    api_request: Request,
    x_user_email: Optional[str] = Header(None, alias="x-user-email")
):
    """Update a student with audit logging"""
    print(f"📝 Updating student {student_id}")
    
    # Get user email from headers or request
    user_email = x_user_email or api_request.headers.get("x-user-email") or get_user_email_from_request(api_request)
    
    # Extract client info
    client_info = get_client_info(api_request)
    
    # Use user email as identifier if available
    user_identifier = user_email if "@" in user_email and "." in user_email else f"{client_info['computer_name']}@{client_info['ip_address']}"
    
    with Session(engine) as session:
        try:
            # Check if student exists
            check_query = text("SELECT id, name, email FROM student WHERE id = :student_id")
            check_result = session.execute(check_query, {"student_id": student_id})
            student_record = check_result.fetchone()
            
            if not student_record:
                raise HTTPException(status_code=404, detail=f"Student {student_id} not found")

            old_name, old_email = student_record[1], student_record[2]
            
            # Update student
            update_query = text("""
                UPDATE student
                SET name = :name, nameplz = :name, email = :email,
                    updated_at = :updated_at, updated_by = :updated_by,
                    last_ip_address = :last_ip_address, last_user_agent = :last_user_agent
                WHERE id = :student_id
                RETURNING id
            """)
            
            result = session.execute(update_query, {
                "student_id": student_id,
                "name": request.name,
                "email": request.email,
                "updated_at": datetime.now(timezone.utc),
                "updated_by": user_identifier,
                "last_ip_address": client_info["ip_address"],
                "last_user_agent": client_info["user_agent"]
            })
            session.commit()

            # Log the action
            log_audit_action(
                action="UPDATE_STUDENT",
                resource_type="student",
                resource_id=student_id,
                details=f"Updated student #{student_id}: '{old_name}' ({old_email}) → '{request.name}' ({request.email})",
                user_id=user_identifier,
                request=api_request
            )

            print(f"✅ Student {student_id} updated by {user_identifier}")
            return {
                "success": True,
                "message": f"Student '{request.name}' updated successfully",
                "student_id": student_id,
                "updated_by": user_identifier,
                "updater_email": user_identifier if "@" in user_identifier and "." in user_identifier else None
            }

        except Exception as e:
            print(f"❌ Error updating student: {e}")
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update student: {str(e)}")

# ========== TODO ROUTES (WITH SLASH) ==========
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

@app.post("/todos/")
async def create_todo(
    request: TodoCreate, 
    api_request: Request,
    x_user_email: Optional[str] = Header(None, alias="x-user-email")
):
    """Create a new todo with full audit tracking"""
    print(f"📝 Creating todo: {request.title}")
    
    # Get user email from headers or request
    user_email = x_user_email or api_request.headers.get("x-user-email") or get_user_email_from_request(api_request)
    
    # Extract client info
    client_info = get_client_info(api_request)
    
    # Use user email as identifier if available
    user_identifier = user_email if "@" in user_email and "." in user_email else f"{client_info['computer_name']}@{client_info['ip_address']}"
    
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

# ========== TODO ROUTES (WITHOUT SLASH) ==========
@app.get("/todos")
async def list_todos_no_slash():
    """List all todos (without slash)"""
    return await list_todos()

@app.post("/todos")
async def create_todo_no_slash(
    request: TodoCreate, 
    api_request: Request,
    x_user_email: Optional[str] = Header(None, alias="x-user-email")
):
    """Create a new todo (without slash)"""
    return await create_todo(request, api_request, x_user_email)

# ========== SINGLE TODO ENDPOINTS ==========
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

@app.put("/todos/{todo_id}")
async def update_todo(
    todo_id: int, 
    request: TodoUpdate, 
    api_request: Request,
    x_user_email: Optional[str] = Header(None, alias="x-user-email")
):
    """Update a todo with audit logging"""
    print(f"📝 Updating todo {todo_id}")
    
    # Get user email from headers or request
    user_email = x_user_email or api_request.headers.get("x-user-email") or get_user_email_from_request(api_request)
    
    # Extract client info
    client_info = get_client_info(api_request)
    
    # Use user email as identifier if available
    user_identifier = user_email if "@" in user_email and "." in user_email else f"{client_info['computer_name']}@{client_info['ip_address']}"
    
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

# ========== DELETE ENDPOINTS ==========
@app.delete("/todos/{todo_id}")
async def delete_todo(
    todo_id: int, 
    api_request: Request,
    x_user_email: Optional[str] = Header(None, alias="x-user-email")
):
    """Delete a todo with audit logging"""
    print(f"🗑️ Deleting todo {todo_id}")
    
    # Get user email from headers or request
    user_email = x_user_email or api_request.headers.get("x-user-email") or get_user_email_from_request(api_request)
    
    # Extract client info
    client_info = get_client_info(api_request)
    
    # Use user email as identifier if available
    user_identifier = user_email if "@" in user_email and "." in user_email else f"{client_info['computer_name']}@{client_info['ip_address']}"
    
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

            print(f"✅ Todo {todo_id} deleted by {user_identifier}")
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
                    if "@" in user_id and "." in user_id:
                        user_info = user_id
                    elif "@" in user_id:
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

# ========== CHAT ENDPOINTS ==========
@app.post("/chat")
async def chat_endpoint(request: ChatRequest, api_request: Request):
    """Chat endpoint that can show audit info"""
    user_msg = request.message.lower()
    
    # Extract user info for audit
    client_info = get_client_info(api_request)
    user_identifier = f"{client_info['computer_name']}@{client_info['ip_address']}"
    
    print(f"[CHAT] Received: '{request.message}' from {user_identifier}")
    
    # Get data from database
    counts = get_todo_counts()
    
    # Simple response
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

@app.post("/v1/chat")
async def v1_chat(request: ChatRequest):
    """v1 endpoint for frontend compatibility"""
    print(f"[V1 CHAT] Received: '{request.message}'")
    
    counts = get_todo_counts()
    
    response = f"""🤖 Student Management Assistant

I understand: "{request.message}"

Current Stats:
• Students: {counts['students']}
• Todos: {counts['total']}"""
    
    return {"response": response}

# ========== HEALTH & TEST ENDPOINTS ==========
@app.get("/health")
async def health():
    """Health check endpoint"""
    counts = get_todo_counts()
    
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
        "version": "3.6",
        "statistics": {
            "students": counts['students'],
            "todos": counts['total'],
            "audit_logs": audit_count
        }
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Student Management API with Audit Tracking",
        "version": "3.6",
        "status": "running",
        "endpoints": {
            "students": [
                "GET /students - List students (with or without slash)",
                "POST /students - Create student",
                "GET /students/{id} - Get single student",
                "PUT /students/{id} - Update student"
            ],
            "todos": [
                "GET /todos - List todos (with or without slash)",
                "POST /todos - Create todo",
                "GET /todos/{id} - Get single todo",
                "PUT /todos/{id} - Update todo",
                "DELETE /todos/{id} - Delete todo"
            ],
            "audit": ["GET /audit-logs - All audit logs"],
            "chat": ["POST /chat", "POST /v1/chat"],
            "monitoring": ["GET /health"]
        }
    }

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 STUDENT MANAGEMENT CHAT BACKEND v3.6")
    print("="*70)
    print("✅ Both with and without slash endpoints enabled")
    print("✅ GET and POST endpoints for /students and /todos")
    print("✅ User email tracking in database")
    print("✅ Error handling for audit history")
    print("="*70)
    print("📡 **Available Endpoints:**")
    print("  • GET  /students OR /students/ - List students")
    print("  • POST /students OR /students/ - Create student")
    print("  • GET  /todos OR /todos/ - List todos")
    print("  • POST /todos OR /todos/ - Create todo")
    print("="*70)
    print("✅ Starting server...")
    print("="*70)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info"
    )