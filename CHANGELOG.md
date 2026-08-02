# Changelog

## 0.3.0 — Evidence integrity and structured UI

- Added runtime cross-checking of every structured evidence reference against the retrieved evidence for the current run.
- Rejects nonexistent source numbers, filename mismatches, and chunk-index mismatches.
- Added one structured-output repair attempt using the original validation error and an explicit allowed-evidence catalog.
- Added explicit validation states: `valid`, `recovered`, `invalid_fallback`, and `not_applicable`.
- Added graceful fallback when the repair request itself fails.
- Added dedicated UI components for `ProfessorProfile`, `GradingReport`, and `StudyPlan`.
- Added visible reliability banners so invalid fallback text cannot be mistaken for a validated report.
- Added an explicit invalid-output warning prefix to persisted run history entries.
- Added structured grading tables, missing-step cards, error groups, corrected-answer display, and confidence indicators.
- Added user-confirmed saving of `GradingReport.suggested_mistake` to the mistake ledger.
- Added a JSON mistake-creation endpoint using the existing `MistakeCreate` schema.
- Added regression tests for hallucinated citations, filename/chunk mismatches, successful repair, failed repair, repair-request failure, and mistake persistence.
- Kept the database schema and retrieval contract unchanged.

## 0.2.0 — Structured contracts

- Added validated `ProfessorProfile`, `GradingReport`, and `StudyPlan` Pydantic schemas.
- Added evidence references and confidence constraints for professor-profile claims.
- Added consistency validation for grading totals and daily study-plan timing.
- Added mode-specific JSON Schema contracts to prompts.
- Added structured response parsing with raw-text fallback on validation failure.
- Added structured API metadata: `structured_output`, `schema`, and `validation_error`.
- Added deterministic structured demo payloads for offline use.
- Added schema, prompt-contract, parser, fallback, and endpoint regression tests.
- Kept the database, retrieval contract, UI workflow, and provider boundary unchanged.

## 0.1.0 — Initial vertical slice

- Added local course workspaces.
- Added PDF, DOCX, TXT and Markdown ingestion.
- Added lightweight lexical retrieval.
- Added nine exam-coaching modes.
- Added optional OpenAI Responses API adapter and offline demo mode.
- Added run history and evidence display.
- Added manual mistake ledger.
- Added responsive Persian RTL interface.
- Added initial automated tests and development guide.
