from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.config import settings

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    professor TEXT NOT NULL DEFAULT '',
    term TEXT NOT NULL DEFAULT '',
    exam_date TEXT NOT NULL DEFAULT '',
    target_grade REAL,
    daily_minutes INTEGER NOT NULL DEFAULT 90,
    exam_scope TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    source_type TEXT NOT NULL,
    character_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_hint INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(source_id) REFERENCES sources(id) ON DELETE CASCADE,
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chunks_course ON chunks(course_id);
CREATE INDEX IF NOT EXISTS idx_sources_course ON sources(course_id);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    mode TEXT NOT NULL,
    user_input TEXT NOT NULL,
    output TEXT NOT NULL,
    evidence_json TEXT NOT NULL DEFAULT '[]',
    provider TEXT NOT NULL DEFAULT 'demo',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS mistakes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    topic TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL,
    prevention TEXT NOT NULL DEFAULT '',
    severity TEXT NOT NULL DEFAULT 'medium',
    repetitions INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
);
"""


def init_db() -> None:
    settings.database_file.parent.mkdir(parents=True, exist_ok=True)
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(settings.database_file) as connection:
        connection.executescript(SCHEMA)
        connection.commit()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(settings.database_file)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
