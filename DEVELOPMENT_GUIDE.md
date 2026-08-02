# Development Guide

## 1. Product scope

Professor-Aware Exam Coach یک ابزار شخصی و local-first برای آمادگی امتحان‌های کمی است. پروژه عمداً کوچک نگه داشته می‌شود.

هدف:

1. ثبت شواهد واقعی تدریس استاد؛
2. استفاده از روش‌های تدریس‌شده در پاسخ؛
3. تصحیح سخت‌گیرانه و شفاف؛
4. آماده‌کردن دانشجو برای حل مستقل.

## 2. Non-goals

در مسیر فعلی این موارد پیاده نمی‌شوند مگر نیاز واقعی ثابت شود:

- microservice؛
- Kubernetes یا queue؛
- vector database مستقل؛
- multi-agent runtime؛
- fine-tuning؛
- شبکه اجتماعی یا چندکاربره؛
- analytics پژوهشی سنگین؛
- frontend framework جدید صرفاً برای نمایش تکنولوژی؛
- پردازش کامل ویدئو یا OCR پیچیده.

## 3. Current architecture

```text
Next.js product UI + Jinja fallback
                ↓
        FastAPI JSON/form API
                ↓
Services: retrieval / prompt / LLM validation
                ↓
          Repositories
                ↓
        SQLite + local files
```

این modular monolith برای ابزار تک‌کاربره کافی است.

## 4. Code boundaries

- `main.py`: برنامه FastAPI و routeهای UI fallback
- `api_routes.py`: قرارداد JSON مورد استفاده Next.js
- `schemas.py`: قرارداد داده
- `repositories.py`: تمام SQL
- `services/retrieval_service.py`: ranking خالص
- `services/prompt_service.py`: policy و prompt
- `services/llm_service.py`: provider، parsing، validation و repair
- `services/exam_coach_service.py`: هماهنگ‌کننده use case
- `templates/static`: UI قدیمی و fallback
- `web/`: رابط محصول Next.js و TypeScript

## 5. Data model

- `courses`: workspace درس
- `sources`: فایل اصلی
- `chunks`: قطعه‌های متنی
- `runs`: تاریخچه اجرا
- `mistakes`: دفترچه خطا
- `example_cards`: سؤال و راه‌حل ثبت‌شده استاد

قانون ثابت از v0.4.0: فقط Example Card با وضعیت `confirmed` می‌تواند وارد retrieval شود.

## 6. Git workflow

- `main` فقط نسخه سالم
- branch کوتاه برای هر تغییر
- Conventional Commits
- PR حتی برای توسعه شخصی
- merge فقط پس از CI و تست دستی لازم

جزئیات: `docs/GIT_WORKFLOW.md`

## 7. Definition of done

یک قابلیت تمام‌شده است اگر:

- مسئله مشخصی را حل کند؛
- schema و persistence روشن داشته باشد؛
- تست خودکار مسیر اصلی و failure مهم را پوشش دهد؛
- تست دستی لازم نوشته شده باشد؛
- README و CHANGELOG به‌روز باشند؛
- داده شخصی وارد Git نشود.

## 8. Short roadmap

### v0.4.0 — completed

- GitHub repository foundation
- Example Card
- draft/confirmed evidence gate

### v0.5.0 — completed

- Next.js product UI
- JSON API for all current workflows
- responsive Persian RTL workspace
- frontend type-check/build CI gate
- legacy UI retained as fallback

### v0.6.0

Method Card ساده:

- نام روش
- شرایط استفاده
- مراحل اجباری
- نمادگذاری استاد
- اتصال به Example Cardهای تأییدشده
- وضعیت draft/confirmed

### v0.7.0

Allowed Method Enforcement:

- انتخاب روش تأییدشده پیش از پاسخ
- هشدار روش خارج از منابع
- grading سخت‌گیرانه بر اساس مراحل روش

### v0.8.0

پایدارسازی:

- export/import workspace
- source/chunk preview
- prompt regression fixtures
- رفع باگ‌های استفاده واقعی

### v1.0.0

- قرارداد داده پایدار
- نصب و اجرای روشن
- تست‌های backend و frontend سبز
- استفاده موفق روی چند درس واقعی
- مستندات کامل

## 9. Stop conditions against over-engineering

قابلیت جدید اضافه نشود اگر:

- با یک فرم یا query ساده حل می‌شود ولی برایش framework جدید پیشنهاد شده؛
- دو مصرف واقعی برای abstraction وجود ندارد؛
- metric یا failure واقعی برای ارتقای retrieval نداریم؛
- فقط ارزش ظاهری رزومه دارد؛
- زمان رسیدن به ابزار قابل استفاده را عقب می‌اندازد.
