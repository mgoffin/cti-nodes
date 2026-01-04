"""Application configuration."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Nodes"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_path: Path = Path("data/nodes.db")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS (for frontend dev server)
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8000"]

    class Config:
        env_prefix = "NODES_"
        env_file = ".env"


settings = Settings()
