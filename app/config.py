from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Professor-Aware Exam Coach"
    app_env: str = "development"
    app_secret: str = "change-me"
    database_path: str = "data/exam_coach.db"
    upload_dir: str = "data/uploads"
    openai_api_key: str = ""
    openai_model: str = ""
    max_context_chunks: int = 8
    max_upload_mb: int = 20
    web_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def database_file(self) -> Path:
        return Path(self.database_path)

    @property
    def upload_path(self) -> Path:
        return Path(self.upload_dir)

    @property
    def web_origin_list(self) -> list[str]:
        return [item.strip() for item in self.web_origins.split(",") if item.strip()]


settings = Settings()
