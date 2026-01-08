import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from sqlmodel import SQLModel, Field
from typing import Optional, List
from datetime import datetime
import inspect

# We are testing the future state of models.py, so we expect these imports to fail at first.
# These models will be moved from app.py to models.py.
try:
    from models import Student, Todo, Priority, Status
except ImportError:
    # Define dummy classes to allow the test file to be parsed before the models are moved.
    class Priority(str): pass
    class Status(str): pass
    class Student(SQLModel): pass
    class Todo(SQLModel): pass


def test_student_model_has_correct_attributes():
    """
    Tests that the Student model will have the correct attributes and types
    after being refactored into models.py.
    """
    # This test will fail until the Student model is correctly defined in models.py
    student_fields = getattr(Student, 'model_fields', {})
    
    assert "id" in student_fields, "Student model should have an 'id' field"
    assert "name" in student_fields, "Student model should have a 'name' field"
    assert "email" in student_fields, "Student model should have an 'email' field"
    assert "created_at" in student_fields, "Student model should have a 'created_at' field"

    # This field should be removed
    assert "nameplz" not in student_fields, "Student model should not have the legacy 'nameplz' field"


def test_todo_model_has_correct_attributes():
    """
    Tests that the Todo model will have the correct attributes and types
    after being refactored into models.py.
    """
    # This test will fail until the Todo model is correctly defined in models.py
    todo_fields = getattr(Todo, 'model_fields', {})

    assert "id" in todo_fields, "Todo model should have an 'id' field"
    assert "title" in todo_fields, "Todo model should have a 'title' a' field"
    assert "description" in todo_fields, "Todo model should have a 'description' field"
    assert "priority" in todo_fields, "Todo model should have a 'priority' field"
    assert "status" in todo_fields, "Todo model should have a 'status' field"
    assert "due_date" in todo_fields, "Todo model should have a 'due_date' field"
    assert "student_id" in todo_fields, "Todo model should have a 'student_id' field"
    assert "created_at" in todo_fields, "Todo model should have a 'created_at' field"
    assert "completed_at" in todo_fields, "Todo model should have a 'completed_at' field"