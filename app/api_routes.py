from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile

from app import repositories
from app.config import settings
from app.schemas import (
    CourseCreate,
    ExampleCardCreate,
    ExampleCardStatusUpdate,
    MistakeCreate,
    ModelConnectionUpsert,
)
from app.services.document_service import DocumentError, SUPPORTED_EXTENSIONS, chunk_text, extract_text
from app.services.exam_coach_service import ExamCoachService
from app.services.model_connection_service import model_connections

router = APIRouter(prefix="/api", tags=["product-api"])
coach = ExamCoachService()


def require_course(course_id: int) -> dict[str, Any]:
    course = repositories.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def _source_public(source: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in source.items() if key != "stored_path"}


def _delete_course_files(course_id: int) -> None:
    for source in repositories.list_sources(course_id):
        Path(source["stored_path"]).unlink(missing_ok=True)
    course_upload_dir = settings.upload_path / str(course_id)
    if course_upload_dir.exists():
        shutil.rmtree(course_upload_dir, ignore_errors=True)


def _store_source(course_id: int, file: UploadFile) -> dict[str, Any]:
    require_course(course_id)
    filename = Path(file.filename or "source").name
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF, DOCX, TXT and MD files are supported.")

    destination_dir = settings.upload_path / str(course_id)
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{uuid.uuid4().hex}_{filename}"

    max_bytes = settings.max_upload_mb * 1024 * 1024
    with destination.open("wb") as output:
        shutil.copyfileobj(file.file, output)
    if destination.stat().st_size > max_bytes:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_mb} MB.")

    try:
        text = extract_text(destination)
        chunks = chunk_text(text)
    except DocumentError as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    source_id = repositories.create_source(
        course_id, filename, str(destination), suffix.lstrip("."), len(text)
    )
    repositories.add_chunks(source_id, course_id, chunks)
    source = repositories.get_source(source_id)
    assert source is not None
    payload = _source_public(source)
    payload["chunk_count"] = len(chunks)
    return payload


@router.get("/courses")
def list_courses_api() -> dict[str, Any]:
    return {"items": repositories.list_courses()}


@router.post("/courses", status_code=201)
def create_course_api(payload: CourseCreate) -> dict[str, Any]:
    course_id = repositories.create_course(payload)
    return {"course": require_course(course_id)}


@router.get("/courses/{course_id}")
def get_course_workspace_api(course_id: int) -> dict[str, Any]:
    course = require_course(course_id)
    return {
        "course": course,
        "sources": [_source_public(item) for item in repositories.list_sources(course_id)],
        "example_cards": repositories.list_example_cards(course_id),
        "runs": repositories.list_runs(course_id, limit=50),
        "mistakes": repositories.list_mistakes(course_id),
        "model_enabled": coach.llm.enabled,
        "active_provider": coach.llm.active_provider,
    }


@router.put("/courses/{course_id}")
def update_course_api(course_id: int, payload: CourseCreate) -> dict[str, Any]:
    require_course(course_id)
    repositories.update_course(course_id, payload)
    return {"course": require_course(course_id)}


@router.delete("/courses/{course_id}", status_code=204)
def delete_course_api(course_id: int) -> None:
    require_course(course_id)
    _delete_course_files(course_id)
    repositories.delete_course(course_id)


@router.post("/courses/{course_id}/sources", status_code=201)
def upload_source_api(course_id: int, file: UploadFile = File(...)) -> dict[str, Any]:
    return {"source": _store_source(course_id, file)}


@router.delete("/sources/{source_id}", status_code=204)
def delete_source_api(source_id: int) -> None:
    source = repositories.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    Path(source["stored_path"]).unlink(missing_ok=True)
    repositories.delete_source(source_id)


@router.post("/courses/{course_id}/example-cards", status_code=201)
def create_example_card_api(course_id: int, payload: ExampleCardCreate) -> dict[str, Any]:
    require_course(course_id)
    card_id = repositories.create_example_card(course_id, payload)
    card = repositories.get_example_card(card_id)
    assert card is not None
    return {"example_card": card}


@router.patch("/courses/{course_id}/example-cards/{card_id}")
def update_example_card_status_api(
    course_id: int, card_id: int, payload: ExampleCardStatusUpdate
) -> dict[str, Any]:
    require_course(course_id)
    card = repositories.get_example_card(card_id)
    if not card or int(card["course_id"]) != course_id:
        raise HTTPException(status_code=404, detail="Example card not found")
    repositories.update_example_card_status(card_id, payload.status)
    updated = repositories.get_example_card(card_id)
    assert updated is not None
    return {"example_card": updated}


@router.delete("/courses/{course_id}/example-cards/{card_id}", status_code=204)
def delete_example_card_api(course_id: int, card_id: int) -> None:
    require_course(course_id)
    card = repositories.get_example_card(card_id)
    if not card or int(card["course_id"]) != course_id:
        raise HTTPException(status_code=404, detail="Example card not found")
    repositories.delete_example_card(card_id)


@router.post("/courses/{course_id}/mistakes", status_code=201)
def create_mistake_api(course_id: int, payload: MistakeCreate) -> dict[str, Any]:
    require_course(course_id)
    mistake_id = repositories.create_mistake(course_id, payload)
    mistake = repositories.get_mistake(mistake_id)
    assert mistake is not None
    return {"status": "saved", "mistake": mistake}


@router.delete("/courses/{course_id}/mistakes/{mistake_id}", status_code=204)
def delete_mistake_api(course_id: int, mistake_id: int) -> None:
    require_course(course_id)
    mistake = repositories.get_mistake(mistake_id)
    if not mistake or int(mistake["course_id"]) != course_id:
        raise HTTPException(status_code=404, detail="Mistake not found")
    repositories.delete_mistake(mistake_id)


@router.get("/model-connections")
def list_model_connections_api() -> dict[str, Any]:
    return {
        "items": model_connections.list_public(),
        "active_provider": coach.llm.active_provider,
    }


@router.put("/model-connections/{slot}")
def save_model_connection_api(slot: int, payload: ModelConnectionUpsert) -> dict[str, Any]:
    try:
        connection = model_connections.save(slot, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"connection": connection, "active_provider": coach.llm.active_provider}


@router.post("/model-connections/{slot}/discover")
def discover_models_api(slot: int) -> dict[str, Any]:
    try:
        models = model_connections.discover_models(slot)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Model discovery failed: {exc}") from exc
    return {"items": models, "count": len(models)}


@router.post("/model-connections/{slot}/test")
def test_model_connection_api(slot: int) -> dict[str, Any]:
    try:
        return model_connections.test_connection(slot)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Connection test failed: {exc}") from exc


@router.delete("/model-connections/{slot}", status_code=204)
def delete_model_connection_api(slot: int) -> None:
    try:
        model_connections.delete(slot)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
