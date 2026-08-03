# Development Guide

## Product scope

Professor-Aware Exam Coach یک modular monolith و ابزار شخصی local-first است. هدف فعلی رسیدن سریع به یک محصول قابل استفاده است، نه ساخت زیرساخت پژوهشی یا سازمانی سنگین.

## Architecture

```text
Next.js UI
   ↓ same-origin /backend proxy
FastAPI API
   ↓
ExamCoach / ModelConnection / Retrieval services
   ↓
Repositories
   ↓
SQLite + local uploads + local API-key file
```

## Current boundaries

- `api_routes.py`: JSON product API
- `schemas.py`: request/structured-output contracts
- `repositories.py`: SQL only
- `model_connection_service.py`: provider discovery, generation and local secrets
- `llm_service.py`: structured validation and one repair attempt
- `exam_coach_service.py`: retrieval → prompt → model → persistence
- `web/`: Next.js UI

## Model runtime rules

1. At most two saved connections.
2. Exactly zero or one active connection.
3. No model IDs hardcoded in product code.
4. API keys never returned to the browser after save.
5. Provider errors remain explicit; the app must not silently fall back to demo after a configured request fails.
6. Structured responses remain schema- and evidence-validated regardless of provider.

## Startup rules

- `scripts/bootstrap.py` creates `.venv` once.
- Python dependencies reinstall only when `requirements.txt` changes.
- Node dependencies reinstall only when dependency/lock data changes.
- Local startup never upgrades pip automatically.
- `start_fast_windows.bat` performs no installation.

## Non-goals

- microservices, queues, Docker orchestration;
- vector DB before measured retrieval failure;
- multi-agent runtime;
- fine-tuning before labeled data;
- provider-specific UI pages;
- maintaining a manual model catalog.

## Definition of done

A change is done only when tests cover its main success and failure path, user verification is explicit, private data remains outside Git, and startup does not regress.

## Short roadmap

### v0.7.0 — completed

- generic two-slot model runtime;
- Gemini and OpenAI-compatible APIs;
- dynamic model discovery;
- real grading activation;
- dependency-aware startup.

### v0.8.0

- simplify coach input into separate question/answer/score fields;
- Method Card MVP and allowed-method warning;
- source chunk preview.

### v1.0.0

- stable daily-use workflow on several real courses;
- export/import workspace;
- full backend/frontend CI green;
- polished documentation and release package.
