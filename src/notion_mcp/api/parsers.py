from datetime import datetime
from typing import Optional
from .utils import JST


def parse_date_property(props: dict, prop_name: str) -> Optional[datetime]:
    """Parse a date property and return a datetime object in JST if available."""
    date_data = props.get(prop_name, {}).get("date", {})
    start_str = date_data.get("start")
    if start_str:
        try:
            return datetime.fromisoformat(start_str.replace("Z", "+00:00")).astimezone(JST)
        except ValueError:
            pass
    return None


def parse_select_property(props: dict, prop_name: str) -> Optional[str]:
    """Parse a select property and return the selected name."""
    select_data = props.get(prop_name, {}).get("select")
    if select_data and "name" in select_data:
        return select_data["name"]
    return None


def parse_title_property(props: dict, prop_name: str) -> Optional[str]:
    """Parse a title property and return the text content."""
    title_data = props.get(prop_name, {}).get("title", [])
    if len(title_data) > 0 and "text" in title_data[0]:
        return title_data[0]["text"].get("content")
    return None


def parse_checkbox_property(props: dict, prop_name: str) -> bool:
    """Parse a checkbox property and return its boolean value."""
    return props.get(prop_name, {}).get("checkbox", False)
