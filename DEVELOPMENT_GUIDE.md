# Development Guide

## 1. Product definition

**Product name:** Professor-Aware Exam Coach  
**Current version:** 0.3.0  
**Primary user:** A university student preparing for quantitative exams under uncertain or opaque grading practices.  
**Primary promise:** Turn course-specific evidence into focused preparation, defensible solutions, realistic mock exams, and transparent grading feedback.

The product is not an answer generator for active assessments. It is a preparation environment. Every feature must move the user toward:

1. genuine understanding;
2. independent problem solving;
3. concise, defensible, high-scoring exam writing.

## 2. Core product goals

### 2.1 Course-isolated evidence

Each `course + professor` pair is an independent workspace. Notes, inferred preferences, exam patterns, mistakes, and outputs must never leak into another course unless the user explicitly imports them.

### 2.2 Evidence before professor-style claims

The system may infer patterns from lecture notes, past exams, graded answers, and professor comments. It must expose uncertainty and avoid claiming a preference without evidence.

### 2.3 Two-layer answers

For normal tutoring requests, the system should produce:

- an educational solution with reasoning;
- a compact exam-sheet version preserving score-bearing steps.

### 2.4 Preparation loop

The intended loop is:

`ingest → profile → diagnose → teach → practice → mock exam → grade → record mistakes → repeat`

### 2.5 Local-first operation

Course metadata, extracted text, chunks, mistakes, and run history live in local SQLite. External model calls are optional. The app must remain inspectable without a cloud database.

## 3. Non-goals for the initial product

The following remain deliberately excluded from the current release:

- fine-tuning;
- autonomous multi-agent orchestration;
- a vector database;
- user accounts and multi-tenancy;
- collaborative classrooms;
- automatic scraping of university systems;
- OCR pipelines;
- complex analytics dashboards;
- generic note-taking or project-management features;
- mobile native applications;
- model-provider marketplaces.

Adding these before evidence of need is over-engineering.

## 4. Architecture

```text
Browser
  │
  ▼
FastAPI + Jinja templates + vanilla JavaScript
  │
  ├── repositories.py       SQLite persistence
  ├── document_service.py   text extraction and chunking
  ├── retrieval_service.py  lightweight lexical retrieval
  ├── prompt_service.py     course-aware prompt construction
  └── llm_service.py        replaceable model adapter
         │
         ├── Demo provider
         └── OpenAI Responses API
```

### Why this stack

- One Python process and one install command.
- No Node build pipeline in the first version.
- Server-rendered UI is fast and easy to debug.
- Vanilla JavaScript is sufficient for the current interaction model.
- SQLite is adequate for a single-user local tool.
- Provider logic is isolated, so the UI and domain workflow do not depend on OpenAI.

This is a deliberate speed/maintainability tradeoff, not a permanent ban on a separate frontend. A React migration is justified only when the product requires rich stateful editing, offline synchronization, complex exam timers, or desktop packaging.

## 5. Code boundaries

### `main.py`

HTTP orchestration only: validate request, call repository/service, return response. Do not place retrieval or prompt logic here.

### `repositories.py`

All SQL lives here. Routes and services should not execute raw SQL.

### `document_service.py`

File-type parsing, normalization, and chunking only. OCR and table extraction should be separate services later.

### `retrieval_service.py`

Pure retrieval logic. It accepts chunks and returns ranked chunks. This makes it easy to replace lexical ranking with embeddings without changing routes or templates.

### `prompt_service.py`

The canonical behavioral policy and mode-specific instructions. Prompt changes should be reviewed as product changes, not incidental strings scattered through the codebase.

### `llm_service.py`

Provider adapter, structured-response validation, evidence-reference cross-checking, and the single repair attempt. It returns a stable `LLMResult` containing raw/display text, provider label, optional validated payload, schema name, validation status, retry metadata, and optional validation error. Provider-specific SDK objects must not escape this layer.

### `exam_coach_service.py`

