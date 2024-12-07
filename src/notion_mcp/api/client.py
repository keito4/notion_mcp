import httpx
import logging
from datetime import datetime
from typing import List, Optional

from ..config.settings import get_settings
from ..models.todo import Todo, TodoCreate

from .utils import to_utc_date_str, JST
from .parsers import (
    parse_title_property, parse_checkbox_property, parse_date_property,
    parse_select_property
)
from .payloads import build_filter_condition, build_query_payload, build_properties_for_todo

logger = logging.getLogger(__name__)
settings = get_settings()


class NotionClient:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.notion_api_key}",
            "Content-Type": "application/json",
            "Notion-Version": settings.notion_version
        }

    async def fetch_todos(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        done: Optional[bool] = None
    ) -> List[Todo]:
        """
        Fetch todos from the Notion database with optional date filtering in JST.
        Returns a list of Todo objects.
        """
        filter_condition = build_filter_condition(
            start_date, end_date, to_utc_date_str, done)
        query_payload = build_query_payload(filter_condition)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.notion_base_url}/databases/{settings.notion_database_id}/query",
                headers=self.headers,
                json=query_payload
            )
            response.raise_for_status()
            data = response.json()

        todos = []
        for item in data.get("results", []):
            todo = self._build_todo_from_properties(item)
            if todo:
                todos.append(todo)

        return todos

    async def create_todo(self, todo_data: TodoCreate) -> Todo:
        """
        Create a new todo in Notion using a TodoCreate object.
        Returns the newly created Todo.
        """
        properties = build_properties_for_todo(todo_data, creating=True)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.notion_base_url}/pages",
                headers=self.headers,
                json={
                    "parent": {"database_id": settings.notion_database_id},
                    "properties": properties
                }
            )
            response.raise_for_status()
            data = response.json()

        return self._build_todo_from_properties(data)

    async def change_todo_schedule(
        self,
        page_id: str,
        start_datetime: datetime,
        end_datetime: Optional[datetime] = None
    ) -> Todo:
        """
        Update the 'Date' property of a todo in Notion to the given start and end datetimes.
        Returns the updated Todo object.
        """
        date_property = {
            "Date": {
                "type": "date",
                "date": {
                    "start": to_utc_date_str(start_datetime),
                    "end": to_utc_date_str(end_datetime) if end_datetime else None
                }
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{settings.notion_base_url}/pages/{page_id}",
                headers=self.headers,
                json={
                    "properties": date_property
                }
            )
            response.raise_for_status()
            data = response.json()

        return self._build_todo_from_properties(data)

    async def complete_todo(self, page_id: str) -> Todo:
        """Mark a todo as complete in Notion and return the updated Todo."""
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{settings.notion_base_url}/pages/{page_id}",
                headers=self.headers,
                json={
                    "properties": {
                        "Done": {
                            "type": "checkbox",
                            "checkbox": True
                        }
                    }
                }
            )
            response.raise_for_status()
            data = response.json()

        return self._build_todo_from_properties(data)

    def _build_todo_from_properties(self, notion_data: dict) -> Optional[Todo]:
        """
        Given a Notion page data dictionary, extract the Todo information and return a Todo object.
        If required fields are missing, returns None.
        """
        props = notion_data.get("properties", {})
        name = parse_title_property(
            props, "Name") or parse_title_property(props, "Task") or ""
        done = parse_checkbox_property(
            props, "Checkbox") or parse_checkbox_property(props, "Done")
        date_value = parse_date_property(props, "Date")
        priority = parse_select_property(props, "Priority")
        project = parse_select_property(props, "Project")
        repeat_task = parse_select_property(props, "Repeat")

        created_time_str = notion_data.get("created_time")
        created_time = None
        if created_time_str:
            try:
                created_time = datetime.fromisoformat(
                    created_time_str.replace("Z", "+00:00")).astimezone(JST)
            except ValueError:
                pass

        _id = notion_data.get("id")
        if not _id or not name:
            return None

        return Todo(
            id=_id,
            name=name,
            date=date_value,
            priority=priority,
            project=project,
            repeat_task=repeat_task,
            created=created_time,
            done=bool(done)
        )
