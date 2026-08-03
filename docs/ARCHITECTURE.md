# Architecture — v0.7.0

پروژه یک modular monolith تک‌کاربره است.

```text
Browser
  ↓ same-origin /backend
Next.js App Router + TypeScript
  ↓
FastAPI product API
  ↓
ExamCoachService ─ ModelConnectionService ─ RetrievalService
  ↓
Repositories
  ↓
SQLite + uploads + local secret file
```

## مرزها

- `web/lib/api.ts`: تنها client ارتباط frontend؛
- `app/api_routes.py`: API محصول؛
- `app/services/model_connection_service.py`: discovery و اجرای provider؛
- `app/services/llm_service.py`: validation و repair مستقل از provider؛
- `app/repositories.py`: SQL؛
- `data/model_secrets.json`: کلیدهای local-only و خارج از Git.

## تصمیم‌های عمدی

- دو connection slot، نه سیستم provider plugin پیچیده؛
- مدل‌ها از API کشف می‌شوند، نه catalog هاردکد؛
- Gemini native REST و OpenAI-compatible با fallback محدود؛
- no Redux, no component library, no microservice؛
- browser از proxy داخلی Next استفاده می‌کند؛
- UI قدیمی Jinja هنوز fallback است.
