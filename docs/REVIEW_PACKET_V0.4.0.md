# Model review packet — v0.4.0

## Review objective

Check whether v0.4.0 adds the smallest useful feature and a credible GitHub workflow without unnecessary architecture.

## Files to focus on

- `app/database.py`
- `app/schemas.py`
- `app/repositories.py`
- `app/services/exam_coach_service.py`
- `app/services/retrieval_service.py`
- `app/templates/course.html`
- `tests/test_app.py`
- `.github/workflows/ci.yml`

## Questions for reviewer

1. Can a draft Example Card reach the model in any normal path?
2. Can one course modify another course's Example Card through the routes?
3. Is the retrieval representation simple enough to replace later?
4. Is any new abstraction unused or premature?
5. Does CI enforce checks that can realistically pass on this codebase?
6. Is any CHANGELOG claim unsupported by code or tests?

## Explicit non-goals

Do not recommend React, a vector database, agents, fine-tuning, migrations framework, or media processing unless a concrete current failure requires it.
