# Professor-Aware Exam Coach — v0.5.0

یک ابزار local-first برای آماده‌شدن قبل از امتحان، بر اساس منابع و مثال‌های واقعی همان استاد.

## رابط جدید

این نسخه یک UI مستقل با Next.js و TypeScript دارد. رابط قدیمی FastAPI همچنان به‌عنوان fallback باقی مانده است.

### اجرای کامل در ویندوز

روی این فایل دوبار کلیک کن:

```text
start_product_windows.bat
```

بعد برنامه در این آدرس باز می‌شود:

```text
http://localhost:3000
```

Backend در این آدرس است:

```text
http://127.0.0.1:8000
```

### اجرای کامل در Linux/macOS

```bash
./start_product_unix.sh
```

## کارهایی که از UI انجام می‌شوند

- ساخت، ویرایش و حذف درس؛
- دیدن آمار منابع، مثال‌ها، اجراها و خطاها؛
- بارگذاری PDF، DOCX، TXT و Markdown؛
- ثبت Example Card به‌صورت پیش‌نویس یا تأییدشده؛
- تأیید/لغو تأیید و حذف مثال‌ها؛
- اجرای مربی در حالت‌های grading، profile، plan و حالت‌های متنی؛
- نمایش structured grading، پروفایل استاد و برنامه مطالعه؛
- دیدن evidence هر پاسخ؛
- تاریخچه اجراها؛
- دفترچه خطا؛
- تنظیمات هر درس.

## ساختار

```text
Next.js UI :3000
      ↓ JSON API
FastAPI :8000
      ↓
Services + SQLite + local uploads
```

جزئیات معماری در [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) است.

## اجرای تست‌ها

Backend و قراردادها:

```bash
pip install -r requirements-dev.txt
python scripts/check_all.py
```

Frontend پس از نصب وابستگی‌ها:

```bash
cd web
npm install
npm run typecheck
npm run build
```

## GitHub

مخزن شامل branch، commitهای واقعی، CI، PR template، issue template و tag نسخه است. راه‌اندازی در [docs/GITHUB_SETUP.md](docs/GITHUB_SETUP.md) توضیح داده شده است.

## محدودیت‌های این نسخه

- Method Registry مستقل هنوز ساخته نشده است.
- OCR و پردازش ویدئو داخل برنامه نیست.
- retrieval هنوز lexical است.
- npm registry در محیط ساخت این بسته در دسترس نبود؛ بنابراین `next build` اینجا اجرا نشد و باید در GitHub Actions یا سیستم تو تأیید شود. syntax فایل‌های TypeScript و تمام قراردادهای backend بررسی شده‌اند.

راهنمای تست دستی: [USER_VERIFICATION.md](USER_VERIFICATION.md)
