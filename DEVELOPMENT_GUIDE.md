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
- React/Next.js صرفاً برای نمایش تکنولوژی؛
- پردازش کامل ویدئو یا OCR پیچیده.

## 3. Current architecture

```text
Jinja + Vanilla JavaScript UI
            ↓
         FastAPI
            ↓
Services: retrieval / prompt / LLM validation
            ↓
       Repositories
            ↓
     SQLite + local files
```

این modular monolith برای ابزار تک‌کاربره کافی است.

## 4. Code boundaries

- `main.py`: route و orchestration
- `schemas.py`: قرارداد داده
- `repositories.py`: تمام SQL
- `services/retrieval_service.py`: ranking خالص
- `services/prompt_service.py`: policy و prompt
- `services/llm_service.py`: provider، parsing، validation و repair
- `services/exam_coach_service.py`: هماهنگ‌کننده use case
- `templates/static`: UI

## 5. Data model

- `courses`: workspace درس
- `sources`: فایل اصلی
- `chunks`: قطعه‌های متنی
- `runs`: تاریخچه اجرا
- `mistakes`: دفترچه خطا
- `example_cards`: سؤال و راه‌حل ثبت‌شده استاد

قانون v0.4.0: فقط Example Card با وضعیت `confirmed` می‌تواند وارد retrieval شود.

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
- CI and contribution files
- Example Card
- draft/confirmed gate
- confirmed examples in retrieval

### v0.5.0

Method Card ساده:

- نام روش
- شرایط استفاده
- مراحل اجباری
- نمادگذاری استاد
- شواهد Example Card
- وضعیت confirmed/draft

### v0.6.0

Allowed Method Enforcement:

- انتخاب روش پیش از تولید پاسخ
- هشدار روش خارج از منابع
- blocking در نسخه برگه، مگر کاربر صریحاً روش استاندارد خارج از جزوه را بخواهد
- grading سخت‌گیرانه بر اساس مراحل روش

### v0.7.0

پایدارسازی:

- export/import کامل workspace
- preview source/chunk
- bug fixes بر اساس استفاده واقعی
- prompt regression fixtureهای ثابت

### v1.0.0

- قرارداد داده پایدار
- نصب و اجرای روشن
- تست‌های اصلی سبز
- استفاده موفق روی چند درس واقعی
- مستندات کامل

## 9. Stop conditions against over-engineering

قابلیت جدید اضافه نشود اگر:

- با یک فرم یا query ساده حل می‌شود ولی برایش framework جدید پیشنهاد شده؛
- دو مصرف واقعی برای abstraction وجود ندارد؛
- metric یا failure واقعی برای ارتقای retrieval نداریم؛
- فقط ارزش ظاهری رزومه دارد؛
- زمان رسیدن به ابزار قابل استفاده را عقب می‌اندازد.
