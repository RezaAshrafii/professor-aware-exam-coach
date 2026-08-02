# Professor-Aware Exam Coach — v0.6.0

ابزار local-first برای آماده‌شدن قبل از امتحان با تکیه بر منابع و مثال‌های واقعی همان استاد.

## اجرای سریع در ویندوز

روی فایل زیر دوبار کلیک کن:

```text
start_product_windows.bat
```

اسکریپت هر دو سرویس را بالا می‌آورد، آماده‌شدن API و UI را بررسی می‌کند و بعد مرورگر را باز می‌کند:

```text
http://localhost:3000
```

در استفاده عادی، مرورگر از مسیر same-origin زیر به backend وصل می‌شود:

```text
http://localhost:3000/backend/...
```

به همین دلیل اتصال اصلی دیگر به CORS مرورگر وابسته نیست. API مستقیم نیز برای توسعه روی `http://127.0.0.1:8000` باقی مانده است.

## تغییر اصلی v0.6.0

- رفع خطای `CORS preflight 405`؛
- proxy داخلی Next.js برای API؛
- حذف header غیرضروری `Content-Type` از درخواست‌های GET؛
- launcher مطمئن‌تر که قبل از بازکردن مرورگر سلامت هر دو سرویس را چک می‌کند؛
- بازطراحی سبک UI با خوانایی بهتر، کارت‌های کم‌حجم‌تر و workspace مینیمال‌تر؛
- بدون کتابخانه UI یا وابستگی سنگین جدید.

## امکانات فعلی

- ساخت، ویرایش و حذف درس؛
- بارگذاری PDF، DOCX، TXT و Markdown؛
- ثبت و تأیید Example Card؛
- اجرای grading، professor profile، study plan و حالت‌های متنی؛
- نمایش structured output و evidence؛
- تاریخچه اجرا و دفترچه خطا؛
- UI فارسی RTL و responsive.

## تست‌ها

```bash
pip install -r requirements-dev.txt
python scripts/check_all.py
```

Frontend در CI:

```bash
cd web
npm install
npm run typecheck
npm run build
```

در محیط ساخت این بسته، npm registry داخلی پکیج `@types/node` را ارائه نکرد؛ بنابراین production build در همین محیط اجرا نشد. syntax فایل‌های TypeScript، قرارداد proxy و تمام تست‌های backend اجرا شده‌اند. `next build` همچنان gate گیت‌هاب و سیستم تو است.

راهنمای تست دستی: [USER_VERIFICATION.md](USER_VERIFICATION.md)
