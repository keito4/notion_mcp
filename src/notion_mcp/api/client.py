import httpx
from datetime import datetime
from typing import List, Optional

from ..config.settings import get_settings
from ..models.todo import Todo, TodoCreate
from ..utils.cache import RelationCache

from .utils import to_utc_date_str, JST
from .parsers import (
    parse_title_property, parse_checkbox_property, parse_date_property,
    parse_select_property, parse_relations_property
)
from .payloads import build_filter_condition, build_query_payload, build_properties_for_todo

settings = get_settings()


class NotionClient:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.notion_api_key}",
            "Content-Type": "application/json",
            "Notion-Version": settings.notion_version
        }
        self.cache = RelationCache()

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
                f"{settings.notion_base_url}/databases/{settings.notion_todo_database_id}/query",
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
                    "parent": {"database_id": settings.notion_todo_database_id},
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
        projects = parse_relations_property(
            self.cache, props, "Project", settings.notion_project_database_id)
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
            projects=projects,
            repeat_task=repeat_task,
            created=created_time,
            done=bool(done)
        )

    async def fetch_all_projects(self):
        projects_db_id = settings.notion_project_database_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.notion_base_url}/databases/{projects_db_id}/query",
                headers=self.headers,
                params={}
            )
            response.raise_for_status()
            data = response.json()

        project_map = {}
        for item in data.get("results", []):
            pid = item.get("id")
            props = item.get("properties", {})
            name = self._extract_title(props, "Name")
            if pid and name:
                project_map[pid] = name

        if not project_map:
            raise RuntimeError(
                "No projects found from Notion. Startup aborted.")

    def _extract_title(self, props: dict, prop_name: str) -> Optional[str]:
        title_data = props.get(prop_name, {}).get("title", [])
        if len(title_data) > 0 and "text" in title_data[0]:
            return title_data[0]["text"].get("content")
        return None
