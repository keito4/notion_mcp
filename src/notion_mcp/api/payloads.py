from datetime import datetime
from ..models.todo import TodoCreate


def build_filter_condition(start_date: datetime, end_date: datetime, to_utc_date_str, done: bool) -> dict:
    filter_condition = {
        "and": []
    }
    if done is not None:
        filter_condition["and"].append(
            {"property": "Done", "checkbox": {"equals": done}})

    if start_date:
        filter_condition["and"].append(
            {"property": "Date", "date": {
                "on_or_after": to_utc_date_str(start_date)}}
        )
    if end_date:
        filter_condition["and"].append(
            {"property": "Date", "date": {
                "on_or_before": to_utc_date_str(end_date)}}
        )
    return filter_condition


def build_query_payload(filter_condition: dict) -> dict:
    """Build the payload for the Notion query call."""
    query_payload = {
        "sorts": [
            {
                "timestamp": "created_time",
                "direction": "descending"
            }
        ]
    }
    if filter_condition:
        query_payload["filter"] = filter_condition
    return query_payload


def build_properties_for_todo(todo_data: TodoCreate, creating: bool = False) -> dict:
    """
    Build the properties payload for Notion based on a TodoCreate object.
    If creating is True, sets Checkbox to False by default.
    """
    properties = {
        "Task": {
            "type": "title",
            "title": [{"type": "text", "text": {"content": todo_data.name}}]
        },
        "Checkbox": {
            "type": "checkbox",
            "checkbox": False if creating else todo_data.done
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

    return properties
