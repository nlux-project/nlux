from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./nlux.db"
    page_length_default: int = 20
    page_length_max: int = 100

    class Config:
        env_file = ".env"


settings = Settings()
