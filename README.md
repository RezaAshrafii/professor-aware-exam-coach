# Professor-Aware Exam Coach — v0.3.0

A local-first university exam-preparation tool grounded in the real materials of each course and professor.

## What v0.3.0 adds

### Reliability fixes

- Every structured `EvidenceReference` is cross-checked against the exact evidence retrieved for that run.
- `source_number`, `filename`, and `chunk_index` must all match; a syntactically valid but hallucinated citation is rejected.
- Invalid structured output receives exactly one repair attempt with the validation error and the allowed evidence catalog.
- A successful repair is marked as `recovered`.
- A failed repair remains an explicit `invalid_fallback`; it is never presented as a valid grading/profile/plan object.
- Failure of the repair API request itself falls back to the first raw response with a visible validation warning.

### Structured UI

- Dedicated professor-profile rendering with claim status, confidence, and evidence references.
- Dedicated grading-report rendering with score breakdown, missing steps, error classes, corrected answer, professor-score range, and confidence.
- Dedicated study-plan rendering with priorities, daily tasks, measurable completion criteria, and timing.
- Visible reliability banners for `valid`, `recovered`, and `invalid_fallback` responses.
- Raw fallback output is clearly labeled as unvalidated instead of silently rendered as a normal report.
- Invalid fallback runs are persisted with an explicit warning prefix, so the history view also cannot present them as normal reports.

### Mistake workflow

- A `GradingReport.suggested_mistake` can be saved to the mistake ledger.
- Saving requires an explicit browser confirmation.
- A new JSON API endpoint accepts the already validated `MistakeCreate` contract.

## Existing capabilities

- Isolated workspace for each course and professor.
- PDF, DOCX, TXT, and Markdown ingestion.
- Local text extraction and chunking.
- Lightweight lexical retrieval without a vector database.
- Nine modes: professor profile, source analysis, teaching, guided practice, mock exam, grading, exam-sheet answer, oral defense, and study planning.
- Run history and retrieved evidence display.
- Manual and grading-assisted mistake ledger.
- Responsive Persian RTL interface.
- Optional OpenAI adapter through the Responses API.
- Offline demo mode.

## Quick start on Windows

Double-click `start_windows.bat`.

Manual setup:

```powershell
cd professor_aware_exam_coach_v0_3_0
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

Open:

```text
http://127.0.0.1:8000
```

## Configure a model

Set these values in `.env`:

```env
OPENAI_API_KEY=...
OPENAI_MODEL=...
```

The model name is deliberately not hard-coded. API credentials remain server-side.

## Structured-output API states

Only `profile`, `grade`, and `plan` use structured contracts.

A run now returns:

```json
{
  "structured_output": {},
  "schema": "GradingReport",
  "validation_error": null,
  "validation_status": "valid",
  "retry_count": 0,
  "first_validation_error": null
}
```

Possible `validation_status` values:

| Status | Meaning |
|---|---|
| `not_applicable` | Normal text mode; no structured schema was requested. |
| `valid` | First response passed schema and evidence-reference validation. |
| `recovered` | First response failed; one repair response passed. |
| `invalid_fallback` | The repair also failed or could not be requested; only raw text is available. |

## Tests

```powershell
pytest -q
```

Current release: **20 tests passing**.

Manual release-gate checks are documented in [USER_VERIFICATION.md](USER_VERIFICATION.md). Do not move to the next phase until its required checks pass on at least one real course workspace.

## Current limitations

- Structured metadata is rendered for the current response but run history still stores the display output in the existing `runs.output` field.
- Workspace ZIP export/import is not implemented.
- Source/chunk preview is not implemented.
- Fixed real evidence-pack prompt regression fixtures are not yet included.
- Mock exams are not stateful and have no server-enforced hidden answer key.
- Retrieval remains lexical until real-course benchmarks justify embeddings.
- Scanned PDFs are not OCR-processed.

See [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for architecture, boundaries, phase gates, and the ordered backlog.
