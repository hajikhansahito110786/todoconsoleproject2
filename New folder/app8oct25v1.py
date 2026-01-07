from fastapi import FastAPI, File, UploadFile, Form, Request, Response, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
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

app = FastAPI()

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
            
            # Create user_files table to track file ownership
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_files (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE KEY unique_user_file (user_id, filename)
                )
            ''')
            
            connection.commit()
            cursor.close()
            connection.close()
            print("✅ MySQL database initialized successfully!")
    except Error as e:
        print(f"Error initializing database: {e}")

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

def get_user_files(user_id: int):
    """Get files uploaded by specific user"""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT filename FROM user_files WHERE user_id = %s",
            (user_id,)
        )
        files = [row['filename'] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        return files
    except Error as e:
        print(f"Error getting user files: {e}")
        return []

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

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()

@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    try:
        user = await get_current_user(request)
        username = user['username']
        user_id = user['user_id']
        user_files = get_user_files(user_id)
        
        # Get all files in upload directory
        all_files = os.listdir(UPLOAD_DIR) if os.path.exists(UPLOAD_DIR) else []
        
        # Create file options for selection (all files)
        file_options = "".join([f'<option value="{f}">{f}</option>' for f in all_files])
        delete_buttons = "".join([
            f'<form action="/delete" method="post" style="display:inline; margin: 5px;">'
            f'<input type="hidden" name="filename" value="{f}">'
            f'<button type="submit" class="btn-delete">🗑️ Delete {f}</button>'
            f'</form><br>'
            for f in user_files
        ])
        
        # Check if assistant is running
        assistant_status = "🟢 Running" if is_assistant_running() else "🔴 Stopped"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Document Analysis System</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                .user-info {{ background: #e8f4fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}
                .status {{ padding: 10px; border-radius: 5px; margin: 10px 0; }}
                .running {{ background: #d4edda; color: #155724; }}
                .stopped {{ background: #f8d7da; color: #721c24; }}
                .section {{ margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 5px; }}
                input, select, button {{ padding: 10px; margin: 5px; border: 1px solid #ddd; border-radius: 5px; }}
                button {{ background: #3498db; color: white; cursor: pointer; border: none; }}
                button:hover {{ background: #2980b9; }}
                .btn-delete {{ background: #e74c3c; }}
                .btn-delete:hover {{ background: #c0392b; }}
                .logout {{ background: #95a5a6; }}
                .logout:hover {{ background: #7f8c8d; }}
                .stats {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin-top: 20px; }}
                .info-box {{ background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>📚 Document Analysis System</h2>
                
                <div class="user-info">
                    <div>
                        <strong>👤 Welcome, {username}!</strong> 
                        <span style="color: #666; margin-left: 10px;">User ID: {user_id}</span>
                    </div>
                    <a href="/logout" class="logout" style="padding: 8px 15px; background: #95a5a6; color: white; text-decoration: none; border-radius: 5px;">🚪 Logout</a>
                </div>
                
                <div class="status {('running' if is_assistant_running() else 'stopped')}">
                    <strong>Assistant Status:</strong> {assistant_status}
                </div>
                
                <div class="section">
                    <h3>📁 Upload Document</h3>
                    <form action="/upload" enctype="multipart/form-data" method="post">
                        <input name="file" type="file" required>
                        <button type="submit">📤 Upload</button>
                    </form>
                </div>
                
                <div class="section">
                    <h3>🔍 Query Documents</h3>
                    <div class="info-box">
                        <strong>💡 Important:</strong> Your query will search across <strong>ALL documents</strong> in the system, 
                        not just the selected file. The file dropdown is for reference only.
                    </div>
                    <form action="/query" method="post">
                        <select name="filename">
                            <option value="all_documents">🔍 Search All Documents</option>
                            {file_options}
                        </select>
                        <input name="permission_code" type="password" placeholder="Permission Code" required>
                        <input name="query" type="text" placeholder="Enter your query..." required style="width: 300px;">
                        <button type="submit">🔎 Search All Documents</button>
                    </form>
                </div>
                
                <div class="section">
                    <h3>⚙️ Assistant Control</h3>
                    <form action="/start_assistant" method="post" style="display:inline;">
                        <button type="submit">🚀 Start Assistant</button>
                    </form>
                    <form action="/stop_assistant" method="post" style="display:inline;">
                        <button type="submit">🛑 Stop Assistant</button>
                    </form>
                </div>
                
                <div class="section">
                    <h3>🗑️ Your Files</h3>
                    <p><em>You can only delete files that you uploaded</em></p>
                    {delete_buttons if delete_buttons else "<p>No files uploaded by you</p>"}
                </div>
                
                <div class="stats">
                    <h4>📊 Your Statistics</h4>
                    <p><strong>Files uploaded by you:</strong> {len(user_files)}</p>
                    <p><strong>Total files in system:</strong> {len(all_files)}</p>
                    <p><strong>Available documents for search:</strong> {', '.join(all_files) if all_files else 'None'}</p>
                </div>
            </div>
        </body>
        </html>
        """
    except HTTPException:
        # User not logged in, show login page
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - Document Analysis System</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex; 
                    justify-content: center; 
                    align-items: center; 
                    min-height: 100vh;
                }
                .login-container { 
                    background: white; 
                    padding: 40px; 
                    border-radius: 15px; 
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2); 
                    width: 350px; 
                    text-align: center;
                }
                h2 { 
                    color: #2c3e50; 
                    margin-bottom: 30px; 
                    font-size: 24px;
                }
                input { 
                    width: 100%; 
                    padding: 12px; 
                    margin: 10px 0; 
                    border: 1px solid #ddd; 
                    border-radius: 5px; 
                    box-sizing: border-box; 
                    font-size: 16px;
                }
                button { 
                    width: 100%; 
                    padding: 12px; 
                    background: #3498db; 
                    color: white; 
                    border: none; 
                    border-radius: 5px; 
                    cursor: pointer; 
                    font-size: 16px;
                    margin-top: 10px;
                }
                button:hover { 
                    background: #2980b9; 
                }
                .register-link { 
                    text-align: center; 
                    margin-top: 20px; 
                    color: #666;
                }
                .register-link a {
                    color: #3498db;
                    text-decoration: none;
                }
                .register-link a:hover {
                    text-decoration: underline;
                }
                .error { 
                    color: #e74c3c; 
                    text-align: center; 
                    margin-bottom: 10px; 
                    padding: 10px;
                    background: #f8d7da;
                    border-radius: 5px;
                }
                .logo {
                    font-size: 48px;
                    margin-bottom: 10px;
                }
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="logo">📚</div>
                <h2>Document Analysis System</h2>
                <form action="/login" method="post">
                    <input type="text" name="username" placeholder="👤 Username" required>
                    <input type="password" name="password" placeholder="🔒 Password" required>
                    <button type="submit">🔐 Login</button>
                </form>
                <div class="register-link">
                    <p>Don't have an account? <a href="/register">Register here</a></p>
                </div>
            </div>
        </body>
        </html>
        """

# ... [Keep the same register, login, logout endpoints as previous version] ...

@app.post("/register", response_class=HTMLResponse)
async def register_user(request: Request):
    form_data = await request.form()
    username = form_data.get("username")
    password = form_data.get("password")
    email = form_data.get("email")
    
    if not username or not password:
        return """
        <div class="register-container">
            <div class="logo">📝</div>
            <h2>Create Account</h2>
            <div class="error">Username and password are required</div>
            <form action="/register" method="post">
                <input type="text" name="username" placeholder="👤 Username" required>
                <input type="password" name="password" placeholder="🔒 Password" required>
                <input type="email" name="email" placeholder="📧 Email (optional)">
                <button type="submit">✅ Register</button>
            </form>
            <div class="login-link">
                <p>Already have an account? <a href="/">Login here</a></p>
            </div>
        </div>
        """
    
    connection = get_db_connection()
    if not connection:
        return "<p>Database connection failed</p>"
    
    try:
        cursor = connection.cursor()
        password_hash = hash_password(password)
        
        cursor.execute(
            "INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)",
            (username, password_hash, email)
        )
        connection.commit()
        cursor.close()
        connection.close()
        
        return """
        <div class="register-container">
            <div class="logo">🎉</div>
            <h2>Registration Successful!</h2>
            <div class="success">Your account has been created successfully!</div>
            <div style="margin-top: 20px;">
                <a href="/" style="display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px;">➡️ Go to Login</a>
            </div>
        </div>
        """
    except Error as e:
        error_msg = "Username already exists" if "Duplicate entry" in str(e) else f"Registration failed: {e}"
        return f"""
        <div class="register-container">
            <div class="logo">📝</div>
            <h2>Create Account</h2>
            <div class="error">{error_msg}</div>
            <form action="/register" method="post">
                <input type="text" name="username" placeholder="👤 Username" required>
                <input type="password" name="password" placeholder="🔒 Password" required>
                <input type="email" name="email" placeholder="📧 Email (optional)">
                <button type="submit">✅ Register</button>
            </form>
            <div class="login-link">
                <p>Already have an account? <a href="/">Login here</a></p>
            </div>
        </div>
        """

@app.post("/login")
async def login_user(request: Request, response: Response):
    form_data = await request.form()
    username = form_data.get("username")
    password = form_data.get("password")
    
    if not username or not password:
        return RedirectResponse(url="/?error=missing_credentials", status_code=302)
    
    user = verify_user(username, password)
    if user:
        # Update last login
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                (user['id'],)
            )
            connection.commit()
            cursor.close()
            connection.close()
        
        # Create session
        session_id = create_session(user['id'], user['username'])
        
        # Set session cookie
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return response
    else:
        return RedirectResponse(url="/?error=invalid_credentials", status_code=302)

@app.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("session_id")
    return response

@app.post("/upload")
async def upload_file(request: Request):
    try:
        user = await get_current_user(request)
    except HTTPException:
        return RedirectResponse(url="/", status_code=302)
    
    form_data = await request.form()
    file = form_data.get("file")
    
    if not file or not hasattr(file, 'filename'):
        return "<p>No file selected</p>"
    
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        if hasattr(file, 'file'):
            shutil.copyfileobj(file.file, buffer)
        else:
            buffer.write(file.value)
    
    # Record file ownership in database
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            # Use INSERT IGNORE to avoid duplicates
            cursor.execute(
                "INSERT IGNORE INTO user_files (user_id, filename, file_path) VALUES (%s, %s, %s)",
                (user['user_id'], file.filename, file_path)
            )
            connection.commit()
            cursor.close()
            connection.close()
        except Error as e:
            print(f"Error recording file ownership: {e}")
    
    return RedirectResponse(url="/", status_code=302)

@app.post("/query", response_class=HTMLResponse)
async def run_query(request: Request):
    try:
        user = await get_current_user(request)
    except HTTPException:
        return "<p>Please login to run queries</p>"
    
    form_data = await request.form()
    permission_code = form_data.get("permission_code")
    query = form_data.get("query")
    filename = form_data.get("filename")
    
    if permission_code != PERMISSION_CODE:
        return "<p>Invalid permission code.</p>"
    
    if not is_assistant_running():
        return "<p>Assistant is not running. Please start the assistant first.</p>"
    
    try:
        # Get all available files for search context
        all_files = os.listdir(UPLOAD_DIR) if os.path.exists(UPLOAD_DIR) else []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            request_data = {
                "action": "query",
                "query": query,
                "filename": filename,
                "search_all": True,  # Flag to indicate search all documents
                "all_files": all_files,  # List all available files
                "file_path": os.path.join(UPLOAD_DIR, filename) if filename != "all_documents" else "all_documents"
            }
            json.dump(request_data, temp_file)
            temp_file_path = temp_file.name
        
        signal_file = "/tmp/assistant_request.signal"
        with open(signal_file, 'w') as f:
            f.write(temp_file_path)
        
        response_file = temp_file_path + ".response"
        timeout = 60
        waited = 0
        
        print(f"⏳ Waiting for assistant response for query: {query}")
        print(f"🔍 Searching across ALL documents: {all_files}")
        
        while not os.path.exists(response_file) and waited < timeout:
            time.sleep(2)
            waited += 2
        
        if os.path.exists(response_file):
            with open(response_file, 'r') as f:
                response_data = json.load(f)
            result = response_data.get("response", "No response received")
            
            try:
                os.unlink(response_file)
                os.unlink(temp_file_path)
            except:
                pass
            
            formatted_result = result.replace('\n', '<br>')
            
            return f"""
            <div style="padding: 20px; background: #f8f9fa; border-radius: 10px; margin: 20px 0;">
                <h3 style="color: #2c3e50;">📊 Query Results</h3>
                <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #3498db;">
                    <div style="background: #e8f4fd; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
                        <strong>🔍 Search Scope:</strong> All Documents ({len(all_files)} files)
                    </div>
                    <p><strong>❓ Query:</strong> {query}</p>
                    <hr>
                    <p><strong>🤖 Response:</strong></p>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #e9ecef; white-space: pre-wrap;">
                        {formatted_result}
                    </div>
                </div>
                <div style="margin-top: 15px;">
                    <a href='/' style="background: #3498db; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px;">← Back to Main</a>
                </div>
            </div>
            """
        else:
            try:
                os.unlink(temp_file_path)
            except:
                pass
            return f"""
            <div style="padding: 20px; background: #fff3cd; border-radius: 10px; color: #856404;">
                <h3>⏰ Timeout</h3>
                <p>Timeout waiting for assistant response after {timeout} seconds.</p>
                <a href='/' style="color: #856404;">← Go back</a>
            </div>
            """
            
    except Exception as e:
        return f"""
        <div style="padding: 20px; background: #f8d7da; border-radius: 10px; color: #721c24;">
            <h3>❌ Error</h3>
            <p>Error processing query: {str(e)}</p>
            <a href='/' style="color: #721c24;">← Go back</a>
        </div>
        """

# ... [Keep the same start_assistant, stop_assistant, delete endpoints as previous version] ...

@app.post("/start_assistant")
async def start_assistant(request: Request):
    try:
        user = await get_current_user(request)
    except HTTPException:
        return "<p>Please login to start assistant</p>"
    
    global assistant_process
    
    if is_assistant_running():
        return HTMLResponse("<p>Assistant is already running.</p><a href='/'>Go back</a>")
    
    try:
        script_path = "/root/filesearchfolder/filesearchutilityandexportcsvAIagent.py"
        assistant_process = subprocess.Popen([
            "python", script_path, "--api-mode"
        ])
        
        print("⏳ Waiting for assistant to initialize and process documents...")
        time.sleep(15)
        
        if assistant_process.poll() is not None:
            return HTMLResponse("""
            <div style="padding: 15px; background: #f8d7da; border-radius: 5px;">
                <p>Assistant failed to start. Check the console for errors.</p>
                <a href='/'>← Go back</a>
            </div>
            """)
        
        return HTMLResponse("""
        <div style="padding: 15px; background: #d1edff; border-radius: 5px;">
            <p>✅ Assistant started successfully and is processing documents!</p>
            <a href='/'>← Go back</a>
        </div>
        """)
    except Exception as e:
        return HTMLResponse(f"""
        <div style="padding: 15px; background: #f8d7da; border-radius: 5px;">
            <p>❌ Failed to start assistant: {str(e)}</p>
            <a href='/'>← Go back</a>
        </div>
        """)

@app.post("/stop_assistant")
async def stop_assistant(request: Request):
    try:
        user = await get_current_user(request)
    except HTTPException:
        return "<p>Please login to stop assistant</p>"
    
    global assistant_process
    
    if assistant_process:
        assistant_process.terminate()
        try:
            assistant_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            assistant_process.kill()
        assistant_process = None
        
        try:
            if os.path.exists("/tmp/assistant_request.signal"):
                os.unlink("/tmp/assistant_request.signal")
        except:
            pass
            
        return HTMLResponse("<p>Assistant stopped successfully!</p><a href='/'>Go back</a>")
    else:
        return HTMLResponse("<p>Assistant is not running.</p><a href='/'>Go back</a>")

@app.post("/delete", response_class=HTMLResponse)
async def delete_file(request: Request):
    try:
        user = await get_current_user(request)
    except HTTPException:
        return "<p>Please login to delete files</p>"
    
    form_data = await request.form()
    filename = form_data.get("filename")
    
    if not filename:
        return "<p>No filename specified</p>"
    
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Check if user owns this file
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT id FROM user_files WHERE user_id = %s AND filename = %s",
                (user['user_id'], filename)
            )
            user_file = cursor.fetchone()
            cursor.close()
            connection.close()
            
            if not user_file:
                return f"""
                <div style="padding: 20px; background: #f8d7da; border-radius: 10px; color: #721c24;">
                    <h3>❌ Access Denied</h3>
                    <p>You can only delete files that you uploaded.</p>
                    <a href='/'>← Go back</a>
                </div>
                """
        except Error as e:
            return f"<p>Error checking file ownership: {e}</p>"
    
    if os.path.exists(file_path):
        os.remove(file_path)
        
        # Remove from database
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute(
                    "DELETE FROM user_files WHERE user_id = %s AND filename = %s",
                    (user['user_id'], filename)
                )
                connection.commit()
                cursor.close()
                connection.close()
            except Error as e:
                print(f"Error removing file from database: {e}")
        
        return RedirectResponse(url="/", status_code=302)
    else:
        return f"""
        <div style="padding: 20px; background: #f8d7da; border-radius: 10px; color: #721c24;">
            <h3>❌ File Not Found</h3>
            <p>File '{filename}' not found.</p>
            <a href='/'>← Go back</a>
        </div>
        """