import httpx
import logging
from datetime import datetime
from typing import List, Optional

from ..config.settings import get_settings
from ..models.todo import Todo, TodoCreate, TodoResponse

logger = logging.getLogger(__name__)
settings = get_settings()


class NotionClient:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.notion_api_key}",
            "Content-Type": "application/json",
            "Notion-Version": settings.notion_version
        }

    async def fetch_todos(self) -> List[Todo]:
        """Fetch todos from Notion database"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.notion_base_url}/databases/{settings.notion_database_id}/query",
                headers=self.headers,
                json={
                    "sorts": [
                        {
                            "timestamp": "created_time",
                            "direction": "descending"
                        }
                    ]
                }
            )
            response.raise_for_status()
            data = response.json()

            todos = []
            for item in data.get("results", []):
                props = item["properties"]

                # name
                name = ""
                if (
                    "Name" in props and
                    "title" in props["Name"] and
                    len(props["Name"]["title"]) > 0 and
                    "text" in props["Name"]["title"][0]
                ):
                    name = props["Name"]["title"][0]["text"]["content"]

                # done
                done = props.get("Checkbox", {}).get("checkbox", False)

                # date
                date_value = None
                if (
                    "Date" in props and
                    props["Date"].get("date") and
                    props["Date"]["date"].get("start")
                ):
                    date_str = props["Date"]["date"]["start"]
                    try:
                        date_value = datetime.fromisoformat(
                            date_str.replace("Z", "+00:00"))
                    except ValueError:
                        # 日付形式でない場合などはスキップ
                        pass

                # priority
                priority = None
                if (
                    "Priority" in props and
                    props["Priority"].get("select") and
                    props["Priority"]["select"].get("name")
                ):
                    priority = props["Priority"]["select"]["name"]

                # project
                project = None
                if (
                    "Project" in props and
                    props["Project"].get("select") and
                    props["Project"]["select"].get("name")
                ):
                    project = props["Project"]["select"]["name"]

                # repeat_task
                repeat_task = None
                if (
                    "Repeat" in props and
                    props["Repeat"].get("select") and
                    props["Repeat"]["select"].get("name")
                ):
                    repeat_task = props["Repeat"]["select"]["name"]

                created_time = datetime.fromisoformat(
                    item["created_time"].replace("Z", "+00:00"))

                todo = Todo(
                    id=item["id"],
                    name=name,
                    date=date_value,
                    priority=priority,
                    project=project,
                    repeat_task=repeat_task,
                    created=created_time,
                    done=done
                )
                todos.append(todo)

            return todos

    async def create_todo(self, todo_data: TodoCreate) -> Todo:
        """Create a new todo in Notion"""
        # Notionに送信するpropertiesを作成
        properties = {
            "Task": {
                "type": "title",
                "title": [{"type": "text", "text": {"content": todo_data.name}}]
            },
            "Checkbox": {
                "type": "checkbox",
                "checkbox": False
            }
        }

        if todo_data.date:
            properties["Date"] = {
                "type": "date",
                "date": {"start": todo_data.date.isoformat()}
            }

        if todo_data.priority:
            properties["Priority"] = {
                "type": "select",
                "select": {"name": todo_data.priority}
            }

        if todo_data.project:
            properties["Project"] = {
                "type": "select",
                "select": {"name": todo_data.project}
            }

        if todo_data.repeat_task:
            properties["Repeat"] = {
                "type": "select",
                "select": {"name": todo_data.repeat_task}
            }

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

            props = data["properties"]

            # 作成後の値を取得
            name = ""
            if (
                "Task" in props and
                "title" in props["Task"] and
                len(props["Task"]["title"]) > 0 and
                "text" in props["Task"]["title"][0]
            ):
                name = props["Task"]["title"][0]["text"]["content"]

            done = props.get("Checkbox", {}).get("checkbox", False)

            date_value = None
            if (
                "Date" in props and
                props["Date"].get("date") and
                props["Date"]["date"].get("start")
            ):
                date_str = props["Date"]["date"]["start"]
                try:
                    date_value = datetime.fromisoformat(
                        date_str.replace("Z", "+00:00"))
                except ValueError:
                    pass

            priority = None
            if (
                "Priority" in props and
                props["Priority"].get("select") and
                props["Priority"]["select"].get("name")
            ):
                priority = props["Priority"]["select"]["name"]

            project = None
            if (
                "Project" in props and
                props["Project"].get("select") and
                props["Project"]["select"].get("name")
            ):
                project = props["Project"]["select"]["name"]

            repeat_task = None
            if (
                "Repeat" in props and
                props["Repeat"].get("select") and
                props["Repeat"]["select"].get("name")
            ):
                repeat_task = props["Repeat"]["select"]["name"]

            created_time = datetime.fromisoformat(
                data["created_time"].replace("Z", "+00:00"))

            return Todo(
                id=data["id"],
                name=name,
                date=date_value,
                priority=priority,
                project=project,
                repeat_task=repeat_task,
                created=created_time,
                done=done
            )

    async def complete_todo(self, page_id: str) -> Todo:
        """Mark a todo as complete in Notion"""
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{settings.notion_base_url}/pages/{page_id}",
                headers=self.headers,
                json={
                    "properties": {
                        "Checkbox": {
                            "type": "checkbox",
                            "checkbox": True
                        }
                    }
                }
            )
            response.raise_for_status()
            data = response.json()

            props = data["properties"]

            name = ""
            if (
                "Task" in props and
                "title" in props["Task"] and
                len(props["Task"]["title"]) > 0 and
                "text" in props["Task"]["title"][0]
            ):
                name = props["Task"]["title"][0]["text"]["content"]

            done = props.get("Checkbox", {}).get("checkbox", False)

            date_value = None
            if (
                "Date" in props and
                props["Date"].get("date") and
                props["Date"]["date"].get("start")
            ):
                date_str = props["Date"]["date"]["start"]
                try:
                    date_value = datetime.fromisoformat(
                        date_str.replace("Z", "+00:00"))
                except ValueError:
                    pass

            priority = None
            if (
                "Priority" in props and
                props["Priority"].get("select") and
                props["Priority"]["select"].get("name")
            ):
                priority = props["Priority"]["select"]["name"]

            project = None
            if (
                "Project" in props and
                props["Project"].get("select") and
                props["Project"]["select"].get("name")
            ):
                project = props["Project"]["select"]["name"]

            repeat_task = None
            if (
                "Repeat" in props and
                props["Repeat"].get("select") and
                props["Repeat"]["select"].get("name")
            ):
                repeat_task = props["Repeat"]["select"]["name"]

            created_time = datetime.fromisoformat(
                data["created_time"].replace("Z", "+00:00"))

            return Todo(
                id=data["id"],
                name=name,
                date=date_value,
                priority=priority,
                project=project,
                repeat_task=repeat_task,
                created=created_time,
                done=done
            )
