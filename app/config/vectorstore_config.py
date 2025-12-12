import os
from pydantic_settings import BaseSettings


class VectorStoreConfig(BaseSettings):
    embeddings_name: str
    k: int
    apply_filter: bool
    filter_keyword: str | None = None
    json_dir: str

    # Chroma Server Settings
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8000"))

    class Config:
        env_file = ".env"
        extra = "ignore"
