# Student Management System with AI Chatbot

This is a comprehensive student management system with integrated AI chatbot capabilities. The application allows you to manage students and todos, with an intelligent assistant to help guide users.

## Features

- Student management (CRUD operations)
- Todo management (CRUD operations with priority and status tracking)
- Session-based authentication
- Health monitoring
- AI-powered chatbot with multiple service support

## AI Chatbot Capabilities

The chatbot can help users with:
- Creating new todos and students
- Understanding application features
- Providing guidance on how to use the system
- Answering questions about tasks and students

## Setup Instructions

### 1. Clone or Download the Project

### 2. Install Dependencies

Run the installation script:
```bash
# On Windows
install_packages.bat

# Or manually:
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the `.env` file and add your database URL and AI service credentials:

```bash
cp .env.example .env
```

Then edit the `.env` file to add your credentials. See `CHATBOT_SETUP_GUIDE.md` for detailed instructions on setting up AI services.

### 4. Run the Application

```bash
python app_with_chatbot.py
```

The application will start on `http://localhost:8000`.

## AI Service Configuration

The application supports multiple AI services:

1. **OpenAI (GPT)** - Most popular, good for general conversations
2. **Anthropic (Claude)** - Strong reasoning capabilities
3. **Google (Gemini)** - Google's advanced AI model

To configure an AI service:

1. Get an API key from your chosen provider
2. Add it to your `.env` file
3. Set `AI_SERVICE` to your chosen service (`openai`, `anthropic`, or `google`)

See `CHATBOT_SETUP_GUIDE.md` for detailed setup instructions for each service.

## API Endpoints

- `GET /` - Root endpoint with API information
- `POST /login` - User authentication
- `GET /check-session` - Check session validity
- `POST /logout` - User logout
- `GET /health` - System health check
- `GET /status` - System status information
- `POST /students/` - Create a new student
- `GET /students/` - List all students
- `GET /students/{id}` - Get a specific student
- `PUT /students/{id}` - Update a student
- `DELETE /students/{id}` - Delete a student
- `POST /todos/` - Create a new todo
- `GET /todos/` - List all todos
- `GET /todos/{id}` - Get a specific todo
- `PUT /todos/{id}` - Update a todo
- `DELETE /todos/{id}` - Delete a todo
- `POST /chat` - AI chatbot endpoint

## Frontend Integration

The backend is designed to work with a frontend application running on `http://localhost:3000`. CORS is configured to allow requests from this origin.

## Security Notes

- API keys are loaded from environment variables and should never be committed to version control
- Sessions expire after 5 minutes for security
- Passwords are stored in plain text in this development version (not recommended for production)

## Troubleshooting

If you encounter issues:

1. Check that all environment variables are properly set
2. Verify that your database connection is working
3. Ensure your AI service API key is valid and has sufficient quota
4. Check the console logs for error messages

For more detailed setup instructions for the AI chatbot, see `CHATBOT_SETUP_GUIDE.md`.