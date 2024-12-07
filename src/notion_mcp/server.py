from mcp.server import Server
from mcp.types import Tool, TextContent, EmbeddedResource
import logging
from typing import Any, Sequence
import httpx
from datetime import datetime

from .tools.todo_tools import TodoTools, get_tool_definitions
from .config.settings import get_settings
import pytz
# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('notion_mcp')

# Initialize server and tools
server = Server("notion-todo")
todo_tools = TodoTools()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available todo tools"""
    return get_tool_definitions()


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | EmbeddedResource]:
    """Handle tool calls for todo management"""
    settings = get_settings()
    try:
        # raise ValueError("Test")
        if not isinstance(arguments, dict):
            raise ValueError("Invalid arguments")

        if name == "add_todo":
            task = arguments.get("task")
            when = arguments.get("when", "later")

            if not task:
                raise ValueError("Task is required")
            if when not in ["today", "later"]:
                raise ValueError("When must be 'today' or 'later'")

            return [await todo_tools.add_todo(task, when)]

        elif name == "show_specific_date_todos":
            tz = pytz.timezone(settings.tz)
            start_date = datetime.fromisoformat(
                arguments.get("start_date")).replace(tzinfo=tz)
            end_date = datetime.fromisoformat(
                arguments.get("end_date")).replace(tzinfo=tz)
            return [await todo_tools.show_todos(start_date=start_date, end_date=end_date)]

        elif name == "complete_todo":
            task_id = arguments.get("task_id")
            if not task_id:
                raise ValueError("Task ID is required")

            return [await todo_tools.complete_todo(task_id)]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except httpx.HTTPError as e:
        logger.error(f"Notion API error: {str(e)}")
        return [
            TextContent(
                type="text",
                text=f"Error during API call: {str(
                    e)}\nPlease make sure your Notion integration is properly set up and has access to the database."
            )
        ]
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return [
            TextContent(
                type="text",
                text=f"Invalid request: {str(e)}"
            )
        ]
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return [
            TextContent(
                type="text",
                text=f"An unexpected error occurred: {str(e)}"
            )
        ]


async def main():
    """Main entry point for the server"""
    from mcp.server.stdio import stdio_server

    # Verify settings are available
    settings = get_settings()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
