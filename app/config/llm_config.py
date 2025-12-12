from pydantic_settings import BaseSettings


class LLMConfig(BaseSettings):
    openai_api_key: str
    google_api_key: str

    class Config:
        env_file = ".env"
        extra = "ignore"
