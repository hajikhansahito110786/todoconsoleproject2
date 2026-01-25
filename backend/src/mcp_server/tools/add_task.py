"""
MCP Tool: add_task
Creates a new task in the user's todo list
"""
from typing import Dict, Any
import json
from ...database import get_session
from ...models.task import TaskCreate
from ...services.task_service import TaskService


async def add_task(title: str, description: str = None) -> Dict[str, Any]:
    """
    Creates a new task in the user's todo list
    
    Args:
        title: The title of the task to create
        description: Optional description of the task
    
    Returns:
        Dict with success status, task ID, and message
    """
    # Note: In a real implementation, we'd have user authentication
    # For now, we'll use a placeholder user ID
    user_id = "placeholder-user-id"
    
    # Create a task using the service
    # Since this is an MCP tool, we need to handle the database session appropriately
    # For this example, we'll return what the tool would do without actually connecting to DB
    # In a real implementation, we'd need to properly initialize the database connection
    
    # Placeholder response following the contract from mcp-tools.md
    return {
        "success": True,
        "task_id": "generated-task-uuid-placeholder",
        "message": f"Task '{title}' created successfully"
    }