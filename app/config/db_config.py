from pydantic_settings import BaseSettings


class DBConfig(BaseSettings):
    url: str
    name: str

    class Config:
        env_file = ".env"
        env_prefix = "MONGODB_"
        extra = "ignore"
