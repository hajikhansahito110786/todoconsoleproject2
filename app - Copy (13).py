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
            from models import Todo  # Import here to avoid circular imports
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

#hk
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
# ========== UPDATE STUDENT ENDPOINTS ==========

@app.get("/students/{student_id}")
async def get_student(student_id: int):
    """Get a single student by ID"""
    with Session(engine) as session:
        # Simple query
        query = text("SELECT * FROM student WHERE id = :student_id")
        result = session.execute(query, {"student_id": student_id})
        student = result.fetchone()
        
        if not student:
            raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
        
        # Convert to dict
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

# ========== DEBUG ENDPOINTS FOR STUDENTS ==========

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
#
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