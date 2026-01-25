# app.py - Production Ready Backend
from fastapi import FastAPI, HTTPException, Request, Header, BackgroundTasks
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlmodel import Field, Session, SQLModel, create_engine, select
import os
from dotenv import load_dotenv
import time
import hashlib
from contextlib import asynccontextmanager
import google.generativeai as genai
import logging
from logging.handlers import RotatingFileHandler

# ========== SETUP LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('app.log', maxBytes=10485760, backupCount=5),  # 10MB per file
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# ========== CONFIGURATION ==========
class Config:
    """Application configuration"""
    APP_NAME = "AI Todo Chatbot"
    VERSION = "1.0.0"
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./todo_chat.db")
    
    # AI Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    AI_MODEL_NAME = os.getenv("AI_MODEL", "models/gemini-2.0-flash")
    
    # Security
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://yourdomain.com",  # Add your domain
        "https://*.vercel.app"  # For Vercel deployments
    ]
    
    # Rate limiting (requests per minute)
    RATE_LIMIT = 60

config = Config()

# Add SSL mode if using Neon PostgreSQL
if "neon.tech" in config.DATABASE_URL and "sslmode" not in config.DATABASE_URL:
    config.DATABASE_URL += "?sslmode=require"

# Initialize database engine
engine = create_engine(
    config.DATABASE_URL, 
    echo=False, 
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Initialize AI
AI_MODEL = None
if config.GOOGLE_API_KEY:
    try:
        genai.configure(api_key=config.GOOGLE_API_KEY)
        AI_MODEL = genai.GenerativeModel(config.AI_MODEL_NAME)
        logger.info(f"AI model initialized: {config.AI_MODEL_NAME}")
    except Exception as e:
        logger.error(f"Failed to initialize AI: {e}")
        AI_MODEL = None

# ========== DATABASE MODELS ==========
class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    name: Optional[str] = None
    avatar: Optional[str] = None
    is_active: bool = Field(default=True)

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TodoBase(SQLModel):
    title: str = Field(index=True)
    description: Optional[str] = None
    priority: str = Field(default="medium")  # low, medium, high, urgent
    status: str = Field(default="todo")  # todo, in_progress, done, cancelled
    due_date: Optional[datetime] = None
    category: Optional[str] = Field(default="general")  # work, personal, study, health
    tags: Optional[str] = None  # Comma-separated tags
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    completed_at: Optional[datetime] = None
    estimated_time: Optional[int] = None  # in minutes
    reminder_sent: bool = Field(default=False)

class Todo(TodoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatHistoryBase(SQLModel):
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    message: str
    is_user: bool = Field(default=True)  # True for user, False for bot
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None

class ChatHistory(ChatHistoryBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
class AnalyticsBase(SQLModel):
    event_type: str  # todo_created, todo_completed, chat_message, etc.
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    data: Optional[str] = None  # JSON string for additional data

class Analytics(AnalyticsBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ========== LIFECYCLE MANAGER ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan for startup and shutdown"""
    logger.info("=" * 70)
    logger.info(f"🚀 {config.APP_NAME} v{config.VERSION}")
    logger.info("=" * 70)
    
    # Create tables
    SQLModel.metadata.create_all(engine)
    logger.info("✅ Database initialized")
    
    if AI_MODEL:
        logger.info(f"✅ AI Service: Google Gemini ({config.AI_MODEL_NAME})")
    else:
        logger.warning("⚠️ AI Service: Disabled")
    
    logger.info("✅ Ready to accept requests")
    logger.info("=" * 70)
    
    yield
    
    logger.info("=" * 70)
    logger.info("🛑 Shutting down...")
    logger.info("=" * 70)

# ========== HELPER FUNCTIONS ==========
def get_client_info(request: Request) -> dict:
    """Extract client information"""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    return {
        "ip_address": client_ip,
        "user_agent": user_agent,
        "timestamp": datetime.now(timezone.utc)
    }

def log_analytics(event_type: str, user_id: Optional[int] = None, data: Optional[Dict] = None):
    """Log analytics events"""
    try:
        with Session(engine) as session:
            analytics = Analytics(
                event_type=event_type,
                user_id=user_id,
                data=json.dumps(data) if data else None
            )
            session.add(analytics)
            session.commit()
    except Exception as e:
        logger.error(f"Failed to log analytics: {e}")

def get_todo_statistics(user_id: Optional[int] = None) -> Dict[str, Any]:
    """Get comprehensive todo statistics"""
    with Session(engine) as session:
        # Build query
        query = select(Todo)
        if user_id:
            query = query.where(Todo.user_id == user_id)
        
        todos = session.exec(query).all()
        total = len(todos)
        
        if total == 0:
            return {
                "total": 0,
                "by_status": {},
                "by_priority": {},
                "by_category": {},
                "completion_rate": 0,
                "overdue": 0
            }
        
        # Calculate statistics
        by_status = {}
        by_priority = {}
        by_category = {}
        completed = 0
        overdue = 0
        
        for todo in todos:
            # Status
            by_status[todo.status] = by_status.get(todo.status, 0) + 1
            if todo.status == "done":
                completed += 1
            
            # Priority
            by_priority[todo.priority] = by_priority.get(todo.priority, 0) + 1
            
            # Category
            by_category[todo.category] = by_category.get(todo.category, 0) + 1
            
            # Overdue
            if todo.due_date and todo.due_date < datetime.now(timezone.utc) and todo.status != "done":
                overdue += 1
        
        completion_rate = (completed / total) * 100 if total > 0 else 0
        
        return {
            "total": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "by_category": by_category,
            "completion_rate": round(completion_rate, 2),
            "overdue": overdue,
            "in_progress": by_status.get("in_progress", 0),
            "pending": by_status.get("todo", 0)
        }

def get_ai_suggestions(todos: List[Todo]) -> List[Dict[str, Any]]:
    """Get AI suggestions for todos"""
    suggestions = []
    
    now = datetime.now(timezone.utc)
    for todo in todos:
        # Suggest based on due date
        if todo.due_date:
            days_left = (todo.due_date - now).days
            if days_left < 0 and todo.status != "done":
                suggestions.append({
                    "type": "overdue",
                    "todo_id": todo.id,
                    "title": todo.title,
                    "message": f"⚠️ This task is {abs(days_left)} days overdue!",
                    "priority": "high"
                })
            elif days_left <= 1 and todo.status == "todo":
                suggestions.append({
                    "type": "due_soon",
                    "todo_id": todo.id,
                    "title": todo.title,
                    "message": "⏰ Due tomorrow! Consider starting this task.",
                    "priority": "medium"
                })
        
        # Suggest based on priority
        if todo.priority == "urgent" and todo.status == "todo":
            suggestions.append({
                "type": "urgent",
                "todo_id": todo.id,
                "title": todo.title,
                "message": "🚨 Urgent task needs attention!",
                "priority": "high"
            })
        
        # Suggest based on estimated time
        if todo.estimated_time and todo.estimated_time > 120 and todo.status == "todo":
            suggestions.append({
                "type": "large_task",
                "todo_id": todo.id,
                "title": todo.title,
                "message": "📋 This is a large task (>2 hours). Consider breaking it down.",
                "priority": "low"
            })
    
    # Sort by priority
    priority_order = {"high": 3, "medium": 2, "low": 1}
    suggestions.sort(key=lambda x: priority_order.get(x["priority"], 0), reverse=True)
    
    return suggestions[:5]  # Return top 5 suggestions

async def process_with_ai(user_message: str, context: Dict[str, Any]) -> str:
    """Process user message with AI"""
    if not AI_MODEL:
        return "AI service is currently unavailable. Please try again later."
    
    try:
        # Build system prompt with context
        system_prompt = f"""You are an AI Todo Assistant. Help users manage their todos effectively.

CONTEXT:
- User: {context.get('user_name', 'Unknown')}
- Total Todos: {context.get('stats', {}).get('total', 0)}
- Completion Rate: {context.get('stats', {}).get('completion_rate', 0)}%
- Overdue Tasks: {context.get('stats', {}).get('overdue', 0)}
- Tasks in Progress: {context.get('stats', {}).get('in_progress', 0)}

RECENT TODOS (last 5):
{chr(10).join([f"- {todo['title']} ({todo['status']}) - Priority: {todo['priority']}" for todo in context.get('recent_todos', [])])}

USER QUERY: "{user_message}"

RESPONSE GUIDELINES:
1. Be helpful, friendly, and concise
2. Reference actual todo data when relevant
3. Provide specific suggestions based on context
4. If user asks to list todos, provide actual counts and suggestions
5. If user wants to create/update todos, explain how
6. Format responses clearly with emojis when appropriate
7. Keep responses under 300 words

Response:"""
        
        response = await AI_MODEL.generate_content_async(system_prompt)
        return response.text
        
    except Exception as e:
        logger.error(f"AI processing error: {e}")
        return f"I encountered an error. Here's what I can tell you:\n\nTotal Todos: {context.get('stats', {}).get('total', 0)}\nOverdue: {context.get('stats', {}).get('overdue', 0)}\n\nTry asking 'show todos' or 'help' for available commands."

# ========== REQUEST MODELS ==========
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[int] = None

class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    status: str = "todo"
    due_date: Optional[datetime] = None
    category: Optional[str] = "general"
    tags: Optional[List[str]] = None
    estimated_time: Optional[int] = None

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    estimated_time: Optional[int] = None
    completed_at: Optional[datetime] = None

class UserCreate(BaseModel):
    email: str
    name: Optional[str] = None
    avatar: Optional[str] = None

# ========== FASTAPI APP ==========
app = FastAPI(
    lifespan=lifespan,
    title=config.APP_NAME,
    version=config.VERSION,
    description="AI-powered Todo Management System with Chat Assistant",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ========== CORS CONFIGURATION ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# ========== MIDDLEWARE ==========
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = time.time()
    request_id = hashlib.md5(f"{start_time}{request.url.path}".encode()).hexdigest()[:8]
    
    logger.info(f"[{request_id}] {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(f"[{request_id}] Completed in {process_time:.2f}s - Status: {response.status_code}")
        
        # Add request ID to headers
        response.headers["X-Request-ID"] = request_id
        return response
        
    except Exception as e:
        logger.error(f"[{request_id}] Error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "request_id": request_id}
        )

# ========== HEALTH & INFO ENDPOINTS ==========
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": config.APP_NAME,
        "version": config.VERSION,
        "status": "running",
        "ai_enabled": AI_MODEL is not None,
        "ai_model": config.AI_MODEL_NAME if AI_MODEL else None,
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "api": {
                "todos": "/api/todos",
                "chat": "/api/chat",
                "users": "/api/users",
                "analytics": "/api/analytics"
            }
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    with Session(engine) as session:
        # Check database
        try:
            session.exec(select(Todo).limit(1))
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        # Check AI
        ai_status = "healthy" if AI_MODEL else "disabled"
        
        # Get statistics
        todo_count = session.exec(select(Todo)).all()
        user_count = session.exec(select(User)).all()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": db_status,
            "ai": ai_status,
            "cache": "in_memory"
        },
        "statistics": {
            "todos": len(todo_count),
            "users": len(user_count),
            "uptime": time.time()
        }
    }

# ========== CHAT ENDPOINTS ==========
@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    x_user_email: Optional[str] = Header(None, alias="x-user-email")
):
    """Main chat endpoint with AI"""
    start_time = time.time()
    
    # Get or create user
    with Session(engine) as session:
        user = None
        if x_user_email:
            user = session.exec(select(User).where(User.email == x_user_email)).first()
        
        if not user and x_user_email:
            # Create new user
            user = User(email=x_user_email, name=x_user_email.split("@")[0])
            session.add(user)
            session.commit()
            session.refresh(user)
        
        # Get context for AI
        stats = get_todo_statistics(user.id if user else None)
        
        # Get recent todos
        query = select(Todo).order_by(Todo.created_at.desc()).limit(5)
        if user:
            query = query.where(Todo.user_id == user.id)
        
        recent_todos = session.exec(query).all()
        
        context = {
            "user_id": user.id if user else None,
            "user_name": user.name if user else "Guest",
            "user_email": user.email if user else None,
            "stats": stats,
            "recent_todos": [{
                "id": todo.id,
                "title": todo.title,
                "status": todo.status,
                "priority": todo.priority,
                "due_date": todo.due_date.isoformat() if todo.due_date else None
            } for todo in recent_todos]
        }
    
    # Process with AI
    ai_response = await process_with_ai(request.message, context)
    
    # Log chat history
    if context["user_id"]:
        background_tasks.add_task(
            log_chat_history,
            context["user_id"],
            request.message,
            ai_response,
            len(request.message) + len(ai_response)  # Approximate tokens
        )
    
    # Log analytics
    log_analytics(
        "chat_message",
        context["user_id"],
        {
            "message_length": len(request.message),
            "response_length": len(ai_response),
            "processing_time": time.time() - start_time
        }
    )
    
    # Get suggestions based on todos
    with Session(engine) as session:
        query = select(Todo)
        if context["user_id"]:
            query = query.where(Todo.user_id == context["user_id"])
        
        todos = session.exec(query).all()
        suggestions = get_ai_suggestions(todos)
    
    return {
        "response": ai_response,
        "suggestions": suggestions,
        "context": {
            "stats": stats,
            "user": context["user_name"]
        },
        "processing_time": round(time.time() - start_time, 2)
    }

def log_chat_history(user_id: int, user_message: str, bot_response: str, tokens_used: int):
    """Log chat history to database"""
    try:
        with Session(engine) as session:
            # Log user message
            user_msg = ChatHistory(
                user_id=user_id,
                message=user_message,
                is_user=True,
                tokens_used=len(user_message) // 4  # Approximate token count
            )
            session.add(user_msg)
            
            # Log bot response
            bot_msg = ChatHistory(
                user_id=user_id,
                message=bot_response,
                is_user=False,
                tokens_used=len(bot_response) // 4,
                model_used=config.AI_MODEL_NAME
            )
            session.add(bot_msg)
            
            session.commit()
    except Exception as e:
        logger.error(f"Failed to log chat history: {e}")

# ========== TODO ENDPOINTS ==========
@app.get("/api/todos")
async def get_todos(
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    limit: int = 20
):
    """Get todos with filtering and pagination"""
    with Session(engine) as session:
        # Build query
        query = select(Todo)
        
        if user_id:
            query = query.where(Todo.user_id == user_id)
        if status:
            query = query.where(Todo.status == status)
        if priority:
            query = query.where(Todo.priority == priority)
        if category:
            query = query.where(Todo.category == category)
        
        # Count total
        total_query = query
        total = len(session.exec(total_query).all())
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit).order_by(Todo.created_at.desc())
        
        todos = session.exec(query).all()
        
        # Get statistics
        stats = get_todo_statistics(user_id)
        
        return {
            "todos": [{
                "id": todo.id,
                "title": todo.title,
                "description": todo.description,
                "priority": todo.priority,
                "status": todo.status,
                "due_date": todo.due_date.isoformat() if todo.due_date else None,
                "category": todo.category,
                "tags": todo.tags.split(",") if todo.tags else [],
                "created_at": todo.created_at.isoformat(),
                "updated_at": todo.updated_at.isoformat(),
                "completed_at": todo.completed_at.isoformat() if todo.completed_at else None,
                "user_id": todo.user_id,
                "estimated_time": todo.estimated_time,
                "is_overdue": todo.due_date and todo.due_date < datetime.now(timezone.utc) and todo.status != "done"
            } for todo in todos],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            },
            "statistics": stats
        }

@app.post("/api/todos")
async def create_todo(
    todo: TodoCreate,
    background_tasks: BackgroundTasks,
    x_user_email: Optional[str] = Header(None, alias="x-user-email")
):
    """Create a new todo"""
    with Session(engine) as session:
        # Get user
        user = None
        if x_user_email:
            user = session.exec(select(User).where(User.email == x_user_email)).first()
        
        # Create todo
        new_todo = Todo(
            **todo.dict(exclude={"tags"}),
            tags=",".join(todo.tags) if todo.tags else None,
            user_id=user.id if user else None
        )
        
        session.add(new_todo)
        session.commit()
        session.refresh(new_todo)
        
        # Log analytics
        background_tasks.add_task(
            log_analytics,
            "todo_created",
            user.id if user else None,
            {"todo_id": new_todo.id, "priority": todo.priority}
        )
        
        return {
            "success": True,
            "todo": {
                "id": new_todo.id,
                "title": new_todo.title,
                "priority": new_todo.priority,
                "status": new_todo.status,
                "created_at": new_todo.created_at.isoformat()
            }
        }

@app.put("/api/todos/{todo_id}")
async def update_todo(
    todo_id: int,
    todo_update: TodoUpdate,
    background_tasks: BackgroundTasks,
    x_user_email: Optional[str] = Header(None, alias="x-user-email")
):
    """Update a todo"""
    with Session(engine) as session:
        # Get todo
        todo = session.exec(select(Todo).where(Todo.id == todo_id)).first()
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        # Check if user owns this todo (optional security)
        user = None
        if x_user_email:
            user = session.exec(select(User).where(User.email == x_user_email)).first()
            if todo.user_id and todo.user_id != user.id:
                raise HTTPException(status_code=403, detail="Not authorized")
        
        # Update fields
        update_data = todo_update.dict(exclude_unset=True, exclude={"tags"})
        
        # Handle tags
        if todo_update.tags is not None:
            todo.tags = ",".join(todo_update.tags) if todo_update.tags else None
        
        # Handle completion
        if todo_update.status == "done" and todo.status != "done":
            todo.completed_at = datetime.now(timezone.utc)
        
        # Update other fields
        for key, value in update_data.items():
            setattr(todo, key, value)
        
        todo.updated_at = datetime.now(timezone.utc)
        session.add(todo)
        session.commit()
        
        # Log analytics
        background_tasks.add_task(
            log_analytics,
            "todo_updated",
            user.id if user else None,
            {"todo_id": todo_id, "status": todo_update.status}
        )
        
        return {
            "success": True,
            "todo": {
                "id": todo.id,
                "title": todo.title,
                "status": todo.status,
                "updated_at": todo.updated_at.isoformat()
            }
        }

@app.delete("/api/todos/{todo_id}")
async def delete_todo(
    todo_id: int,
    background_tasks: BackgroundTasks,
    x_user_email: Optional[str] = Header(None, alias="x-user-email")
):
    """Delete a todo"""
    with Session(engine) as session:
        # Get todo
        todo = session.exec(select(Todo).where(Todo.id == todo_id)).first()
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        # Check if user owns this todo
        user = None
        if x_user_email:
            user = session.exec(select(User).where(User.email == x_user_email)).first()
            if todo.user_id and todo.user_id != user.id:
                raise HTTPException(status_code=403, detail="Not authorized")
        
        # Delete
        session.delete(todo)
        session.commit()
        
        # Log analytics
        background_tasks.add_task(
            log_analytics,
            "todo_deleted",
            user.id if user else None,
            {"todo_id": todo_id}
        )
        
        return {"success": True, "message": f"Todo {todo_id} deleted"}

# ========== ANALYTICS ENDPOINTS ==========
@app.get("/api/analytics/dashboard")
async def get_dashboard(
    days: int = 7,
    x_user_email: Optional[str] = Header(None, alias="x-user-email")
):
    """Get dashboard analytics"""
    with Session(engine) as session:
        # Get user
        user = None
        user_id = None
        if x_user_email:
            user = session.exec(select(User).where(User.email == x_user_email)).first()
            if user:
                user_id = user.id
        
        # Get todo statistics
        stats = get_todo_statistics(user_id)
        
        # Get completion trend (last 7 days)
        trend_data = []
        for i in range(days):
            date = datetime.now(timezone.utc) - timedelta(days=i)
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Count todos created on this day
            query = select(Todo).where(Todo.created_at >= start_of_day, Todo.created_at <= end_of_day)
            if user_id:
                query = query.where(Todo.user_id == user_id)
            
            created = len(session.exec(query).all())
            
            # Count todos completed on this day
            query = select(Todo).where(Todo.completed_at >= start_of_day, Todo.completed_at <= end_of_day)
            if user_id:
                query = query.where(Todo.user_id == user_id)
            
            completed = len(session.exec(query).all())
            
            trend_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "created": created,
                "completed": completed
            })
        
        # Get chat statistics
        chat_query = select(ChatHistory).where(ChatHistory.user_id == user_id) if user_id else select(ChatHistory)
        chat_messages = session.exec(chat_query).all()
        
        return {
            "statistics": stats,
            "trends": list(reversed(trend_data)),
            "chat_stats": {
                "total_messages": len(chat_messages),
                "user_messages": sum(1 for msg in chat_messages if msg.is_user),
                "bot_messages": sum(1 for msg in chat_messages if not msg.is_user)
            },
            "user": {
                "name": user.name if user else "Guest",
                "email": user.email if user else None,
                "joined": user.created_at.isoformat() if user else None
            }
        }

# ========== DEPLOYMENT CONFIGURATION ==========
if __name__ == "__main__":
    # Production configuration
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info",
        access_log=True,
        proxy_headers=True,
        forwarded_allow_ips="*"
    )