from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime

class ChatRequest(BaseModel):
    message: str
    user_id: str = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database simulation
#todos = [
#    {"id": 1, "title": "Complete assignment", "status": "todo", "priority": "high"},
#    {"id": 2, "title": "Study for exam", "status": "in_progress", "priority": "medium"},
#    {"id": 3, "title": "Submit project", "status": "done", "priority": "high"}
#]

#students = [
#    {"id": 1, "name": "John Doe", "email": "john@example.com"},
#    {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
#]

# In your working_backend.py, replace the hardcoded todos with:
with Session(engine) as session:
    result = session.execute(text("SELECT id, title, status, priority FROM todo ORDER BY created_at DESC LIMIT 10"))
    real_todos = result.fetchall()
    
    # Use real_todos instead of sample data

# Working chat endpoint
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Fast, reliable chat endpoint"""
    user_msg = request.message.lower()
    
    print(f"[CHAT] {datetime.now().strftime('%H:%M:%S')} - Received: '{request.message}'")
    
    if "hello" in user_msg or "hi" in user_msg:
        return {"response": f"👋 Hello! I'm your Student Management Assistant. We have {len(students)} students and {len(todos)} todos."}
    
    elif "show" in user_msg and "todo" in user_msg:
        todo_list = "📋 **Your Todos:**\n\n"
        for todo in todos:
            status_icon = "📝" if todo["status"] == "todo" else "🔄" if todo["status"] == "in_progress" else "✅"
            priority_icon = "🔴" if todo["priority"] == "high" else "🟡" if todo["priority"] == "medium" else "🟢"
            todo_list += f"{status_icon} **{todo['title']}** (ID: {todo['id']}, Priority: {priority_icon} {todo['priority']}, Status: {todo['status']})\n"
        
        todo_list += f"\n📊 **Total:** {len(todos)} todos"
        todo_list += f"\n👨‍🎓 **Students:** {len(students)}"
        todo_list += "\n\n💡 **Tip:** Create new todos with 'Add New Todo' button!"
        return {"response": todo_list}
    
    elif "create" in user_msg and "todo" in user_msg:
        return {"response": """🆕 **Create a New Todo**

**Steps:**
1. Go to **Todos** page
2. Click **"Add New Todo"** button
3. Fill in:
   - **Title** (required)
   - **Description** (optional)
   - **Priority**: Low/Medium/High
   - **Status**: todo/in_progress/done
   - **Due Date** (optional)
   - **Assign to Student** (optional)
4. Click **"Create Todo"**

🎯 Your new todo will appear in the list!"""}
    
    elif "help" in user_msg:
        return {"response": """🆘 **Help Center**

**Available Features:**
• Student Management (add, edit, view students)
• Todo Management (create, track, complete tasks)
• Assignment System (link todos to students)
• Progress Tracking (monitor completion)

**Common Commands:**
- "show todo" - View todos
- "create todo" - Add new task  
- "list students" - View students
- "how many" - Check counts
- "help" - This message

What would you like to do?"""}
    
    else:
        return {"response": f"""🤖 **Student Management Assistant**

I understand you asked: *"{request.message}"*

**Quick Help:**
- Say "show todo" to view todos
- Say "create todo" to add new tasks
- Say "help" for full guide

Currently managing {len(students)} students and {len(todos)} todos.

How can I help you today?"""}

# Add v1 endpoint for frontend compatibility
@app.post("/v1/chat")
async def v1_chat(request: ChatRequest):
    """v1 endpoint"""
    return await chat_endpoint(request)

# Health endpoint
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "student-chat-backend",
        "timestamp": datetime.now().isoformat(),
        "endpoints": ["/chat", "/v1/chat", "/health"]
    }

# Other endpoints for compatibility
@app.get("/todos/")
async def get_todos():
    return todos

@app.get("/students/")
async def get_students():
    return students

@app.get("/")
async def root():
    return {
        "message": "Student Management Chat Backend",
        "version": "1.0",
        "status": "running",
        "endpoints": {
            "chat": ["POST /chat", "POST /v1/chat"],
            "data": ["GET /todos/", "GET /students/"],
            "health": ["GET /health"]
        }
    }

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 WORKING BACKEND STARTING...")
    print("="*50)
    print("📡 Endpoints:")
    print("  • POST http://localhost:8000/chat")
    print("  • POST http://localhost:8000/v1/chat (for frontend)")
    print("  • GET  http://localhost:8000/health")
    print("  • GET  http://localhost:8000/todos/")
    print("  • GET  http://localhost:8000/students/")
    print("="*50)
    print("✅ This backend will NOT hang or timeout!")
    print("="*50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")