import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, SQLModel
from datetime import datetime

# Adjust path to import app and models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import from the main application file
from app import app
# Import get_session from models.py, which was previously in app.py logic
from models import Student, Todo, Priority, Status, get_session as original_get_session
from schemas import TodoCreate, TodoRead # Import from our refactored schemas.py


# Setup a test database engine
# Using a file-based sqlite for easy inspection if needed, or ":memory:" for a pure in-memory database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db" 
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False) # echo=False for cleaner test output

# Override the get_session dependency
@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine) # Create tables
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine) # Drop tables after test

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        yield session

    app.dependency_overrides[original_get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_create_todo(client: TestClient):
    todo_data = {
        "title": "Buy groceries",
        "description": "Milk, eggs, bread",
        "priority": Priority.HIGH.value, # Send enum value
        "status": Status.TODO.value,     # Send enum value
        "due_date": datetime.now().isoformat(), # FastAPI expects ISO format
    }
    response = client.post("/todos/", json=todo_data)
    assert response.status_code == 200
    
    created_todo = response.json()
    assert created_todo["title"] == todo_data["title"]
    assert created_todo["description"] == todo_data["description"]
    assert created_todo["priority"] == todo_data["priority"]
    assert created_todo["status"] == todo_data["status"]
    # Check if a valid ID was assigned
    assert "id" in created_todo
    assert created_todo["id"] is not None

    # Verify that the created_at field is present and not None
    assert "created_at" in created_todo
    assert created_todo["created_at"] is not None

    # Optionally, validate with the Read schema
    TodoRead(**created_todo)


def test_read_todos(client: TestClient):
    # First create a todo
    todo_data = {
        "title": "Read all the books",
        "priority": Priority.MEDIUM.value,
        "status": Status.IN_PROGRESS.value,
    }
    client.post("/todos/", json=todo_data)

    response = client.get("/todos/")
    assert response.status_code == 200
    todos = response.json()
    assert isinstance(todos, list)
    assert len(todos) > 0
    assert any(todo["title"] == todo_data["title"] for todo in todos)

    # Optionally, validate the first todo with the Read schema
    TodoRead(**todos[0])
