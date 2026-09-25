from pathlib import Path

from pydantic_settings import BaseSettings


# Default SQLite database lives next to the backend package (backend/nlux.db),
# so the API works regardless of the CWD it is started from. Docker overrides
# this via DATABASE_URL (e.g. sqlite:////data/nlux.db).
class Settings(BaseSettings):
    database_url: str = f"sqlite:///{Path(__file__).resolve().parent.parent / 'nlux.db'}"
    page_length_default: int = 20
    page_length_max: int = 100
    cors_origins: str = "*"
    # Base URL used to build absolute URLs in responses (no trailing slash)
    base_url: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