The use-case coordinator: retrieve evidence, build prompt, call model, persist run.

## 6. Data model

### `courses`

One isolated workspace per course/professor pair.

### `sources`

Original uploaded file metadata and local path.

### `chunks`

Normalized pieces of source text used for retrieval.

### `runs`

Every model request, output, provider, and evidence reference.

### `mistakes`

The student's mistake ledger. Initially manual; later partially extracted from grading outputs.

Avoid adding generalized entity tables until repeated requirements justify them.

## 7. Initial user flows

### Flow A — first setup

1. Create course.
2. Add exam date, scope, target grade, and current weaknesses.
3. Upload lecture notes and past exams.
4. Run “Professor Profile.”
5. Review low-confidence claims.

### Flow B — learn a topic

1. Select “Teach.”
2. Ask for one topic.
3. Review evidence references.
4. Solve the control question independently.
5. Record recurring mistakes.

### Flow C — mock and grade

1. Generate a mock exam.
2. Complete it outside the answer view.
3. Submit responses in “Strict Grader.”
4. Add major mistakes to the ledger.
5. Generate targeted exercises.

## 8. UI principles

- RTL-first, keyboard-friendly, responsive.
- A course page is the primary workspace; avoid deep navigation.
- One visible primary action per panel.
- Modes are explicit and mutually understandable.
- Evidence and uncertainty must be visible, not hidden in system behavior.
- Destructive actions require confirmation.
- The interface must remain useful in demo mode without an API key.
- Avoid dashboard decoration that does not change user decisions.

## 9. Development phases

### Phase 0 — completed in v0.1.0

- project scaffold;
- clean RTL UI;
- course workspaces;
- local source ingestion;
- chunk storage;
- lexical retrieval;
- nine coaching modes;
- provider abstraction;
- run history;
- manual mistake ledger;
- smoke tests.

**Exit criterion:** A user can create a course, upload real notes, issue a course-aware request, see evidence, and store the result.

### Phase 1 — reliability, not breadth

Progress through v0.3.0:

- completed in v0.2.0: Pydantic contracts for `ProfessorProfile`, `GradingReport`, and `StudyPlan`;
- completed in v0.2.0: JSON-only structured prompt contracts for profile, grading, and planning;
- completed in v0.2.0: schema validation and initial prompt/schema regression tests;
- completed in v0.3.0: exact cross-checking of source number, filename, and chunk index against the evidence of the current run;
- completed in v0.3.0: one repair attempt with validation-error feedback and an allowed-evidence catalog;
- completed in v0.3.0: explicit `valid`, `recovered`, and `invalid_fallback` states in the API and UI;
- completed in v0.3.0: dedicated structured UI rendering;
- completed in v0.3.0: user-approved mistake persistence from grading results;
- pending: workspace ZIP export/import;
- pending: source and chunk preview;
- pending: fixed real evidence-pack regression fixtures.

Ordered remaining work:

1. Export/import a complete course workspace as ZIP.
2. Add source and chunk preview endpoints and UI.
3. Add fixed evidence-pack prompt regression tests.
4. Improve error pages and upload progress.

**Do not add embeddings before evaluating lexical retrieval on real courses.**

**Exit criterion:** Outputs can be validated, compared, and safely converted into persistent structured data.

### Phase 2 — exam workflow

1. Stateful mock-exam sessions.
2. Timer, pause policy, and question navigation.
3. Hidden answer key until submission.
4. Per-question grading and score breakdown.
5. Retry queue driven by the mistake ledger.
6. Printable exam and answer-sheet view.

**Exit criterion:** A complete mock exam can be taken and graded inside the product without leaking answers.

### Phase 3 — retrieval upgrade if justified

Measure retrieval failures first. If lexical retrieval misses semantically relevant chunks:

1. add an `EmbeddingProvider` interface;
2. store embeddings in SQLite or a lightweight local index;
3. implement hybrid lexical + semantic ranking;
4. preserve current evidence references and service contracts;
5. benchmark against a labeled set of real questions.

