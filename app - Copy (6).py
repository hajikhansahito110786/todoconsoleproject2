from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional
from enum import Enum
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Field, Session, SQLModel, create_engine, select, text
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import jwt
from passlib.context import CryptContext

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

# ========== AUTH CONFIGURATION ==========
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/signin")

# ========== IMPORTS FROM UNIFIED MODELS AND SCHEMAS ==========
from models import Student, Todo, Priority, Status, get_session
from schemas import (
    StudentCreate, StudentUpdate, StudentRead,
    TodoCreate, TodoUpdate, TodoRead
)

# ========== AUTH MODELS ==========
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class SignInRequest(BaseModel):
    email: str
    password: str

class SignUpRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

class UserBase(BaseModel):
    email: str
    name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

# SQLModel User table
class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: Optional[str] = None
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ========== AUTH UTILITY FUNCTIONS ==========
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except jwt.PyJWTError:
        raise credentials_exception
    
    with Session(engine) as session:
        user = session.exec(
            select(User).where(User.email == token_data.email)
        ).first()
        if user is None:
            raise credentials_exception
        return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# ========== LIFESPAN ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*50)
    print("🚀 Starting Student Todo Management System")
    print("="*50)
    
    SQLModel.metadata.create_all(engine)
    print("✅ Database ready!")
    
    yield
    
    print("\n" + "="*50)
    print("🛑 Shutting down...")
    print("="*50)

