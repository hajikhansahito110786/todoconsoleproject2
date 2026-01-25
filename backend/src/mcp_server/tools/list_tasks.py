"""
MCP Tool: list_tasks
Retrieves the user's tasks with optional filtering
"""
from typing import Dict, Any, List, Optional
import json
from ...database import get_session
from ...services.task_service import TaskService


async def list_tasks(status: str = None) -> Dict[str, Any]:
    """
    Retrieves the user's tasks with optional filtering
    
    Args:
        status: Optional filter for task status (pending, completed)
    
    Returns:
        Dict with success status, list of tasks, and message
    """
    # Note: In a real implementation, we'd have user authentication
    # For now, we'll use a placeholder user ID
    user_id = "placeholder-user-id"
    
    # Get tasks using the service
    # For this example, we'll return placeholder data
    # In a real implementation, we'd need to properly initialize the database connection
    
    # Placeholder response following the contract from mcp-tools.md
    tasks = [
        {
            "id": "task-uuid-placeholder-1",
            "title": "Sample task 1",
            "description": "This is a sample task",
            "status": "pending"
        },
        {
            "id": "task-uuid-placeholder-2", 
            "title": "Sample task 2",
            "status": "completed"
        }
    ]
    
    # Filter by status if provided
    if status:
        tasks = [task for task in tasks if task["status"] == status]
    
    return {
        "success": True,
        "tasks": tasks,
        "message": f"Retrieved {len(tasks)} tasks"
    }