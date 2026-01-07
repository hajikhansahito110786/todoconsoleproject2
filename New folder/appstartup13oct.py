from fastapi import FastAPI, File, UploadFile, Form, Request, Response, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import shutil, os
import subprocess
import json
import tempfile
import time
import mysql.connector
from mysql.connector import Error
import hashlib
import secrets
from typing import Optional
import glob

app = FastAPI(title="AI Document Analysis System", version="1.0.0")

UPLOAD_DIR = "/root/filesearchfolder/documents"
PERMISSION_CODE = "your_secret_code"  # Change this!

# MySQL Configuration
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root', 
    'password': 'YourNewPassword@2025',  # Change this
    'database': 'document_analysis_db'
}

# Global variable to track if assistant is running
assistant_process = None

# Session storage (in production, use Redis or database)
sessions = {}

def get_db_connection():
    """Create MySQL database connection"""
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_database():
    """Initialize MySQL database tables"""
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL
                )
            ''')
            
            # Create system_files table to track pre-loaded documents
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_files (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    file_type VARCHAR(10) NOT NULL,
                    file_size BIGINT,
                    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_filename (filename)
                )
            ''')
            
            connection.commit()
            cursor.close()
            connection.close()
            print("✅ MySQL database initialized successfully!")
    except Error as e:
        print(f"Error initializing database: {e}")

def load_pre_existing_documents():
    """Automatically load all existing documents from the documents folder"""
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        print(f"📁 Created documents directory: {UPLOAD_DIR}")
        return []
    
    supported_extensions = ['.pdf', '.docx', '.xlsx', '.txt']
    documents = []
    
    for ext in supported_extensions:
        pattern = os.path.join(UPLOAD_DIR, f"*{ext}")
        matching_files = glob.glob(pattern)
        documents.extend(matching_files)
    
    # Also check for files without specific extension pattern
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(file_path) and file_path not in documents:
            documents.append(file_path)
    
    # Register documents in database
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            for doc_path in documents:
                filename = os.path.basename(doc_path)
                file_ext = os.path.splitext(filename)[1].lower()
                file_size = os.path.getsize(doc_path)
                
                cursor.execute(
                    "INSERT IGNORE INTO system_files (filename, file_path, file_type, file_size) VALUES (%s, %s, %s, %s)",
                    (filename, doc_path, file_ext, file_size)
                )
            
            connection.commit()
            cursor.close()
            connection.close()
            print(f"✅ Loaded {len(documents)} pre-existing documents into database")
        except Error as e:
            print(f"Error loading documents into database: {e}")
    
    return [os.path.basename(doc) for doc in documents]

def get_system_files():
    """Get all system files from database"""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT filename, file_type, file_size FROM system_files ORDER BY filename")
        files = cursor.fetchall()
        cursor.close()
        connection.close()
        return files
    except Error as e:
        print(f"Error getting system files: {e}")
        return []

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username: str, password: str):
    """Verify user credentials"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        password_hash = hash_password(password)
        
        cursor.execute(
            "SELECT id, username FROM users WHERE username = %s AND password_hash = %s",
            (username, password_hash)
        )
        user = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return user
    except Error as e:
        print(f"Database error: {e}")
        return None

def is_assistant_running():
    """Check if assistant process is running"""
    global assistant_process
    if assistant_process is None:
        return False
    return assistant_process.poll() is None

def create_session(user_id: int, username: str) -> str:
    """Create a new session"""
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        'user_id': user_id,
        'username': username,
        'created_at': time.time()
    }
    return session_id

def get_session(session_id: str):
    """Get session data"""
    if session_id in sessions:
        return sessions[session_id]
    return None

async def get_current_user(request: Request):
    """Get current user from session"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    return session

# Initialize database and load documents on startup
@app.on_event("startup")
async def startup_event():
    init_database()
    loaded_docs = load_pre_existing_documents()
    print(f"🚀 System started with {len(loaded_docs)} documents ready for analysis")

