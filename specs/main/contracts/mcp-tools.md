# MCP Tools Specification: Todo AI Chatbot

## Overview
This document specifies the MCP (Model Context Protocol) tools available for the Todo AI Chatbot, which allow the AI agent to interact with the task management system.

## Tool: add_task
**Description**: Creates a new task in the user's todo list

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "description": "The title of the task to create"
    },
    "description": {
      "type": "string",
      "description": "Optional description of the task"
    }
  },
  "required": ["title"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Whether the task was created successfully"
    },
    "task_id": {
      "type": "string",
      "format": "uuid",
      "description": "The ID of the created task"
    },
    "message": {
      "type": "string",
      "description": "Human-readable message about the result"
    }
  },
  "required": ["success", "task_id", "message"]
}
```

**Example Request**:
```json
{
  "title": "Buy groceries",
  "description": "Get milk, bread, and eggs"
}
```

**Example Response**:
```json
{
  "success": true,
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Task 'Buy groceries' created successfully"
}
```

## Tool: list_tasks
**Description**: Retrieves the user's tasks with optional filtering

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["pending", "completed"],
      "description": "Filter tasks by status"
    }
  }
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Whether the request was processed successfully"
    },
    "tasks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "format": "uuid",
            "description": "Unique identifier for the task"
          },
          "title": {
            "type": "string",
            "description": "The task title"
          },
          "description": {
            "type": "string",
            "description": "Optional detailed description of the task"
          },
          "status": {
            "type": "string",
            "enum": ["pending", "completed"],
            "description": "Current status of the task"
          }
        },
        "required": ["id", "title", "status"]
      }
    },
    "message": {
      "type": "string",
      "description": "Human-readable message about the result"
    }
  },
  "required": ["success", "tasks", "message"]
}
```

**Example Request**:
```json
{
  "status": "pending"
}
```

**Example Response**:
```json
{
  "success": true,
  "tasks": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Buy groceries",
      "description": "Get milk, bread, and eggs",
      "status": "pending"
    },
    {
      "id": "123e4567-e89b-12d3-a456-426614174001",
      "title": "Schedule meeting",
      "status": "pending"
    }
  ],
  "message": "Retrieved 2 pending tasks"
}
```

## Tool: complete_task
**Description**: Marks a task as completed

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "format": "uuid",
      "description": "The ID of the task to mark as completed"
    }
  },
  "required": ["task_id"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Whether the task was updated successfully"
    },
    "message": {
      "type": "string",
      "description": "Human-readable message about the result"
    }
  },
  "required": ["success", "message"]
}
```

**Example Request**:
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Example Response**:
```json
{
  "success": true,
  "message": "Task 'Buy groceries' marked as completed"
}
```

## Tool: delete_task
**Description**: Removes a task from the user's todo list

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "format": "uuid",
      "description": "The ID of the task to delete"
    }
  },
  "required": ["task_id"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Whether the task was deleted successfully"
    },
    "message": {
      "type": "string",
      "description": "Human-readable message about the result"
    }
  },
  "required": ["success", "message"]
}
```

**Example Request**:
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Example Response**:
```json
{
  "success": true,
  "message": "Task 'Buy groceries' deleted successfully"
}
```

## Tool: update_task
**Description**: Modifies properties of an existing task

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "format": "uuid",
      "description": "The ID of the task to update"
    },
    "title": {
      "type": "string",
      "description": "New title for the task (optional)"
    },
    "description": {
      "type": "string",
      "description": "New description for the task (optional)"
    },
    "status": {
      "type": "string",
      "enum": ["pending", "completed"],
      "description": "New status for the task (optional)"
    }
  },
  "required": ["task_id"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Whether the task was updated successfully"
    },
    "message": {
      "type": "string",
      "description": "Human-readable message about the result"
    }
  },
  "required": ["success", "message"]
}
```

**Example Request**:
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Buy groceries and cook dinner",
  "description": "Get ingredients for pasta and prepare meal"
}
```

**Example Response**:
```json
{
  "success": true,
  "message": "Task updated successfully"
}
```