from __future__ import annotations

import json
from typing import Any

from app.database import get_connection
from app.schemas import CourseCreate, ExampleCardCreate, MistakeCreate


def _dict(row: Any) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def list_courses() -> list[dict[str, Any]]:
    with get_connection() as db:
        rows = db.execute(
            """SELECT c.*,
                      (SELECT COUNT(*) FROM sources s WHERE s.course_id = c.id) AS source_count,
                      (SELECT COUNT(*) FROM runs r WHERE r.course_id = c.id) AS run_count,
                      (SELECT COUNT(*) FROM mistakes m WHERE m.course_id = c.id) AS mistake_count,
                      (SELECT COUNT(*) FROM example_cards e WHERE e.course_id = c.id) AS example_count
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

def create_example_card(course_id: int, data: ExampleCardCreate) -> int:
    with get_connection() as db:
        cursor = db.execute(
            """INSERT INTO example_cards(
                   course_id, title, topic, question, solution, method_name,
                   source_kind, source_reference, notes, status
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                course_id,
                data.title.strip(),
                data.topic.strip(),
                data.question.strip(),
                data.solution.strip(),
                data.method_name.strip(),
                data.source_kind,
                data.source_reference.strip(),
                data.notes.strip(),
                data.status,
            ),
        )
        return int(cursor.lastrowid)


def list_example_cards(course_id: int) -> list[dict[str, Any]]:
    with get_connection() as db:
        rows = db.execute(
            """SELECT * FROM example_cards
               WHERE course_id=?
               ORDER BY CASE status WHEN 'confirmed' THEN 1 ELSE 2 END, id DESC""",
            (course_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_example_card(card_id: int) -> dict[str, Any] | None:
    with get_connection() as db:
        return _dict(db.execute("SELECT * FROM example_cards WHERE id=?", (card_id,)).fetchone())


def update_example_card_status(card_id: int, status: str) -> None:
    if status not in {"draft", "confirmed"}:
        raise ValueError("Unknown example card status")
    with get_connection() as db:
        db.execute(
            "UPDATE example_cards SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (status, card_id),
        )


def delete_example_card(card_id: int) -> None:
    with get_connection() as db:
        db.execute("DELETE FROM example_cards WHERE id=?", (card_id,))


def list_retrieval_items(course_id: int) -> list[dict[str, Any]]:
    """Return source chunks plus student-confirmed professor examples.

    Example cards remain separate domain records, but confirmed cards participate in
    retrieval as high-value evidence. Draft cards are never sent to the model.
    """

    items: list[dict[str, Any]] = []
    with get_connection() as db:
        rows = db.execute(
            """SELECT * FROM example_cards
               WHERE course_id=? AND status='confirmed'
               ORDER BY id""",
            (course_id,),
        ).fetchall()

    for row in rows:
        card = dict(row)
        content_parts = [
            f"عنوان مثال استاد: {card['title']}",
            f"مبحث: {card['topic']}" if card["topic"] else "",
            f"روش ثبت‌شده: {card['method_name']}" if card["method_name"] else "",
            f"صورت سؤال:\n{card['question']}",
            f"راه‌حل ثبت‌شده استاد:\n{card['solution']}",
            f"یادداشت دانشجو: {card['notes']}" if card["notes"] else "",
            f"مرجع: {card['source_reference']}" if card["source_reference"] else "",
        ]
        items.append(
            {
                "id": f"example-{card['id']}",
                "source_id": -int(card["id"]),
                "course_id": course_id,
                "chunk_index": None,
                "content": "\n\n".join(part for part in content_parts if part),
                "token_hint": max(1, (len(card["question"]) + len(card["solution"])) // 4),
                "filename": f"کارت مثال: {card['title']}",
                "evidence_kind": "example_card",
                "example_card_id": card["id"],
            }
        )
    items.extend(list_chunks(course_id))
    return items

