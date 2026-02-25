"""
config.py — Centralized configuration using pydantic-settings.

WHY: Hardcoding credentials in database.py and celery_app.py means:
  - You can't deploy to different environments (dev/staging/prod)
  - Secrets can accidentally get committed to git
  - Changing a value requires touching multiple files

NOW: One place, reads from .env automatically, fails fast if anything is missing.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Single instance imported everywhere — don't instantiate Settings() in each file
settings = Settings()