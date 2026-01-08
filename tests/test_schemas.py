import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from pydantic import BaseModel, ValidationError
from datetime import datetime
from typing import Optional, List, Type
from enum import Enum

# We are testing the future state of schemas.py.
# These schemas and enums will be moved from app.py to schemas.py.
try:
    from schemas import (
        StudentCreate, StudentUpdate, StudentRead,
        TodoCreate, TodoUpdate, TodoRead,
    )
    # Import Priority and Status from models.py for actual enum definitions
    from models import Priority, Status 
except ImportError:
    # Define dummy classes/enums to allow the test file to be parsed before the schemas are moved.
    class Priority(str, Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
    class Status(str, Enum):
        TODO = "todo"
        IN_PROGRESS = "in_progress"
        DONE = "done"
    class StudentCreate(BaseModel): pass
    class StudentUpdate(BaseModel): pass
    class StudentRead(BaseModel): pass
    class TodoCreate(BaseModel): pass
    class TodoUpdate(BaseModel): pass
    class TodoRead(BaseModel): pass


def test_priority_enum_definition():
    assert issubclass(Priority, str)
    assert issubclass(Priority, Enum)
    assert Priority.LOW == "low"
    assert Priority.MEDIUM == "medium"
    assert Priority.HIGH == "high"

def test_status_enum_definition():
    assert issubclass(Status, str)
    assert issubclass(Status, Enum)
    assert Status.TODO == "todo"
    assert Status.IN_PROGRESS == "in_progress"
    assert Status.DONE == "done"

def test_student_create_schema():
    fields = StudentCreate.model_fields
    assert "name" in fields and fields["name"].is_required()
    assert "email" in fields and fields["email"].is_required()

    # Test validation
    with pytest.raises(ValidationError):
        StudentCreate(email="invalid") # missing name
    with pytest.raises(ValidationError):
        StudentCreate(name="test") # missing email
    
    student = StudentCreate(name="Test Student", email="test@example.com")
    assert student.name == "Test Student"
    assert student.email == "test@example.com"


def test_student_update_schema():
    fields = StudentUpdate.model_fields
    assert "name" in fields and not fields["name"].is_required()
    assert "email" in fields and not fields["email"].is_required()

    student_update = StudentUpdate(name="Updated Name")
    assert student_update.name == "Updated Name"
    assert student_update.email is None

    student_update = StudentUpdate(email="updated@example.com")
    assert student_update.email == "updated@example.com"
    assert student_update.name is None


def test_student_read_schema():
    fields = StudentRead.model_fields
    assert "id" in fields and fields["id"].is_required()
    assert "name" in fields and fields["name"].is_required()
    assert "email" in fields and fields["email"].is_required()
    assert "created_at" in fields and fields["created_at"].is_required()

    # Test validation (minimal for Read models)
    now = datetime.utcnow()
    student_read = StudentRead(id=1, name="Read Student", email="read@example.com", created_at=now)
    assert student_read.id == 1
    assert student_read.name == "Read Student"
    assert student_read.email == "read@example.com"
    assert student_read.created_at == now


def test_todo_create_schema():
    fields = TodoCreate.model_fields
    assert "title" in fields and fields["title"].is_required()
    assert "description" in fields and not fields["description"].is_required()
    assert "priority" in fields and not fields["priority"].is_required()
    assert "status" in fields and not fields["status"].is_required()
    assert "due_date" in fields and not fields["due_date"].is_required()
    assert "student_id" in fields and not fields["student_id"].is_required()

    # Test defaults
    todo = TodoCreate(title="New Task")
    assert todo.title == "New Task"
    assert todo.priority == Priority.MEDIUM
    assert todo.status == Status.TODO

    # Test validation
    with pytest.raises(ValidationError):
        TodoCreate(description="only desc") # missing title


def test_todo_update_schema():
    fields = TodoUpdate.model_fields
    assert "title" in fields and not fields["title"].is_required()
    assert "priority" in fields and not fields["priority"].is_required()
    assert "status" in fields and not fields["status"].is_required()
    assert "due_date" in fields and not fields["due_date"].is_required()
    assert "student_id" in fields and not fields["student_id"].is_required()

    todo_update = TodoUpdate(title="Updated Title", status=Status.DONE)
    assert todo_update.title == "Updated Title"
    assert todo_update.status == Status.DONE
    assert todo_update.description is None


def test_todo_read_schema():
    fields = TodoRead.model_fields
    assert "id" in fields and fields["id"].is_required()
    assert "title" in fields and fields["title"].is_required()
    assert "priority" in fields and fields["priority"].is_required()
    assert "status" in fields and fields["status"].is_required()
    assert "created_at" in fields and fields["created_at"].is_required()

    # Assert that completed_at, description, due_date, student_id exist and can accept None
    assert "completed_at" in fields
    assert "description" in fields
    assert "due_date" in fields
    assert "student_id" in fields

    # Test that model can be instantiated with optional fields as None
    todo_read_data = {
        "id": 1,
        "title": "Read Todo",
        "priority": Priority.LOW,
        "status": Status.IN_PROGRESS,
        "created_at": datetime.utcnow(),
        "description": None,
        "due_date": None,
        "student_id": None,
        "completed_at": None, # Explicitly pass None for all optional fields
    }
    todo_read_instance = TodoRead(**todo_read_data)
    assert todo_read_instance.id == 1
    assert todo_read_instance.title == "Read Todo"
    assert todo_read_instance.priority == Priority.LOW
    assert todo_read_instance.status == Status.IN_PROGRESS
    assert todo_read_instance.created_at is not None
    assert todo_read_instance.description is None
    assert todo_read_instance.due_date is None
    assert todo_read_instance.student_id is None
    assert todo_read_instance.completed_at is None
