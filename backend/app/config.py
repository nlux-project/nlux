from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./nlux.db"
    page_length_default: int = 20
    page_length_max: int = 100
    cors_origins: str = "*"
    # Base URL used to build absolute URLs in responses (no trailing slash)
    base_url: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
