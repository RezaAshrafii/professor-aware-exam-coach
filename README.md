# Professor-Aware Exam Coach

Local-first AI study workspace for practicing and reviewing university answers against the course sources supplied by the student.

> The project is an experimental educational tool, not an automated replacement for a professor or an official grading system. Model output must be reviewed by a human.

## Highlights

- Separate question, student answer and score/rubric inputs
- Retrieval from course materials with visible evidence snippets
- Structured grading output with schema validation and one repair attempt
- Gemini and OpenAI-compatible model connections discovered at runtime
- Local storage for course data and model credentials
- RTL/LTR-friendly Persian interface with formula and source rendering
- FastAPI backend, Next.js frontend and SQLite persistence

## Architecture

```text
Next.js UI
   ↓ same-origin backend proxy
FastAPI API
   ↓
ExamCoach / model / retrieval services
   ↓
Repositories → SQLite + local uploads + local model-key file
```

The application is intentionally a modular monolith. It avoids microservices and external vector databases until measured product needs justify them.

## Run on Windows

Requirements: Python 3.11+, Node.js 20+ and npm.

```powershell
git clone https://github.com/RezaAshrafii/professor-aware-exam-coach.git
cd professor-aware-exam-coach
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd web
npm install
npm run dev
```

The included launcher scripts can also be used after the first setup:

```text
start_product_windows.bat
```

The web UI runs at `http://localhost:3000`. API keys are stored locally in `data/model_secrets.json` and must never be committed.

## Tests

From the repository root:

```bash
python -m pytest
node scripts/check_frontend_syntax.mjs
```

Manual verification flows are documented in [USER_VERIFICATION.md](USER_VERIFICATION.md). Development boundaries and the definition of done are in [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md).

## Security and privacy

- Keep `.env`, local model secrets, uploaded course files and generated data outside Git.
- Use `.env.example` as the template for configuration.
- Do not send private course material to a provider unless the user has chosen and authorised that provider.
- Treat model feedback as assistance; validate evidence and grading decisions independently.

## Current status

The repository contains a working v0.7.2 product milestone with automated backend/frontend checks. Some provider integrations and Windows speech/packaging workflows remain environment-dependent and should be verified locally before a production release.

## Roadmap

- Export/import a complete study workspace
- Improve source chunk preview and review history
- Add a polished release package and CI status
- Expand human-verification flows with representative course data

## License

No license has been declared yet. Until one is added, treat the source as all rights reserved.
