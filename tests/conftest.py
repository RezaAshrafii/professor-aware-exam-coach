from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    database_path = tmp_path / "test.db"
    upload_path = tmp_path / "uploads"
    monkeypatch.setenv("DATABASE_PATH", str(database_path))
    monkeypatch.setenv("UPLOAD_DIR", str(upload_path))

    from app.config import settings
    settings.database_path = str(database_path)
    settings.upload_dir = str(upload_path)
    settings.model_secrets_path = str(tmp_path / "model_secrets.json")

    from app.database import init_db
    init_db()
    from app.main import app
    with TestClient(app) as test_client:
        yield test_client
