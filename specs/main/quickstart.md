# Quickstart Guide: Todo AI Chatbot

## Overview
This guide provides instructions for setting up and running the Todo AI Chatbot locally.

## Prerequisites
- Python 3.11+
- pip package manager
- PostgreSQL (or access to Neon Serverless PostgreSQL)
- OpenAI API key
- MCP server dependencies

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd todowithchatbot
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the backend directory with the following variables:

```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/tododb
NEON_DB_URL=your_neon_db_connection_string
SECRET_KEY=your_secret_key_for_authentication
MCP_SERVER_PORT=3000
```

### 5. Set Up Database
```bash
# Run database migrations
python -m alembic upgrade head
```

### 6. Run the Application
```bash
# Start the backend server
uvicorn src.api.main:app --reload --port 8000

# In a separate terminal, start the MCP server
python -m src.mcp_server.server
```

### 7. Run the Frontend
```bash
cd ../frontend
npm install
npm run dev
```

## Usage

### Interacting with the Chatbot
1. Navigate to `http://localhost:3000` in your browser
2. Authenticate with your credentials
3. Start chatting with the bot using natural language:
   - "Add a task to buy groceries"
   - "Show me my tasks"
   - "Mark the meeting as complete"
   - "Delete the old task"

### MCP Server Tools
The MCP server exposes the following tools for AI agents:
- `add_task`: Creates a new task
- `list_tasks`: Retrieves user's tasks with optional filters
- `complete_task`: Marks a task as completed
- `delete_task`: Removes a task
- `update_task`: Modifies task properties

## Development

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm run test
```

### Adding New MCP Tools
1. Create a new tool file in `src/mcp_server/tools/`
2. Implement the tool following the existing pattern
3. Register the tool in the MCP server configuration
4. Update the agent to recognize when to use the new tool

### Database Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head
```

## Troubleshooting

### Common Issues
- **Database Connection**: Ensure PostgreSQL is running and credentials are correct
- **OpenAI API**: Verify your API key is valid and has sufficient quota
- **MCP Server**: Confirm the server is running and accessible to the AI agent

### Logs
- Backend logs: Check console output when running uvicorn
- Database logs: Check PostgreSQL logs
- Frontend logs: Check browser developer console