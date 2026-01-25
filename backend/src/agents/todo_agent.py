"""
Todo Agent Implementation
This module implements the AI agent that interacts with users through natural language
and uses MCP tools to manage tasks.
"""
import asyncio
from typing import Dict, Any, Optional
from openai import OpenAI
import json


class TodoAgent:
    def __init__(self, openai_client: OpenAI, mcp_base_url: str = "http://localhost:3000"):
        """
        Initialize the Todo Agent
        
        Args:
            openai_client: Initialized OpenAI client
            mcp_base_url: Base URL for the MCP server
        """
        self.openai_client = openai_client
        self.mcp_base_url = mcp_base_url
        self.tools_map = {
            "add_task": self._call_add_task,
            "list_tasks": self._call_list_tasks,
            "complete_task": self._call_complete_task,
            "delete_task": self._call_delete_task,
            "update_task": self._call_update_task
        }

    async def process_message(self, user_message: str, conversation_context: Optional[Dict] = None) -> str:
        """
        Process a user message and return an appropriate response
        
        Args:
            user_message: The message from the user
            conversation_context: Context from the ongoing conversation
            
        Returns:
            The agent's response to the user
        """
        # Determine the appropriate action based on the user's message
        action = self._determine_action(user_message)
        
        if action and action in self.tools_map:
            # Call the appropriate MCP tool
            tool_result = await self.tools_map[action](user_message)
            
            # Generate a natural language response based on the tool result
            response = self._generate_response(action, tool_result, user_message)
        else:
            # If no specific action is needed, generate a general response
            response = self._generate_general_response(user_message)
        
        return response

    def _determine_action(self, message: str) -> Optional[str]:
        """
        Determine which action to take based on the user's message
        
        Args:
            message: The user's message
            
        Returns:
            The action to take (e.g., "add_task", "list_tasks", etc.) or None
        """
        message_lower = message.lower()
        
        # Simple keyword matching for demonstration
        # In a real implementation, this would use more sophisticated NLP
        if any(word in message_lower for word in ["add", "create", "new", "remember"]):
            return "add_task"
        elif any(word in message_lower for word in ["show", "list", "see", "my tasks"]):
            return "list_tasks"
        elif any(word in message_lower for word in ["done", "complete", "finish", "completed"]):
            return "complete_task"
        elif any(word in message_lower for word in ["delete", "remove", "cancel"]):
            return "delete_task"
        elif any(word in message_lower for word in ["change", "update", "rename", "modify"]):
            return "update_task"
        
        return None

    async def _call_add_task(self, message: str) -> Dict[str, Any]:
        """
        Call the add_task MCP tool
        
        Args:
            message: The user's message
            
        Returns:
            Result from the MCP tool
        """
        # Extract task title and description from the message
        # This is a simplified extraction - in practice, this would use more advanced NLP
        title = self._extract_task_title(message)
        description = self._extract_task_description(message)
        
        # In a real implementation, this would make an HTTP call to the MCP server
        # For now, we'll simulate the call
        return {
            "success": True,
            "task_id": "generated-task-uuid",
            "message": f"Task '{title}' created successfully"
        }

    async def _call_list_tasks(self, message: str) -> Dict[str, Any]:
        """
        Call the list_tasks MCP tool
        
        Args:
            message: The user's message
            
        Returns:
            Result from the MCP tool
        """
        # Determine if the user wants to filter by status
        status_filter = None
        if "completed" in message.lower():
            status_filter = "completed"
        elif "pending" in message.lower():
            status_filter = "pending"
        
        # In a real implementation, this would make an HTTP call to the MCP server
        # For now, we'll simulate the call
        return {
            "success": True,
            "tasks": [
                {"id": "task1", "title": "Sample task 1", "status": "pending"},
                {"id": "task2", "title": "Sample task 2", "status": "completed"}
            ],
            "message": "Retrieved 2 tasks"
        }

    async def _call_complete_task(self, message: str) -> Dict[str, Any]:
        """
        Call the complete_task MCP tool
        
        Args:
            message: The user's message
            
        Returns:
            Result from the MCP tool
        """
        # Extract task ID or title from the message
        # This is a simplified extraction
        task_identifier = self._extract_task_identifier(message)
        
        # In a real implementation, this would make an HTTP call to the MCP server
        # For now, we'll simulate the call
        return {
            "success": True,
            "message": f"Task '{task_identifier}' marked as completed"
        }

    async def _call_delete_task(self, message: str) -> Dict[str, Any]:
        """
        Call the delete_task MCP tool
        
        Args:
            message: The user's message
            
        Returns:
            Result from the MCP tool
        """
        # Extract task ID or title from the message
        # This is a simplified extraction
        task_identifier = self._extract_task_identifier(message)
        
        # In a real implementation, this would make an HTTP call to the MCP server
        # For now, we'll simulate the call
        return {
            "success": True,
            "message": f"Task '{task_identifier}' deleted successfully"
        }

    async def _call_update_task(self, message: str) -> Dict[str, Any]:
        """
        Call the update_task MCP tool
        
        Args:
            message: The user's message
            
        Returns:
            Result from the MCP tool
        """
        # Extract task ID or title and new details from the message
        # This is a simplified extraction
        task_identifier = self._extract_task_identifier(message)
        
        # In a real implementation, this would make an HTTP call to the MCP server
        # For now, we'll simulate the call
        return {
            "success": True,
            "message": f"Task '{task_identifier}' updated successfully"
        }

    def _extract_task_title(self, message: str) -> str:
        """
        Extract the task title from a user message
        
        Args:
            message: The user's message
            
        Returns:
            The extracted task title
        """
        # Simplified extraction - in practice, this would use more advanced NLP
        # Look for phrases like "add task to..." or "create task..."
        if "to" in message:
            return message.split("to", 1)[1].strip()
        else:
            return message.strip()

    def _extract_task_description(self, message: str) -> Optional[str]:
        """
        Extract the task description from a user message
        
        Args:
            message: The user's message
            
        Returns:
            The extracted task description or None
        """
        # For now, we'll not extract descriptions separately
        # In a real implementation, this would use more advanced NLP
        return None

    def _extract_task_identifier(self, message: str) -> str:
        """
        Extract the task identifier from a user message
        
        Args:
            message: The user's message
            
        Returns:
            The extracted task identifier
        """
        # Simplified extraction - in practice, this would use more advanced NLP
        # and possibly reference conversation history to identify the task
        return "identified-task"

    def _generate_response(self, action: str, tool_result: Dict[str, Any], original_message: str) -> str:
        """
        Generate a natural language response based on the tool result
        
        Args:
            action: The action that was taken
            tool_result: The result from the MCP tool
            original_message: The user's original message
            
        Returns:
            A natural language response
        """
        if tool_result.get("success"):
            if action == "add_task":
                return f"I've added the task to your list."
            elif action == "list_tasks":
                tasks = tool_result.get("tasks", [])
                if tasks:
                    task_titles = [task["title"] for task in tasks]
                    return f"Here are your tasks: {', '.join(task_titles)}"
                else:
                    return "You don't have any tasks right now."
            elif action == "complete_task":
                return "I've marked that task as completed!"
            elif action == "delete_task":
                return "I've removed that task from your list."
            elif action == "update_task":
                return "I've updated that task for you."
        else:
            error_msg = tool_result.get("message", "An error occurred")
            return f"Sorry, I couldn't do that. {error_msg}"

    def _generate_general_response(self, message: str) -> str:
        """
        Generate a general response when no specific action is needed
        
        Args:
            message: The user's message
            
        Returns:
            A general response
        """
        # Use OpenAI to generate a response for general conversation
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for managing tasks. Respond to the user's message."},
                    {"role": "user", "content": message}
                ],
                max_tokens=100
            )
            return response.choices[0].message.content
        except Exception:
            return "I understand. How else can I help you with your tasks?"


# Example usage
async def main():
    # Initialize OpenAI client
    client = OpenAI(api_key="your-openai-api-key")
    
    # Create the agent
    agent = TodoAgent(client)
    
    # Example conversation
    user_input = "Add a task to buy groceries"
    response = await agent.process_message(user_input)
    print(f"User: {user_input}")
    print(f"Agent: {response}")


if __name__ == "__main__":
    asyncio.run(main())