# External Model Review Packet — v0.5.0

## Review question

Did this release add a usable frontend while preserving the validated backend and avoiding unnecessary architecture?

## Inspect

- `app/api_routes.py`
- `web/lib/api.ts`
- `web/components/dashboard.tsx`
- `web/components/course-workspace.tsx`
- `web/components/structured-output.tsx`
- `.github/workflows/ci.yml`
- `tests/test_product_api.py`

## Required critique

1. Find any UI path that mutates the wrong course.
2. Find API fields leaked unnecessarily.
3. Check whether draft examples can enter model evidence.
4. Identify frontend abstractions that are premature.
5. Identify missing error/loading states.
6. Check whether a smaller implementation would preserve all user-facing behavior.
7. Give reproducible evidence for every claimed bug.

## Non-goals

Do not request Redux, microservices, WebSockets, vector databases or a component library unless a concrete current defect requires them.
