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
import glob

app = FastAPI()

UPLOAD_DIR = "/root/filesearchfolder/documents"
PERMISSION_CODE = "hk123hk123"  # Change this!

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

def query_gemini_with_documents(query: str, documents: list) -> str:
    """Query Gemini CLI with multiple documents"""
    try:
        # Create a temporary file with the query and document list
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(f"QUERY: {query}\n\n")
            temp_file.write("DOCUMENTS TO SEARCH:\n")
            for doc in documents:
                temp_file.write(f"- {doc}\n")
            temp_file.write(f"\nPlease search through all these documents and provide a comprehensive answer for: {query}")
            temp_file_path = temp_file.name
        
        # Use gemini CLI to process the query
        result = subprocess.run(
            ['gemini', f"Please analyze these documents and answer: {query}. Documents available: {', '.join(documents)}"],
            capture_output=True, 
            text=True,
            shell=True
        )
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: {result.stderr}"
            
    except Exception as e:
        return f"Error querying Gemini: {str(e)}"

# Initialize database and load documents on startup
@app.on_event("startup")
async def startup_event():
    init_database()
    loaded_docs = load_pre_existing_documents()
    print(f"🚀 System started with {len(loaded_docs)} documents ready for analysis")

@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    try:
        user = await get_current_user(request)
        username = user['username']
        
        # Get all system files
        system_files = get_system_files()
        
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
            <title>AI Document Analysis System - Gemini</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                .user-info {{ background: #e8f4fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}
                .section {{ margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 5px; }}
                input, select, button {{ padding: 10px; margin: 5px; border: 1px solid #ddd; border-radius: 5px; }}
                button {{ background: #3498db; color: white; cursor: pointer; border: none; }}
                button:hover {{ background: #2980b9; }}
                .btn-query {{ background: #27ae60; }}
                .btn-query:hover {{ background: #219653; }}
                .logout {{ background: #95a5a6; }}
                .logout:hover {{ background: #7f8c8d; }}
                .info-box {{ background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .file-list {{ max-height: 300px; overflow-y: auto; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🤖 AI Document Analysis System (Gemini)</h2>
                
                <div class="user-info">
                    <div>
                        <strong>👤 Welcome, {username}!</strong> 
                    </div>
                    <a href="/logout" class="logout" style="padding: 8px 15px; background: #95a5a6; color: white; text-decoration: none; border-radius: 5px;">🚪 Logout</a>
                </div>
                
                <div class="section">
                    <h3>📋 Available Documents</h3>
                    <div class="file-list">
                        {file_list_html if file_list_html else "<p>No documents available</p>"}
                    </div>
                </div>
                
                <div class="section">
                    <h3>🔍 Query Documents with Gemini</h3>
                    <div class="info-box">
                        <strong>💡 Powered by Google Gemini</strong>
                        <p>Ask questions about your documents and Gemini will search through all available files to find answers.</p>
                    </div>
                    <form action="/auto_query" method="post" id="queryForm">
                        <input name="query" type="text" placeholder="Enter your question about the documents..." required style="width: 400px;">
                        <input name="permission_code" type="password" placeholder="Permission Code" required>
                        <button type="submit" class="btn-query">🚀 Ask Gemini</button>
                    </form>
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
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - AI Document Analysis System</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex; 
                    justify-content: center; 
                    align-items: center; 
                    min-height: 100vh;
                }}
                .login-container {{ 
                    background: white; 
                    padding: 40px; 
                    border-radius: 15px; 
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2); 
                    width: 350px; 
                    text-align: center;
                }}
                h2 {{ 
                    color: #2c3e50; 
                    margin-bottom: 30px; 
                    font-size: 24px;
                }}
                input {{ 
                    width: 100%; 
                    padding: 12px; 
                    margin: 10px 0; 
                    border: 1px solid #ddd; 
                    border-radius: 5px; 
                    box-sizing: border-box; 
                    font-size: 16px;
                }}
                button {{ 
                    width: 100%; 
                    padding: 12px; 
                    background: #3498db; 
                    color: white; 
                    border: none; 
                    border-radius: 5px; 
                    cursor: pointer; 
                    font-size: 16px;
                    margin-top: 10px;
                }}
                button:hover {{ 
                    background: #2980b9; 
                }}
                .register-link {{ 
                    text-align: center; 
                    margin-top: 20px; 
                    color: #666;
                }}
                .register-link a {{
                    color: #3498db;
                    text-decoration: none;
                }}
                .register-link a:hover {{
                    text-decoration: underline;
                }}
                .logo {{
                    font-size: 48px;
                    margin-bottom: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="logo">🤖</div>
                <h2>AI Document Analysis</h2>
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

@app.post("/auto_query", response_class=HTMLResponse)
async def auto_query(request: Request):
    """Automated query endpoint using Gemini CLI"""
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
    
    try:
        # Get all available files
        system_files = get_system_files()
        all_filenames = [f['filename'] for f in system_files]
        
        if not all_filenames:
            return "<p>No documents available for querying.</p>"
        
        print(f"🔍 Gemini Query: {query}")
        print(f"📚 Searching across {len(all_filenames)} documents")
        
        # Use Gemini CLI to query documents
        response = query_gemini_with_documents(query, all_filenames)
        
        formatted_result = response.replace('\n', '<br>')
        
        return f"""
        <div style="padding: 20px; background: #f8f9fa; border-radius: 10px; margin: 20px 0;">
            <h3 style="color: #2c3e50;">🎉 Gemini Query Results</h3>
            <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #27ae60;">
                <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                    <strong>✅ Query Processed Successfully</strong>
                    <p style="margin: 5px 0 0 0; font-size: 0.9em;">
                        Powered by Google Gemini • {len(all_filenames)} documents searched
                    </p>
                </div>
                <p><strong>❓ Your Query:</strong> {query}</p>
                <p><strong>📊 Documents Analyzed:</strong> {len(all_filenames)} files</p>
                <hr>
                <p><strong>🤖 Gemini Response:</strong></p>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; border: 1px solid #e9ecef; white-space: pre-wrap; line-height: 1.6;">
                    {formatted_result}
                </div>
            </div>
            <div style="margin-top: 20px;">
                <a href='/' style="background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">← New Query</a>
            </div>
        </div>
        """
            
    except Exception as e:
        return f"""
        <div style="padding: 20px; background: #f8d7da; border-radius: 10px; color: #721c24;">
            <h3>❌ Processing Error</h3>
            <p>Error during query processing: {str(e)}</p>
            <a href='/' style="color: #721c24; text-decoration: none; padding: 8px 15px; background: #e74c3c; color: white; border-radius: 5px;">← Go back</a>
        </div>
        """

# Keep other existing endpoints (login, register, logout) unchanged
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

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        timeout_keep_alive=600
    )