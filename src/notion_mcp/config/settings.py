from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path
from functools import lru_cache


class Settings(BaseSettings):
    notion_api_key: str = Field(..., env="NOTION_API_KEY")
    notion_todo_database_id: str = Field(..., env="NOTION_TODO_DATABASE_ID")
    notion_project_database_id: str = Field(...,
                                            env="NOTION_PROJECT_DATABASE_ID")
    tz: str = Field(..., env="TZ")
    notion_version: str = "2022-06-28"
    notion_base_url: str = "https://api.notion.com/v1"

    class Config:
        env_file = str(Path(__file__).parent.parent.parent.parent / ".env")
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
