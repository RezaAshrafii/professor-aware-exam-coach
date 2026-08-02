# Architecture

این نسخه عمداً یک modular monolith است:

```text
Browser UI (Jinja + JavaScript)
        ↓
FastAPI endpoints
        ↓
Services: retrieval, prompting, LLM validation
        ↓
Repositories
        ↓
SQLite + local uploads
```

## مرزها

- `schemas.py`: قرارداد ورودی و خروجی
- `repositories.py`: فقط persistence و query
- `services/`: منطق retrieval، prompt و validation
- `main.py`: HTTP orchestration
- `templates/static`: نمایش و تعامل

## تصمیم‌های عمدی

- فعلاً React/Next.js اضافه نشده؛ UI فعلی برای رسیدن سریع به محصول قابل استفاده کافی است.
- migration framework، vector database، queue و microservice نداریم.
- هر قابلیت جدید باید ابتدا ارزش مستقیم برای آمادگی امتحان داشته باشد.