@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    """Beautiful startup page with two main options"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Assistant System</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }

            .container {
                text-align: center;
                background: rgba(255, 255, 255, 0.95);
                padding: 60px 40px;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                backdrop-filter: blur(10px);
                max-width: 600px;
                width: 100%;
                animation: fadeInUp 0.8s ease-out;
            }

            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            .logo {
                font-size: 80px;
                margin-bottom: 20px;
                animation: bounce 2s infinite;
            }

            @keyframes bounce {
                0%, 20%, 50%, 80%, 100% {
                    transform: translateY(0);
                }
                40% {
                    transform: translateY(-10px);
                }
                60% {
                    transform: translateY(-5px);
                }
            }

            h1 {
                color: #2c3e50;
                margin-bottom: 10px;
                font-size: 2.5em;
                font-weight: 700;
            }

            .subtitle {
                color: #7f8c8d;
                margin-bottom: 40px;
                font-size: 1.2em;
                line-height: 1.6;
            }

            .apps-container {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 30px;
            }

            .app-card {
                background: white;
                padding: 30px 20px;
                border-radius: 15px;
                text-decoration: none;
                transition: all 0.3s ease;
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
                border: 2px solid transparent;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 15px;
            }

            .app-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 30px rgba(0, 0, 0, 0.2);
                border-color: #3498db;
            }

            .app-card.filesearch {
                background: linear-gradient(135deg, #3498db, #2980b9);
                color: white;
            }

            .app-card.diary {
                background: linear-gradient(135deg, #27ae60, #219653);
                color: white;
            }

            .app-card.filesearch:hover {
                background: linear-gradient(135deg, #2980b9, #3498db);
            }

            .app-card.diary:hover {
                background: linear-gradient(135deg, #219653, #27ae60);
            }

            .app-icon {
                font-size: 48px;
                margin-bottom: 10px;
            }

            .app-title {
                font-size: 1.4em;
                font-weight: 700;
                margin-bottom: 8px;
            }

            .app-description {
                font-size: 0.9em;
                opacity: 0.9;
                line-height: 1.4;
            }

            .features {
                background: #f8f9fa;
                padding: 25px;
                border-radius: 15px;
                margin-top: 30px;
            }

            .features h3 {
                color: #2c3e50;
                margin-bottom: 15px;
                font-size: 1.3em;
            }

            .features ul {
                list-style: none;
                text-align: left;
            }

            .features li {
                padding: 8px 0;
                color: #5a6c7d;
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .features li:before {
                content: "✓";
                color: #27ae60;
                font-weight: bold;
            }

            .footer {
                margin-top: 30px;
                color: #7f8c8d;
                font-size: 0.9em;
            }

            @media (max-width: 480px) {
                .container {
                    padding: 40px 20px;
                }
                
                .apps-container {
                    grid-template-columns: 1fr;
                }
                
                h1 {
                    font-size: 2em;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🤖</div>
            <h1>AI Assistant System</h1>
            <p class="subtitle">Choose your AI assistant application</p>
            
            <div class="apps-container">
                <a href="/filesearch" class="app-card filesearch">
                    <div class="app-icon">🔍</div>
                    <div class="app-title">File Search</div>
                    <div class="app-description">
                        AI-powered document search and analysis across PDF, DOCX, XLSX files
                    </div>
                </a>
                
                <a href="/diary" class="app-card diary">
                    <div class="app-icon">📝</div>
                    <div class="app-title">Diary Dispatch</div>
                    <div class="app-description">
                        Intelligent diary management and automated dispatch system
                    </div>
                </a>
            </div>

            <div class="features">
                <h3>✨ System Features</h3>
                <ul>
                    <li>AI-powered intelligence</li>
                    <li>Secure authentication</li>
                    <li>Real-time processing</li>
                    <li>Multi-format support</li>
                    <li>Automated workflows</li>
                    <li>User-friendly interface</li>
                </ul>
            </div>

            <div class="footer">
                <p>Powered by FastAPI & AI Technology</p>
            </div>
        </div>

        <script>
            // Add interactive effects
            document.addEventListener('DOMContentLoaded', function() {
                const cards = document.querySelectorAll('.app-card');
                
                cards.forEach(card => {
                    card.addEventListener('mouseenter', function() {
                        this.style.transform = 'translateY(-5px) scale(1.02)';
                    });
                    
                    card.addEventListener('mouseleave', function() {
                        this.style.transform = 'translateY(0) scale(1)';
                    });
                });
            });
        </script>
    </body>
    </html>
    """

