from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict

Relation = List[Dict[str, str]]


class Todo(BaseModel):
    id: str
    name: str
    date: Optional[datetime] = None
    priority: Optional[str] = None
    projects: Optional[Relation] = None
    repeat_task: Optional[str] = None
    created: datetime
    done: bool


class TodoCreate(BaseModel):
    name: str
    date: Optional[datetime] = None
    priority: Optional[str] = None
    projects: Optional[Relation] = None
    repeat_task: Optional[str] = None


class TodoResponse(BaseModel):
    message: str
    data: Optional[Todo] = None
