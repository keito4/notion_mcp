from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Todo(BaseModel):
    id: str
    name: str
    date: Optional[datetime] = None
    priority: Optional[str] = None
    project: Optional[str] = None
    repeat_task: Optional[str] = None
    created: datetime
    done: bool


class TodoCreate(BaseModel):
    name: str
    date: Optional[datetime] = None
    priority: Optional[str] = None
    project: Optional[str] = None
    repeat_task: Optional[str] = None


class TodoResponse(BaseModel):
    message: str
    data: Optional[Todo] = None
