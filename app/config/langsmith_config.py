from pydantic_settings import BaseSettings
from typing import Optional


class LangSmithConfig(BaseSettings):
    tracing_v2: Optional[bool] = False
    endpoint: Optional[str] = "https://api.smith.langchain.com"
    api_key: Optional[str] = None
    project: Optional[str] = None

    class Config:
        env_file = ".env"
        env_prefix = "LANGCHAIN_"
        extra = "ignore"
