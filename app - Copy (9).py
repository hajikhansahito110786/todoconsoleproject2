from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select, text
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import secrets

load_dotenv()

# ========== DATABASE CONNECTION ==========
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file.")

engine = create_engine(DATABASE_URL, echo=True)

# ========== SESSION STORAGE ==========
sessions: Dict[str, dict] = {}

# ========== USER TABLE MODEL ==========
class User(SQLModel, table=True):
    __tablename__ = "usertable"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    password: str

# ========== REQUEST MODELS ==========
class LoginRequest(BaseModel):
    email: str
    password: str

# ========== LIFESPAN ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*50)
    print("🚀 Starting Login System")
    print("="*50)
    
    try:
        with Session(engine) as session:
            print("🔍 Checking usertable...")
            
            # Get actual column names
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'usertable'
                ORDER BY ordinal_position
            """))
            columns = [row[0] for row in result.fetchall()]
            
            print(f"✅ Table 'usertable' found")
            print(f"✅ Columns: {', '.join(columns)}")
            
            # Count users
            count_result = session.execute(text("SELECT COUNT(*) FROM usertable"))
            user_count = count_result.scalar()
            print(f"📊 Total users: {user_count}")
            
            if user_count > 0:
                # Show first few users
                users_result = session.execute(text("SELECT * FROM usertable LIMIT 5"))
                users = users_result.fetchall()
                print("👥 Sample users:")
                for user in users:
                    print(f"   - {user}")
    
    except Exception as e:
        print(f"❌ Database error: {e}")
        raise
    
    print("="*50)
    print("✅ Backend ready! Login endpoint: POST /login")
    print("="*50)
    
    yield
    
    print("\n" + "="*50)
    print("🛑 Shutting down...")
    print("="*50)

# ========== FASTAPI APP ==========
app = FastAPI(
    title="Simple Login System",
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

# ========== SESSION MANAGEMENT ==========
def create_session(user_data: dict) -> str:
    session_token = secrets.token_hex(16)
    sessions[session_token] = {
        **user_data,
        "expires_at": datetime.now() + timedelta(minutes=5)
    }
    return session_token

def get_session(token: str) -> Optional[dict]:
    if token not in sessions:
        return None
    
    session_data = sessions[token]
    if datetime.now() > session_data["expires_at"]:
        del sessions[token]
        return None
    
    return session_data

# ========== SIMPLE LOGIN ENDPOINT ==========
@app.post("/login")
async def login(request: LoginRequest, response: Response):
    """
    Simple login - checks email/password in usertable
    """
    print(f"📨 Login attempt for: {request.email}")
    
    try:
        with Session(engine) as session:
            # CORRECT WAY: Use execute() with parameters
            query = text("""
                SELECT id, email, password 
                FROM usertable 
                WHERE email = :email
            """)
            result = session.execute(query, {"email": request.email})
            user_data = result.fetchone()
            
            if not user_data:
                print(f"❌ User not found: {request.email}")
                raise HTTPException(
                    status_code=401,
                    detail="User not found"
                )
            
            user_id, user_email, user_password = user_data
            
            print(f"✅ User found: ID={user_id}, Email={user_email}")
            
            # Check password
            if user_password != request.password:
                print(f"❌ Password incorrect for: {user_email}")
                raise HTTPException(
                    status_code=401,
                    detail="Incorrect password"
                )
            
            print(f"✅ Login successful for: {user_email}")
            
            # Create session
            session_token = create_session({
                "user_id": user_id,
                "email": user_email
            })
            
            # Set cookie
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
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Login error: {str(e)}"
        )

# ========== SIMPLE ENDPOINTS ==========
@app.get("/")
async def root():
    return {
        "message": "Login API",
        "endpoint": "POST /login",
        "test": "GET /test"
    }

@app.get("/health")
async def health_check():
    try:
        with Session(engine) as session:
            # Simple connection test
            session.execute(text("SELECT 1"))
            
            # Count users
            count_result = session.execute(text("SELECT COUNT(*) FROM usertable"))
            user_count = count_result.scalar()
            
            return {
                "status": "healthy",
                "users": user_count
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {
        "message": "Backend is running!",
        "time": datetime.now().isoformat()
    }

@app.get("/check/{email}")
async def check_user(email: str):
    """Check if user exists"""
    try:
        with Session(engine) as session:
            query = text("SELECT email FROM usertable WHERE email = :email")
            result = session.execute(query, {"email": email})
            user = result.fetchone()
            
            return {
                "exists": user is not None,
                "email": email
            }
    except Exception as e:
        return {
            "exists": False,
            "error": str(e)
        }

# ========== MAIN ==========
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🔐 SIMPLE LOGIN SYSTEM")
    print("="*60)
    print("🌐 Backend: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("="*60)
    print("🚀 Starting server...")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)