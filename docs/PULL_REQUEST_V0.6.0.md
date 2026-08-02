# PR — Stable UI Connection and Minimal Visual Refresh

## Scope

- Make frontend/backend connectivity independent from browser CORS during normal use.
- Preserve direct local API access for development.
- Improve UI density and readability without a UI framework.
- Make one-click startup wait for both services.

## Out of scope

- Method Registry
- Retrieval changes
- Database schema changes
- New AI providers
- Component libraries or global state managers

## Verification

- 30 backend/contract tests
- Exact browser preflight regression
- TypeScript syntax check
- Live FastAPI smoke test
