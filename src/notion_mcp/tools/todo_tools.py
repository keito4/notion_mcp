from mcp.types import Tool, TextContent
from typing import List
import json
from datetime import datetime

from ..api.notion import NotionClient
from ..models.todo import TodoCreate


def get_tool_definitions() -> List[Tool]:
    """Get list of available todo tools"""
    return [
        Tool(
            name="add_todo",
            description="Add a new todo item",
            inputSchema={
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The todo task description"
                    },
                    "when": {
                        "type": "string",
                        "description": "When the task should be done (today or later)",
                        "enum": ["today", "later"]
                    }
                },
                "required": ["task", "when"]
            }
        ),
        Tool(
            name="show_all_todos",
            description="Show all todo items from Notion",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="show_today_todos",
            description="Show today's todo items from Notion",
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {"type": "integer"},
                    "month": {"type": "integer"},
                    "day": {"type": "integer"}
                },
                "required": []
            }
        ),
        Tool(
            name="complete_todo",
            description="Mark a todo item as complete",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The ID of the todo task to mark as complete"
                    }
                },
                "required": ["task_id"]
            }
        )
    ]


class TodoTools:
    def __init__(self):
        self.client = NotionClient()

    async def add_todo(self, task: str, when: str) -> TextContent:
        """Add a new todo item"""

        # when="today" の場合は今日の日付、"later"の場合は日付指定なしとする例
        date_value = datetime.now() if when.lower() == "today" else None

        todo_create = TodoCreate(
            name=task,
            date=date_value,
            # 必要に応じてpriority, project, repeat_taskを設定可能
            # priority="High",
            # project="MyProject",
            # repeat_task="Weekly"
        )

        todo = await self.client.create_todo(todo_create)
        return TextContent(
            type="text",
            text=f"Added todo: {todo.name} scheduled for {
                todo.date if todo.date else 'later'}"
        )

    async def show_todos(self, date: datetime | None = None) -> TextContent:
        """Show todos, optionally filtered to a specific date"""
        todos = await self.client.fetch_todos()

        if date:
            todos = [todo for todo in todos if todo.date and todo.date.date()
                     == date.date()]

        return TextContent(
            type="text",
            text=json.dumps([todo.model_dump()
                            for todo in todos], indent=2, default=str)
        )

    async def complete_todo(self, task_id: str) -> TextContent:
        """Mark a todo as complete"""
        todo = await self.client.complete_todo(task_id)
        return TextContent(
            type="text",
            text=f"Marked todo as complete: {todo.name}"
        )