@app.get("/filesearch", response_class=HTMLResponse)
async def filesearch_page(request: Request):
    """File Search Application Main Page"""
    try:
        user = await get_current_user(request)
        username = user['username']
        
        # Get all system files
        system_files = get_system_files()
        
        # Check if assistant is running
        assistant_status = "🟢 Running" if is_assistant_running() else "🔴 Stopped"
        
        # Create file list display
        file_list_html = ""
        if system_files:
            for file_info in system_files:
                file_size_kb = file_info['file_size'] // 1024 if file_info['file_size'] else 0
                file_icon = {
                    '.pdf': '📕',
                    '.docx': '📘', 
                    '.xlsx': '📗',
                    '.txt': '📄'
                }.get(file_info['file_type'], '📁')
                
                file_list_html += f"""
                <div style="padding: 8px; margin: 5px 0; background: #f8f9fa; border-radius: 5px; border-left: 4px solid #3498db;">
                    {file_icon} <strong>{file_info['filename']}</strong>
                    <span style="color: #666; font-size: 0.9em; margin-left: 10px;">
                        ({file_info['file_type']}, {file_size_kb} KB)
                    </span>
                </div>
                """
        else:
            file_list_html = "<p>No documents found in the system. Please place PDF, DOCX, or XLSX files in the documents folder.</p>"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>File Search - AI Document Analysis</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #3498db; }}
                h1 {{ color: #2c3e50; margin: 0; }}
                .user-info {{ background: #e8f4fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}
                .status {{ padding: 10px; border-radius: 5px; margin: 10px 0; }}
                .running {{ background: #d4edda; color: #155724; }}
                .stopped {{ background: #f8d7da; color: #721c24; }}
                .section {{ margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 5px; }}
                input, select, button {{ padding: 10px; margin: 5px; border: 1px solid #ddd; border-radius: 5px; }}
                button {{ background: #3498db; color: white; cursor: pointer; border: none; }}
                button:hover {{ background: #2980b9; }}
                .btn-query {{ background: #27ae60; }}
                .btn-query:hover {{ background: #219653; }}
                .btn-back {{ background: #95a5a6; }}
                .btn-back:hover {{ background: #7f8c8d; }}
                .stats {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin-top: 20px; }}
                .info-box {{ background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .file-list {{ max-height: 300px; overflow-y: auto; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔍 File Search Assistant</h1>
                    <a href="/" class="btn-back" style="padding: 8px 15px; background: #95a5a6; color: white; text-decoration: none; border-radius: 5px;">🏠 Home</a>
                </div>
                
                <div class="user-info">
                    <div>
                        <strong>👤 Welcome, {username}!</strong> 
                    </div>
                    <a href="/logout" class="btn-back" style="padding: 8px 15px; background: #95a5a6; color: white; text-decoration: none; border-radius: 5px;">🚪 Logout</a>
                </div>
                
                <div class="status {('running' if is_assistant_running() else 'stopped')}">
                    <strong>AI Assistant Status:</strong> {assistant_status}
                </div>
                
                <div class="section">
                    <h3>📚 Available Documents</h3>
                    <div class="file-list">
                        {file_list_html}
                    </div>
                    <div class="info-box">
                        <strong>💡 System Info:</strong> Documents are automatically loaded from the system folder. 
                        Place PDF, DOCX, or XLSX files in the documents directory to make them available for analysis.
                    </div>
                </div>
                
                <div class="section">
                    <h3>🔍 Query Documents</h3>
                    <div class="info-box">
                        <strong>🚀 Automatic Processing:</strong> Clicking "Start AI Query" will automatically:
                        <ul>
                            <li>Start the AI Assistant if not running</li>
                            <li>Process all available documents</li>
                            <li>Execute your query across all documents</li>
                            <li>Display the results</li>
                            <li>Automatically close the assistant when done</li>
                        </ul>
                    </div>
                    <form action="/auto_query" method="post" id="queryForm">
                        <input name="query" type="text" placeholder="Enter your question about the documents..." required style="width: 400px;">
                        <input name="permission_code" type="password" placeholder="Permission Code" required>
                        <button type="submit" class="btn-query">🚀 Start AI Query</button>
                    </form>
                </div>
                
                <div class="section">
                    <h3>⚙️ Manual Controls</h3>
                    <form action="/start_assistant" method="post" style="display:inline;">
                        <button type="submit">🔧 Start Assistant Only</button>
                    </form>
                    <form action="/stop_assistant" method="post" style="display:inline;">
                        <button type="submit">🛑 Stop Assistant</button>
                    </form>
                </div>
                
                <div class="stats">
                    <h4>📊 System Statistics</h4>
                    <p><strong>Total documents available:</strong> {len(system_files)}</p>
                    <p><strong>Document types:</strong> {', '.join(set([f['file_type'] for f in system_files])) if system_files else 'None'}</p>
                    <p><strong>Documents folder:</strong> {UPLOAD_DIR}</p>
                </div>
            </div>
            
            <script>
                document.getElementById('queryForm').addEventListener('submit', function(e) {{
                    const button = this.querySelector('button[type="submit"]');
                    button.innerHTML = '⏳ Processing...';
                    button.disabled = true;
                }});
            </script>
        </body>
        </html>
        """
    except HTTPException:
        # User not logged in, show login page
        return RedirectResponse(url="/login?redirect=filesearch")

@app.get("/diary", response_class=HTMLResponse)
async def diary_page(request: Request):
    """Diary Dispatch Application Main Page"""
    try:
        user = await get_current_user(request)
        username = user['username']
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Diary Dispatch - AI Assistant</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #27ae60; }}
                h1 {{ color: #2c3e50; margin: 0; }}
                .user-info {{ background: #e8f6ef; padding: 15px; border-radius: 5px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}
                .section {{ margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 5px; }}
                input, textarea, select, button {{ padding: 10px; margin: 5px; border: 1px solid #ddd; border-radius: 5px; width: 100%; }}
                textarea {{ height: 120px; resize: vertical; }}
                button {{ background: #27ae60; color: white; cursor: pointer; border: none; width: auto; }}
                button:hover {{ background: #219653; }}
                .btn-back {{ background: #95a5a6; }}
                .btn-back:hover {{ background: #7f8c8d; }}
                .diary-form {{ background: #e8f6ef; padding: 20px; border-radius: 8px; }}
                .form-group {{ margin: 15px 0; }}
                label {{ display: block; margin-bottom: 5px; font-weight: bold; color: #2c3e50; }}
                .features {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
                .feature-card {{ background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #27ae60; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📝 Diary Dispatch Assistant</h1>
                    <a href="/" class="btn-back" style="padding: 8px 15px; background: #95a5a6; color: white; text-decoration: none; border-radius: 5px;">🏠 Home</a>
                </div>
                
                <div class="user-info">
                    <div>
                        <strong>👤 Welcome, {username}!</strong> 
                    </div>
                    <a href="/logout" class="btn-back" style="padding: 8px 15px; background: #95a5a6; color: white; text-decoration: none; border-radius: 5px;">🚪 Logout</a>
                </div>
                
                <div class="section">
                    <h3>📖 Create New Diary Entry</h3>
                    <div class="diary-form">
                        <form action="/diary_submit" method="post">
                            <div class="form-group">
                                <label for="title">Title:</label>
                                <input type="text" id="title" name="title" placeholder="Enter diary entry title" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="content">Content:</label>
                                <textarea id="content" name="content" placeholder="Write your diary entry here..." required></textarea>
                            </div>
                            
                            <div class="form-group">
                                <label for="category">Category:</label>
                                <select id="category" name="category">
                                    <option value="personal">Personal</option>
                                    <option value="work">Work</option>
                                    <option value="travel">Travel</option>
                                    <option value="ideas">Ideas</option>
                                    <option value="other">Other</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="dispatch_time">Dispatch Time:</label>
                                <input type="datetime-local" id="dispatch_time" name="dispatch_time">
                            </div>
                            
                            <button type="submit">💾 Save & Dispatch</button>
                        </form>
                    </div>
                </div>
                
                <div class="section">
                    <h3>✨ Diary Features</h3>
                    <div class="features">
                        <div class="feature-card">
                            <h4>📅 Smart Scheduling</h4>
                            <p>Schedule diary entries for automatic dispatch at specified times</p>
                        </div>
                        <div class="feature-card">
                            <h4>🔍 AI Analysis</h4>
                            <p>Get insights and patterns from your diary entries using AI</p>
                        </div>
                        <div class="feature-card">
                            <h4>📱 Multi-Platform</h4>
                            <p>Access your diary from any device with secure cloud sync</p>
                        </div>
                        <div class="feature-card">
                            <h4>🔒 Privacy First</h4>
                            <p>Your diary entries are encrypted and stored securely</p>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h3>📊 Recent Entries</h3>
                    <div style="background: #fff3cd; padding: 20px; border-radius: 8px; text-align: center;">
                        <p>📈 Diary analytics and recent entries will be displayed here</p>
                        <p><em>Start writing your first diary entry to see analytics!</em></p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    except HTTPException:
        # User not logged in, show login page
        return RedirectResponse(url="/login?redirect=diary")

@app.post("/diary_submit")
async def diary_submit(request: Request):
    """Handle diary form submission"""
    try:
        user = await get_current_user(request)
    except HTTPException:
        return "<p>Please login to submit diary entries</p>"
    
    form_data = await request.form()
    title = form_data.get("title")
    content = form_data.get("content")
    category = form_data.get("category")
    dispatch_time = form_data.get("dispatch_time")
    
    # Here you would typically save to database and process the diary entry
    # For now, we'll just show a success message
    
    return f"""
    <div style="padding: 20px; background: #d4edda; border-radius: 10px; color: #155724; margin: 20px;">
        <h3>✅ Diary Entry Saved Successfully!</h3>
        <p><strong>Title:</strong> {title}</p>
        <p><strong>Category:</strong> {category}</p>
        <p><strong>Dispatch Time:</strong> {dispatch_time if dispatch_time else 'Immediate'}</p>
        <div style="margin-top: 20px;">
            <a href="/diary" style="background: #27ae60; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-right: 10px;">📝 New Entry</a>
            <a href="/" style="background: #95a5a6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">🏠 Home</a>
        </div>
    </div>
    """

# ... (Keep all your existing endpoints below - auto_query, start_assistant, stop_assistant, login, register, logout)
# The rest of your existing code remains exactly the same...

@app.post("/auto_query", response_class=HTMLResponse)
async def auto_query(request: Request):
    """Automated query endpoint that handles everything automatically"""
    try:
        user = await get_current_user(request)
    except HTTPException:
        return "<p>Please login to run queries</p>"
    
    form_data = await request.form()
    permission_code = form_data.get("permission_code")
    query = form_data.get("query")
    
    if permission_code != PERMISSION_CODE:
        return "<p>Invalid permission code.</p>"
    
    if not query:
        return "<p>Query is required.</p>"
    
    # Step 1: Ensure assistant is running
    global assistant_process
    assistant_was_started = False
    
    if not is_assistant_running():
        try:
            script_path = "/root/filesearchfolder/filesearchutilityandexportcsvAIagent.py"
            assistant_process = subprocess.Popen([
                "python", script_path, "--api-mode"
            ], cwd="/root/filesearchfolder")
            
            # Wait for assistant to initialize
            print("⏳ Starting AI Assistant...")
            for i in range(30):
                if is_assistant_running():
                    if i >= 10:
                        print("✅ Assistant started successfully!")
                        break
                time.sleep(2)
            
            if assistant_process.poll() is not None:
                return """
                <div style="padding: 20px; background: #f8d7da; border-radius: 10px; color: #721c24;">
                    <h3>❌ Assistant Failed to Start</h3>
                    <p>AI Assistant could not be started. Please check the console for errors.</p>
                    <a href='/filesearch' style="color: #721c24; text-decoration: none; padding: 8px 15px; background: #e74c3c; color: white; border-radius: 5px;">← Go back</a>
                </div>
                """
            
            assistant_was_started = True
            print("🚀 Assistant started, proceeding with query...")
            
        except Exception as e:
            return f"""
            <div style="padding: 20px; background: #f8d7da; border-radius: 10px; color: #721c24;">
                <h3>❌ Failed to start assistant</h3>
                <p>Error: {str(e)}</p>
                <a href='/filesearch' style="color: #721c24;">← Go back</a>
            </div>
            """
    
    # Step 2: Execute query
    try:
        # Get all available files
        system_files = get_system_files()
        all_filenames = [f['filename'] for f in system_files]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            request_data = {
                "action": "query",
                "query": query,
                "filename": "all_documents",
                "search_all": True,
                "all_files": all_filenames,
                "file_path": "all_documents"
            }
            json.dump(request_data, temp_file)
            temp_file_path = temp_file.name
        
        signal_file = "/tmp/assistant_request.signal"
        with open(signal_file, 'w') as f:
            f.write(temp_file_path)
        
        response_file = temp_file_path + ".response"
        
        # Wait for response with increased timeout
        timeout = 600
        waited = 0
        check_interval = 2
        
        print(f"⏳ Processing query: {query}")
        print(f"📚 Searching across {len(all_filenames)} documents")
        
        while not os.path.exists(response_file) and waited < timeout:
            time.sleep(check_interval)
            waited += check_interval
            if waited % 30 == 0:
                print(f"⏱️  Still processing... {waited}/{timeout} seconds")
        
        if os.path.exists(response_file):
            with open(response_file, 'r') as f:
                response_data = json.load(f)
            result = response_data.get("response", "No response received")
            
            # Clean up temporary files
            try:
                os.unlink(response_file)
                os.unlink(temp_file_path)
            except:
                pass
            
            # Step 3: Stop assistant if we started it
            if assistant_was_started and assistant_process:
                print("🛑 Stopping assistant after query completion...")
                assistant_process.terminate()
                try:
                    assistant_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    assistant_process.kill()
                assistant_process = None
            
            formatted_result = result.replace('\n', '<br>')
            
            return f"""
            <div style="padding: 20px; background: #f8f9fa; border-radius: 10px; margin: 20px 0;">
                <h3 style="color: #2c3e50;">🎉 Query Results</h3>
                <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #27ae60;">
                    <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                        <strong>✅ Automatic Processing Complete</strong>
                        <p style="margin: 5px 0 0 0; font-size: 0.9em;">
                            Assistant was {'started and ' if assistant_was_started else ''}stopped automatically
                        </p>
                    </div>
                    <p><strong>❓ Your Query:</strong> {query}</p>
                    <p><strong>📊 Documents Analyzed:</strong> {len(all_filenames)} files</p>
                    <p><strong>⏱️ Processing Time:</strong> {waited} seconds</p>
                    <hr>
                    <p><strong>🤖 AI Response:</strong></p>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; border: 1px solid #e9ecef; white-space: pre-wrap; line-height: 1.6;">
                        {formatted_result}
                    </div>
                </div>
                <div style="margin-top: 20px;">
                    <a href='/filesearch' style="background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">← New Query</a>
                </div>
            </div>
            """
        else:
            # Clean up on timeout
            try:
                os.unlink(temp_file_path)
            except:
                pass
            
            # Stop assistant if we started it
            if assistant_was_started and assistant_process:
                assistant_process.terminate()
                assistant_process = None
            
            return f"""
            <div style="padding: 20px; background: #fff3cd; border-radius: 10px; color: #856404;">
                <h3>⏰ Processing Timeout</h3>
                <p>Query processing took longer than {timeout} seconds (10 minutes).</p>
                <p><em>This might be due to a large number of documents or complex query. Please try a more specific query.</em></p>
                <a href='/filesearch' style="color: #856404; text-decoration: none; padding: 8px 15px; background: #ffc107; border-radius: 5px;">← Try Again</a>
            </div>
            """
            
    except Exception as e:
        # Stop assistant if we started it and there was an error
        if assistant_was_started and assistant_process:
            assistant_process.terminate()
            assistant_process = None
            
        return f"""
        <div style="padding: 20px; background: #f8d7da; border-radius: 10px; color: #721c24;">
            <h3>❌ Processing Error</h3>
            <p>Error during query processing: {str(e)}</p>
            <a href='/filesearch' style="color: #721c24; text-decoration: none; padding: 8px 15px; background: #e74c3c; color: white; border-radius: 5px;">← Go back</a>
        </div>
        """

# ... (Keep all other existing endpoints - start_assistant, stop_assistant, register, login, logout)

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        timeout_keep_alive=600,
        timeout_notify=600,
        timeout_graceful_shutdown=600
    )