# ========== FASTAPI APP ==========
app = FastAPI(
    title="Student Todo Management System",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== HELPER FUNCTIONS ==========
def student_db_to_read(student_db: Student) -> StudentRead:
    """Convert database model to API response"""
    return StudentRead(
        id=student_db.id,
        name=student_db.name,
        email=student_db.email,
        created_at=student_db.created_at
    )

def todo_db_to_read(todo_db: Todo) -> TodoRead:
    """Convert Todo database model to API response"""
    return TodoRead(
        id=todo_db.id,
        title=todo_db.title,
        description=todo_db.description,
        priority=todo_db.priority,
        status=todo_db.status,
        due_date=todo_db.due_date,
        student_id=todo_db.student_id,
        created_at=todo_db.created_at,
        completed_at=todo_db.completed_at
    )

# ========== AUTH ROUTES ==========
@app.post("/auth/signup", response_model=UserRead)
async def sign_up(request: SignUpRequest):
    with Session(engine) as session:
        # Check if user already exists
        existing_user = session.exec(
            select(User).where(User.email == request.email)
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(request.password)
        user = User(
            email=request.email,
            name=request.name,
            hashed_password=hashed_password
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        return user

@app.post("/auth/signin", response_model=Token)
async def sign_in(request: SignInRequest):
    with Session(engine) as session:
        user = session.exec(
            select(User).where(User.email == request.email)
        ).first()
        
        if not user or not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=UserRead)
async def get_current_user_endpoint(current_user: User = Depends(get_current_active_user)):
    return current_user

# ========== STUDENT ROUTES ==========
@app.post("/students/", response_model=StudentRead)
async def create_student(student: StudentCreate):
    with Session(engine) as session:
        db_student = Student(
            name=student.name,
            email=student.email
        )
        session.add(db_student)
        session.commit()
        session.refresh(db_student)
        return student_db_to_read(db_student)

@app.get("/students/", response_model=List[StudentRead])
async def read_students():
    with Session(engine) as session:
        students = session.exec(select(Student)).all()
        return [student_db_to_read(s) for s in students]

@app.get("/students/{student_id}", response_model=StudentRead)
async def read_student(student_id: int):
    with Session(engine) as session:
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        return student_db_to_read(student)

@app.put("/students/{student_id}", response_model=StudentRead)
async def update_student(student_id: int, student_update: StudentUpdate):
    with Session(engine) as session:
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        if student_update.name is not None:
            student.name = student_update.name
        
        if student_update.email is not None:
            student.email = student_update.email
        
        session.add(student)
        session.commit()
        session.refresh(student)
        return student_db_to_read(student)

@app.delete("/students/{student_id}")
async def delete_student(student_id: int):
    with Session(engine) as session:
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        try:
            # Delete from studentclass first
            try:
                session.exec(text("DELETE FROM studentclass WHERE student_id = :student_id"), 
                            {"student_id": student_id})
                print(f"✅ Deleted related studentclass records for student {student_id}")
            except Exception as e:
                print(f"ℹ️  studentclass table might not exist or error: {e}")
            
            # Delete associated todos
            try:
                todos = session.exec(select(Todo).where(Todo.student_id == student_id)).all()
                for todo in todos:
                    session.delete(todo)
                print(f"✅ Deleted {len(todos)} todos for student {student_id}")
            except Exception as e:
                print(f"ℹ️  Error deleting todos: {e}")
            
            # Now delete the student
            session.delete(student)
            session.commit()
            
            return {"message": f"Student {student_id} deleted successfully with related records"}
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error deleting student {student_id}: {e}")
            
            if "foreign key" in str(e).lower():
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot delete student {student_id}. They have related records in other tables. Delete those records first."
                )
            else:
                raise HTTPException(status_code=500, detail=f"Failed to delete student: {e}")

# ========== TODO ROUTES ==========
@app.post("/todos/", response_model=TodoRead)
async def create_todo(todo: TodoCreate):
    with Session(engine) as session:
        db_todo = Todo(
            title=todo.title,
            description=todo.description,
            priority=todo.priority,
            status=todo.status,
            due_date=todo.due_date,
            student_id=todo.student_id
        )
        session.add(db_todo)
        session.commit()
        session.refresh(db_todo)
        return todo_db_to_read(db_todo)

@app.get("/todos/", response_model=List[TodoRead])
async def read_todos():
    with Session(engine) as session:
        todos = session.exec(select(Todo)).all()
        return [todo_db_to_read(todo) for todo in todos]

@app.get("/todos/{todo_id}", response_model=TodoRead)
async def read_todo(todo_id: int):
    with Session(engine) as session:
        todo = session.get(Todo, todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        return todo_db_to_read(todo)

@app.put("/todos/{todo_id}", response_model=TodoRead)
async def update_todo(todo_id: int, todo_update: TodoUpdate):
    with Session(engine) as session:
        todo = session.get(Todo, todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        update_data = todo_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(todo, field, value)
        
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo_db_to_read(todo)

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int):
    with Session(engine) as session:
        todo = session.get(Todo, todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        session.delete(todo)
        session.commit()
        return {"message": "Todo deleted successfully"}

@app.put("/todos/{todo_id}/complete", response_model=TodoRead)
async def mark_todo_complete(todo_id: int):
    with Session(engine) as session:
        todo = session.get(Todo, todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        todo.status = Status.DONE
        todo.completed_at = datetime.utcnow()
        
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo_db_to_read(todo)

@app.get("/todos/student/{student_id}", response_model=List[TodoRead])
async def get_todos_by_student(student_id: int):
    with Session(engine) as session:
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        todos = session.exec(select(Todo).where(Todo.student_id == student_id)).all()
        return [todo_db_to_read(todo) for todo in todos]

# ========== HEALTH CHECK ==========
@app.get("/")
async def root():
    return {
        "message": "Student Todo Management API",
        "status": "running",
        "database": "connected",
        "endpoints": {
            "auth": {
                "signup": "/auth/signup",
                "signin": "/auth/signin",
                "me": "/auth/me"
            },
            "students": "/students",
            "todos": "/todos",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    try:
        with Session(engine) as session:
            session.exec(select(1))
        return {"status": "healthy", "database": "connected"}
    except:
        return {"status": "unhealthy", "database": "disconnected"}

# ========== MAIN ==========
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🎯 STUDENT TODO MANAGEMENT SYSTEM")
    print("="*60)
    print("✅ All 5 Core Todo Features Ready")
    print("✅ Authentication System Added")
    print("✅ Database synchronization enabled")
    print("✅ Foreign key constraint handling fixed")
    print("="*60)
    print("📖 API: http://localhost:8000/docs")
    print("👨‍💻 Frontend: http://localhost:3000")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)