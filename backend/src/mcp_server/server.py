"""
MCP (Model Context Protocol) Server for the Todo AI Chatbot
This server exposes task operations as tools that the AI agent can use.
"""
import asyncio
from typing import Dict, Any
import json
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn


# Import the tools
from .tools.add_task import add_task
from .tools.list_tasks import list_tasks
from .tools.complete_task import complete_task
from .tools.delete_task import delete_task
from .tools.update_task import update_task


# Dictionary to hold our tools
TOOLS = {
    "add_task": add_task,
    "list_tasks": list_tasks,
    "complete_task": complete_task,
    "delete_task": delete_task,
    "update_task": update_task
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("MCP Server starting up...")
    yield
    # Shutdown
    print("MCP Server shutting down...")


# Create FastAPI app to serve as MCP server
app = FastAPI(
    title="Todo AI Chatbot MCP Server",
    description="MCP server exposing task operations as tools",
    version="0.1.0",
    lifespan=lifespan
)


@app.post("/mcp/tool/call")
async def call_tool(request: Dict[str, Any]):
    """Endpoint to call MCP tools"""
    tool_name = request.get("method")
    params = request.get("params", {})

    if tool_name not in TOOLS:
        return {"error": f"Unknown tool: {tool_name}", "success": False}

    try:
        # Call the appropriate tool function
        import inspect
        if inspect.iscoroutinefunction(TOOLS[tool_name]):
            result = await TOOLS[tool_name](**params)
        else:
            result = TOOLS[tool_name](**params)
        return {"result": result, "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}


@app.get("/mcp/tools/list")
async def list_tools():
    """Endpoint to list available tools"""
    return {"tools": list(TOOLS.keys()), "count": len(TOOLS)}


def run_mcp_server(host: str = "localhost", port: int = 3000):
    """Run the MCP server"""
    print(f"Starting MCP server on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    run_mcp_server()