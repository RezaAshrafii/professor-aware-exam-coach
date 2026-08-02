# Release checklist

- [ ] `pytest -q` passes
- [ ] `python -m compileall -q app tests` passes
- [ ] `node --check app/static/app.js` passes
- [ ] required manual checks in `USER_VERIFICATION.md` pass
- [ ] README and CHANGELOG match the implementation
- [ ] no `.env`, database, uploads, or course material are tracked
- [ ] working tree is clean
- [ ] version in `pyproject.toml` is correct
- [ ] tag is created from `main`