Do not introduce a separate vector database for a single-user workspace unless corpus size or latency measurements require it.

### Phase 4 — professor model evaluation

1. Build a labeled evaluation pack from anonymized, consented data.
2. Compare standard rubric grading with professor-aware grading.
3. Measure calibration, not only average score error.
4. Track confidence versus evidence count.
5. Add pairwise ranking of alternative answers.

Fine-tuning becomes eligible only after this phase shows that prompting plus retrieval has reached a stable ceiling.

### Phase 5 — optional productization

Only after repeat use by multiple users:

- authentication;
- encrypted cloud sync;
- multi-device support;
- teacher/course template sharing;
- billing and quotas;
- audit and privacy controls.

## 10. Evaluation plan

The first evaluation should use real course materials, not synthetic examples.

For each of 3–5 courses:

- 20 representative questions;
- lecture notes and past exams;
- at least 5 graded answers when available;
- expert or student-reviewed expected evidence chunks;
- expected score-bearing steps.

Measure:

- retrieval recall@8;
- unsupported professor-style claims;
- correctness of the educational solution;
- preservation of score-bearing steps in the exam version;
- grading consistency;
- user ability to reproduce the solution without looking;
- time saved during revision.

A feature is not successful merely because the model output looks polished.

## 11. Security and privacy

- API keys remain server-side in `.env`.
- Uploaded files remain local by default.
- Before a model call, only retrieved chunks are sent, not the full workspace.
- The UI must eventually show exactly which text will leave the device.
- Graded student answers should be anonymized and used with consent.
- Never silently use one student's work to train or profile another user.

## 12. Coding standards

- Python type hints on public functions.
- Small services with one responsibility.
- No provider SDK objects outside adapters.
- No SQL outside repositories.
- No business logic in templates.
- No speculative abstractions without two concrete callers.
- Prefer explicit names over framework magic.
- Add tests for every bug fixed.
- Keep dependencies limited and reviewed.
- Refactor when duplication is observed, not predicted.

## 13. Immediate backlog, ordered

1. **Completed in v0.2.0:** Define Pydantic schemas for `ProfessorProfile`, `GradingReport`, and `StudyPlan`.
2. **Completed in v0.2.0:** Request and validate JSON outputs for those schemas.
3. **Completed in v0.3.0:** Cross-check structured citations against the exact current-run evidence and add one repair attempt.
4. **Completed in v0.3.0:** Render structured grading, professor profiles, and study plans cleanly in the UI.
5. **Completed in v0.3.0:** Add user-approved “Save as mistake” actions.
6. Add workspace export/import as ZIP.
7. Add source/chunk preview.
8. Add fixed prompt regression fixtures built from a consented evidence pack.
9. Build stateful exam sessions with a server-side hidden answer key.
10. Create a 20-question real-course retrieval evaluation pack and measure recall@8.
11. Add an `EmbeddingProvider` and hybrid retrieval only if the benchmark shows material misses.
12. Begin professor-model evaluation only after structured exam-session data exists.
13. Consider productization only after repeated use by multiple users.

## 14. Definition of done for v0.3.0

- Application starts from a documented clean install.
- Health endpoint returns OK.
- Existing course, upload, retrieval, and text-mode workflows remain operational.
- Structured profile, grading, and planning outputs pass both Pydantic validation and current-run evidence-reference validation.
- A nonexistent source number, mismatched filename, or mismatched chunk index cannot receive a valid status.
- Invalid structured output receives no more than one repair attempt.
- Invalid fallback text is visibly marked and cannot be mistaken for a validated report.
- Professor profile, grading report, and study plan have dedicated UI rendering.
- A suggested mistake is inserted only after explicit user confirmation.
- Automated tests pass.
- Required manual checks in `USER_VERIFICATION.md` pass on at least one real course workspace.
- Architecture and roadmap are documented here.
