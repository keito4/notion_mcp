from mcp.types import TextContent
from typing import List, Optional
import json
from datetime import datetime

from ..api.notion import NotionClient
from ..models.todo import TodoCreate


class TodoTools:
    def __init__(self):
        self.client = NotionClient()

    async def add_todo(self, task: str, when: str) -> TextContent:
        date_value = datetime.now() if when.lower() == "today" else None

        todo_create = TodoCreate(
            name=task,
            date=date_value,
            # Additional fields like priority, project, repeat_task can be set if needed.
        )

        todo = await self.client.create_todo(todo_create)
        return self._format_add_message(todo.name, todo.date)

    async def show_todos(self, start_date: Optional[datetime], end_date: Optional[datetime]) -> TextContent:
        todos = await self.client.fetch_todos(start_date=start_date, end_date=end_date)
        return self._format_show_message(todos)

    async def change_todo_schedule(self, task_id: str, start_datetime: datetime, end_datetime: Optional[datetime]) -> TextContent:
        todo = await self.client.change_todo_schedule(
            task_id, start_datetime, end_datetime)
        return self._format_change_message(todo.name, start_datetime, end_datetime)

    async def complete_todo(self, task_id: str) -> TextContent:
        todo = await self.client.complete_todo(task_id)
        return self._format_complete_message(todo.name)

    def _format_add_message(self, task_name: str, date_value: Optional[datetime]) -> TextContent:
        scheduled_for = date_value.isoformat() if date_value else "later"
        return TextContent(
            type="text",
            text=f"Added todo: {task_name} scheduled for {scheduled_for}"
        )

    def _format_show_message(self, todos: List[TodoCreate]) -> TextContent:
        return TextContent(
            type="text",
            text=json.dumps([todo.model_dump()
                            for todo in todos], indent=2, default=str)
        )

    def _format_change_message(self, task_name: str, start_datetime: Optional[datetime], end_datetime: Optional[datetime]) -> TextContent:
        return TextContent(
            type="text",
            text=f"Changed todo schedule: {task_name} from {
                start_datetime} to {end_datetime}"
        )

    def _format_complete_message(self, task_name: str) -> TextContent:
        return TextContent(
            type="text",
            text=f"Marked todo as complete: {task_name}"
        )
