from __future__ import annotations

import json
from typing import Any

from app.database import get_connection
from app.schemas import CourseCreate, MistakeCreate


def _dict(row: Any) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def list_courses() -> list[dict[str, Any]]:
    with get_connection() as db:
        rows = db.execute(
            """SELECT c.*,
                      (SELECT COUNT(*) FROM sources s WHERE s.course_id = c.id) AS source_count,
                      (SELECT COUNT(*) FROM runs r WHERE r.course_id = c.id) AS run_count,
                      (SELECT COUNT(*) FROM mistakes m WHERE m.course_id = c.id) AS mistake_count
               FROM courses c ORDER BY c.updated_at DESC, c.id DESC"""
        ).fetchall()
    return [dict(row) for row in rows]


def create_course(data: CourseCreate) -> int:
    with get_connection() as db:
        cursor = db.execute(
            """INSERT INTO courses
               (name, professor, term, exam_date, target_grade, daily_minutes, exam_scope, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data.name.strip(), data.professor.strip(), data.term.strip(),
                data.exam_date.strip(), data.target_grade, data.daily_minutes,
                data.exam_scope.strip(), data.notes.strip(),
            ),
        )
        return int(cursor.lastrowid)


def get_course(course_id: int) -> dict[str, Any] | None:
    with get_connection() as db:
        return _dict(db.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone())


def update_course(course_id: int, data: CourseCreate) -> None:
    with get_connection() as db:
        db.execute(
            """UPDATE courses SET name=?, professor=?, term=?, exam_date=?, target_grade=?,
               daily_minutes=?, exam_scope=?, notes=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""",
            (
                data.name.strip(), data.professor.strip(), data.term.strip(), data.exam_date.strip(),
                data.target_grade, data.daily_minutes, data.exam_scope.strip(), data.notes.strip(), course_id,
            ),
        )


def delete_course(course_id: int) -> None:
    with get_connection() as db:
        db.execute("DELETE FROM courses WHERE id = ?", (course_id,))


def create_source(course_id: int, filename: str, stored_path: str, source_type: str, character_count: int) -> int:
    with get_connection() as db:
        cursor = db.execute(
            "INSERT INTO sources(course_id, filename, stored_path, source_type, character_count) VALUES (?, ?, ?, ?, ?)",
            (course_id, filename, stored_path, source_type, character_count),
        )
        return int(cursor.lastrowid)


def add_chunks(source_id: int, course_id: int, chunks: list[str]) -> None:
    with get_connection() as db:
        db.executemany(
            "INSERT INTO chunks(source_id, course_id, chunk_index, content, token_hint) VALUES (?, ?, ?, ?, ?)",
            [(source_id, course_id, i, chunk, max(1, len(chunk) // 4)) for i, chunk in enumerate(chunks)],
        )


def list_sources(course_id: int) -> list[dict[str, Any]]:
    with get_connection() as db:
        rows = db.execute("SELECT * FROM sources WHERE course_id=? ORDER BY id DESC", (course_id,)).fetchall()
    return [dict(row) for row in rows]


def get_source(source_id: int) -> dict[str, Any] | None:
    with get_connection() as db:
        return _dict(db.execute("SELECT * FROM sources WHERE id=?", (source_id,)).fetchone())


def delete_source(source_id: int) -> None:
    with get_connection() as db:
        db.execute("DELETE FROM sources WHERE id=?", (source_id,))


def list_chunks(course_id: int) -> list[dict[str, Any]]:
    with get_connection() as db:
        rows = db.execute(
            """SELECT ch.*, s.filename FROM chunks ch
               JOIN sources s ON s.id=ch.source_id
               WHERE ch.course_id=? ORDER BY ch.id""",
            (course_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def save_run(course_id: int, mode: str, user_input: str, output: str, evidence: list[dict[str, Any]], provider: str) -> int:
    with get_connection() as db:
        cursor = db.execute(
            "INSERT INTO runs(course_id, mode, user_input, output, evidence_json, provider) VALUES (?, ?, ?, ?, ?, ?)",
            (course_id, mode, user_input, output, json.dumps(evidence, ensure_ascii=False), provider),
        )
        return int(cursor.lastrowid)


def list_runs(course_id: int, limit: int = 20) -> list[dict[str, Any]]:
    with get_connection() as db:
        rows = db.execute(
            "SELECT * FROM runs WHERE course_id=? ORDER BY id DESC LIMIT ?", (course_id, limit)
        ).fetchall()
    output: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["evidence"] = json.loads(item.pop("evidence_json", "[]"))
        output.append(item)
    return output


def create_mistake(course_id: int, data: MistakeCreate) -> int:
    with get_connection() as db:
        cursor = db.execute(
            """INSERT INTO mistakes(course_id, topic, category, description, prevention, severity)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (course_id, data.topic.strip(), data.category.strip(), data.description.strip(), data.prevention.strip(), data.severity),
        )
        return int(cursor.lastrowid)


def list_mistakes(course_id: int) -> list[dict[str, Any]]:
    with get_connection() as db:
        rows = db.execute(
            "SELECT * FROM mistakes WHERE course_id=? ORDER BY CASE severity WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, id DESC",
            (course_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def delete_mistake(mistake_id: int) -> None:
    with get_connection() as db:
        db.execute("DELETE FROM mistakes WHERE id=?", (mistake_id,))
