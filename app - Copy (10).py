from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, create_engine, text
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

class LoginRequest(BaseModel):
    email: str
    password: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*50)
    print("🚀 Login System Starting...")
    print("="*50)
    
    try:
        with Session(engine) as session:
            # Test connection
            session.execute(text("SELECT 1"))
            print("✅ Connected to database")
            
            # Count users
            result = session.execute(text("SELECT COUNT(*) FROM usertable"))
            count = result.scalar()
            print(f"✅ Found {count} user(s) in usertable")
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        raise
    
    print("="*50)
    print("✅ Ready! Login at: POST /login")
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

def create_session(user_data: dict) -> str:
    token = secrets.token_hex(16)
    sessions[token] = {
        **user_data,
        "expires_at": datetime.now() + timedelta(minutes=5)
    }
    return token

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

@app.get("/")
async def root():
    return {"message": "Login API", "login": "POST /login"}

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
    print("🔐 SIMPLE LOGIN SYSTEM")
    print("="*60)
    print("🌐 http://localhost:8000")
    print("👤 Login: POST /login")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)