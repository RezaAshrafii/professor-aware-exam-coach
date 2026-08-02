# Changelog

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
