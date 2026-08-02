# Architecture — v0.5.0

پروژه همچنان یک modular monolith است؛ فقط رابط محصول از backend جدا شده است.

```text
Browser
  ↓
Next.js App Router + TypeScript       web/
  ↓ HTTP JSON / multipart
FastAPI product API                  app/api_routes.py
  ↓
Existing services                    app/services/
  ↓
Repositories                         app/repositories.py
  ↓
SQLite + local uploads
```

## تصمیم‌های عمدی

- backend فعلی بازنویسی نشده است؛
- UI قدیمی Jinja فعلاً حذف نشده و fallback است؛
- state manager سراسری، Redux، WebSocket و microservice نداریم؛
- frontend مستقیماً قرارداد JSON ساده FastAPI را مصرف می‌کند؛
- داده حساس و فایل‌ها local-first باقی می‌مانند؛
- تغییرات UI نباید retrieval یا validation را تغییر دهند.

## مرز فایل‌ها

- `app/api_routes.py`: API مورد استفاده Next.js؛
- `app/main.py`: برنامه FastAPI و UI fallback؛
- `web/lib/api.ts`: تنها مسیر ارتباط frontend با backend؛
- `web/lib/types.ts`: قراردادهای TypeScript؛
- `web/components/dashboard.tsx`: ساخت و فهرست درس‌ها؛
- `web/components/course-workspace.tsx`: workspace و عملیات اصلی؛
- `web/components/structured-output.tsx`: نمایش خروجی‌های schema‌دار؛
- `web/app/globals.css`: design system سبک بدون کتابخانه UI خارجی.

## چیزی که عمداً نداریم

- SSR پیچیده یا Server Actions برای mutationها؛
- احراز هویت؛
- cloud database؛
- queue؛
- چند frontend package؛
- Tailwind/shadcn dependency؛
- abstraction عمومی قبل از نیاز واقعی.
