from __future__ import annotations

from contextlib import asynccontextmanager
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import repositories
from app.config import settings
from app.database import init_db
from app.schemas import CourseCreate, MistakeCreate, RunRequest
from app.services.document_service import DocumentError, SUPPORTED_EXTENSIONS, chunk_text, extract_text
from app.services.exam_coach_service import ExamCoachService

BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
coach = ExamCoachService()


def require_course(course_id: int) -> dict:
    course = repositories.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    courses = repositories.list_courses()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"courses": courses, "app_name": settings.app_name},
    )


@app.post("/courses")
def create_course(
    name: str = Form(...), professor: str = Form(""), term: str = Form(""),
    exam_date: str = Form(""), target_grade: str = Form(""), daily_minutes: int = Form(90),
    exam_scope: str = Form(""), notes: str = Form(""),
) -> RedirectResponse:
    payload = CourseCreate(
        name=name, professor=professor, term=term, exam_date=exam_date,
        target_grade=float(target_grade) if target_grade.strip() else None,
        daily_minutes=daily_minutes, exam_scope=exam_scope, notes=notes,
    )
    course_id = repositories.create_course(payload)
    return RedirectResponse(url=f"/courses/{course_id}", status_code=303)


@app.get("/courses/{course_id}", response_class=HTMLResponse)
def course_page(request: Request, course_id: int) -> HTMLResponse:
    course = require_course(course_id)
    return templates.TemplateResponse(
        request=request,
        name="course.html",
        context={
            "course": course,
            "sources": repositories.list_sources(course_id),
            "runs": repositories.list_runs(course_id),
            "mistakes": repositories.list_mistakes(course_id),
            "model_enabled": coach.llm.enabled,
        },
    )


@app.post("/courses/{course_id}/update")
def update_course(
    course_id: int, name: str = Form(...), professor: str = Form(""), term: str = Form(""),
    exam_date: str = Form(""), target_grade: str = Form(""), daily_minutes: int = Form(90),
    exam_scope: str = Form(""), notes: str = Form(""),
) -> RedirectResponse:
    require_course(course_id)
    payload = CourseCreate(
        name=name, professor=professor, term=term, exam_date=exam_date,
        target_grade=float(target_grade) if target_grade.strip() else None,
        daily_minutes=daily_minutes, exam_scope=exam_scope, notes=notes,
    )
    repositories.update_course(course_id, payload)
    return RedirectResponse(url=f"/courses/{course_id}", status_code=303)


@app.post("/courses/{course_id}/delete")
def delete_course(course_id: int) -> RedirectResponse:
    require_course(course_id)
    for source in repositories.list_sources(course_id):
        Path(source["stored_path"]).unlink(missing_ok=True)
    repositories.delete_course(course_id)
    return RedirectResponse(url="/", status_code=303)


@app.post("/courses/{course_id}/sources")
def upload_source(course_id: int, file: UploadFile = File(...)) -> RedirectResponse:
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

    source_id = repositories.create_source(course_id, filename, str(destination), suffix.lstrip("."), len(text))
    repositories.add_chunks(source_id, course_id, chunks)
    return RedirectResponse(url=f"/courses/{course_id}#sources", status_code=303)


@app.post("/sources/{source_id}/delete")
def delete_source(source_id: int) -> RedirectResponse:
    source = repositories.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    Path(source["stored_path"]).unlink(missing_ok=True)
    repositories.delete_source(source_id)
    return RedirectResponse(url=f"/courses/{source['course_id']}#sources", status_code=303)


@app.post("/api/courses/{course_id}/run")
def run_coach(course_id: int, payload: RunRequest) -> JSONResponse:
    course = require_course(course_id)
    allowed_modes = {"profile", "analyze", "teach", "guided", "exam", "grade", "exam_answer", "oral", "plan"}
    if payload.mode not in allowed_modes:
        raise HTTPException(status_code=400, detail="Unknown mode")
    try:
        result = coach.run(course, payload.mode, payload.prompt)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Model request failed: {exc}") from exc
    return JSONResponse(result)


@app.post("/api/courses/{course_id}/mistakes")
def create_mistake_api(course_id: int, payload: MistakeCreate) -> JSONResponse:
    require_course(course_id)
    mistake_id = repositories.create_mistake(course_id, payload)
    return JSONResponse({"id": mistake_id, "status": "saved"}, status_code=201)


@app.post("/courses/{course_id}/mistakes")
def create_mistake(
    course_id: int, topic: str = Form(""), category: str = Form(""),
    description: str = Form(...), prevention: str = Form(""), severity: str = Form("medium"),
) -> RedirectResponse:
    require_course(course_id)
    repositories.create_mistake(course_id, MistakeCreate(
        topic=topic, category=category, description=description,
        prevention=prevention, severity=severity,
    ))
    return RedirectResponse(url=f"/courses/{course_id}#mistakes", status_code=303)


@app.post("/mistakes/{mistake_id}/delete")
def delete_mistake(mistake_id: int, course_id: int = Form(...)) -> RedirectResponse:
    repositories.delete_mistake(mistake_id)
    return RedirectResponse(url=f"/courses/{course_id}#mistakes", status_code=303)
