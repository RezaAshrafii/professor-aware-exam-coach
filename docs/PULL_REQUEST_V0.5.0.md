# PR: Add Next.js product UI

## Goal

Make the existing backend usable through a real product interface without rewriting the validated core.

## Included

- JSON CRUD API for product workflows;
- CORS limited to local Next.js origins;
- Next.js App Router frontend in Persian RTL;
- dashboard and per-course workspace;
- sources, examples, coach, history, mistakes and settings UI;
- structured output renderer;
- product startup scripts;
- backend contract tests and frontend syntax check;
- CI frontend type-check and build gate.

## Explicitly out of scope

- Method Registry;
- OCR/video processing;
- embeddings;
- auth/cloud deployment;
- deleting the legacy UI.

## Verification

- 26 Python tests;
- TypeScript syntax transpilation;
- real FastAPI smoke test on a separate port;
- `npm run typecheck` and `npm run build` required by GitHub CI.

## Known limitation

The package registry was not available in the build sandbox, so dependency installation and the real Next.js build must be confirmed by CI or the user's machine.
