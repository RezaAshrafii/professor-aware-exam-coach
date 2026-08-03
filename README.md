# Professor-Aware Exam Coach — v0.7.0

ابزار local-first برای تمرین و تصحیح پاسخ‌های دانشگاهی بر اساس منابع همان درس.

## اجرای سریع در ویندوز

روی این فایل دوبار کلیک کن:

```text
start_product_windows.bat
```

در اجرای اول محیط Python و وابستگی‌های frontend نصب می‌شوند. اجراهای بعدی فقط hash وابستگی‌ها را چک می‌کنند و اگر تغییری نکرده باشد هیچ نصب یا ارتقای pip انجام نمی‌شود.

برای اجرای کاملاً سریع بعد از نصب اولیه:

```text
start_fast_windows.bat
```

رابط اصلی:

```text
http://localhost:3000
```

## مدل و API

از داشبورد روی «مدل و API» بزن یا برو به:

```text
http://localhost:3000/settings
```

دو slot عمومی داری. هر slot می‌تواند یکی از این دو قرارداد را استفاده کند:

- Gemini API
- OpenAI-compatible API

Base URL و API key را وارد می‌کنی، برنامه فهرست مدل‌ها را مستقیم از همان API می‌گیرد، سپس با جست‌وجوی کوتاه مدل را انتخاب می‌کنی. هیچ مدل مشخصی در UI هاردکد نشده است.

کلیدها فقط داخل `data/model_secrets.json` روی سیستم محلی ذخیره می‌شوند، در پاسخ API نمایش داده نمی‌شوند و توسط `.gitignore` وارد Git نمی‌شوند.

## تغییرات اصلی v0.7.0

- اتصال واقعی Gemini API؛
- اتصال عمومی OpenAI-compatible برای OpenAI، OpenRouter و سرویس‌های سازگار؛
- discovery پویای مدل‌ها از endpoint خود سرویس؛
- دو API slot با یک UI مشترک و searchable model picker؛
- انتخاب یک مدل فعال برای تمام درس‌ها؛
- تست اتصال و نمایش provider/model واقعی در خروجی؛
- حذف وابستگی مستقیم به پکیج OpenAI؛
- startup هوشمند بدون نصب تکراری وابستگی‌ها؛
- `start_fast_windows.bat` برای اجرای فوری بعد از setup اولیه.

## تست‌ها

```bash
python -m pytest
node scripts/check_frontend_syntax.mjs
```

CI علاوه بر این‌ها type-check و production build فرانت را اجرا می‌کند.

راهنمای تست دستی: [USER_VERIFICATION.md](USER_VERIFICATION.md)
