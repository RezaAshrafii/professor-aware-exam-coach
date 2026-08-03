# Changelog

## [0.7.0] - 2026-08-03

### Added

- Two generic local model-connection slots.
- Native Gemini REST discovery and generation.
- OpenAI-compatible model discovery with Chat Completions and Responses API fallback.
- Searchable model picker that renders at most eight results at once.
- Local secret store excluded from Git.
- Connection test endpoint and active provider status.
- Smart dependency bootstrap that adopts an existing valid environment without reinstalling, plus a fast Windows launcher.

### Changed

- LLM runtime now resolves the active connection dynamically for every run.
- Removed the hard dependency on the OpenAI Python SDK.
- Demo grading is automatically replaced once an active connection and model exist.
- Frontend version updated to 0.7.0.

### Verification

- 38 Python tests pass.
- Gemini discovery, secret masking, dynamic selection and real grading path are covered with mock provider responses.
- OpenAI-compatible dynamic model discovery is covered.
- TypeScript syntax and model-picker contract checks pass.

## [0.6.0] - 2026-08-03

### Fixed

- Replaced browser-to-FastAPI calls with a same-origin Next.js `/backend` proxy.
- Removed unnecessary JSON `Content-Type` headers from bodyless requests.
- Hardened direct local CORS for localhost and 127.0.0.1 origins.
- Added an exact regression test for the failing `/health` preflight request.
- Updated launchers to wait for both API and proxied frontend health before opening the browser.

### Changed

- Refined the UI into a denser minimal visual system without adding a component library.
- Improved typography, spacing, cards, forms, sidebar, responsive layout and structured reports.
- Updated application versions to 0.6.0.

### Verification

- 30 Python tests pass.
- FastAPI live health and exact browser-style CORS preflight pass.
- TypeScript syntax and frontend proxy contract checks pass.
- Production Next.js build remains a GitHub/system gate because the artifact environment npm registry lacks `@types/node`.

## [0.5.0] - 2026-08-03

### Added

- Next.js 16 App Router frontend with TypeScript and Persian RTL UI.
- Dashboard for creating and opening course workspaces.
- Course workspace tabs for overview, sources, professor examples, coach, history, mistakes and settings.
- Structured renderers for `ProfessorProfile`, `GradingReport` and `StudyPlan`.
- JSON/multipart product API and local CORS configuration.
- One-command product startup scripts for Windows and Unix.
- Frontend CI gates for TypeScript and production build.
- Product API tests and TypeScript syntax check.

### Preserved

- Existing FastAPI/Jinja interface as a fallback.
- Existing retrieval, LLM validation, evidence validation and SQLite data model.

### Known limitation

- The Next.js dependency installation and production build could not run in the artifact sandbox because its npm registry was unavailable. GitHub CI is the release gate for that build.

## [0.4.0] - 2026-08-02

- Added confirmed professor Example Cards and GitHub repository foundation.
