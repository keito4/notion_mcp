from mcp.types import TextContent
from typing import Sequence
from datetime import datetime
import pytz

from .todo_tools import TodoTools
from ..config.settings import get_settings

todo_tools = TodoTools()


async def handle_add_todo(arguments: dict) -> Sequence[TextContent]:
    task = arguments.get("task")
    datetime = arguments.get("datetime", "later")

    if not task:
        raise ValueError("Task is required")
    if datetime not in ["today", "later"]:
        raise ValueError("datetime must be 'today' or 'later'")

    return [await todo_tools.add_todo(task, datetime)]


async def handle_show_specific_date_todos(arguments: dict) -> Sequence[TextContent]:
    settings = get_settings()
    tz = pytz.timezone(settings.tz)

    start_str = arguments.get("start_date")
    end_str = arguments.get("end_date")

    start_date = datetime.fromisoformat(start_str).replace(
        tzinfo=tz) if start_str else None
    end_date = datetime.fromisoformat(end_str).replace(
        tzinfo=tz) if end_str else None

    return [await todo_tools.show_todos(start_date=start_date, end_date=end_date)]


async def handle_change_todo_schedule(arguments: dict) -> Sequence[TextContent]:
    settings = get_settings()
    tz = pytz.timezone(settings.tz)

    task_id = arguments.get("task_id")
    start_datetime = arguments.get("start_datetime")
    end_datetime = arguments.get("end_datetime")

    if not task_id:
        raise ValueError("Task ID is required")
    if not start_datetime or not end_datetime:
        raise ValueError("start_datetime and end_datetime are required")

    start_datetime = datetime.fromisoformat(start_datetime).replace(tzinfo=tz)
    end_datetime = datetime.fromisoformat(end_datetime).replace(tzinfo=tz)

    return [await todo_tools.change_todo_schedule(task_id, start_datetime, end_datetime)]


async def handle_complete_todo(arguments: dict) -> Sequence[TextContent]:
    task_id = arguments.get("task_id")
    if not task_id:
        raise ValueError("Task ID is required")

    return [await todo_tools.complete_todo(task_id)]


TOOL_HANDLERS = {
    "add_todo": {
        "handler": handle_add_todo,
        "description": "Add a new todo item",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "The todo task description"
                },
            },
            "required": ["task"]
        }
    },
    "show_specific_date_todos": {
        "handler": handle_show_specific_date_todos,
        "description": "Show todo items from Notion on a specific date range",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date (YYYY-MM-DDTHH:MM:SS.SSSSSS). Can be omitted."
                },
                "end_date": {
                    "type": "string",
                    "description": "End date (YYYY-MM-DDTHH:MM:SS.SSSSSS). Can be omitted."
                }
            },
            "required": ["start_date", "end_date"]
        }
    },
    "change_todo_schedule": {
        "handler": handle_change_todo_schedule,
        "description": "Change the schedule of a todo item",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "The ID of the todo task to change the schedule"
                },
                "start_datetime": {
                    "type": "string",
                    "description": "The datetime the task should be done (YYYY-MM-DDTHH:MM:SS.SSSSSS)"
                },
                "end_datetime": {
                    "type": "string",
                    "description": "The datetime the task should be done (YYYY-MM-DDTHH:MM:SS.SSSSSS). If omitted, the task will be scheduled for the entire day. "
                                   "The end_datetime must be at least 30 minutes after the start_datetime."
                }
            },
            "required": ["task_id", "start_datetime", "end_datetime"]
        }
    },
    "complete_todo": {
        "handler": handle_complete_todo,
        "description": "Mark a todo item as complete",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "The ID of the todo task to mark as complete"
                }
            },
            "required": ["task_id"]
        }
    }
}
