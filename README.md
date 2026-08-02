# Professor-Aware Exam Coach — v0.4.0

یک ابزار local-first برای آمادگی امتحان‌های ریاضی و آمار بر اساس منابع واقعی همان درس و روش‌های تدریس‌شده استاد.

## هدف فعلی

این پروژه قرار نیست یک پلتفرم آموزشی عظیم یا پروژه پژوهشی سنگین باشد. هدف عملی آن این است که:

- منابع هر درس جدا بمانند؛
- مثال‌های واقعی کلاس به‌شکل قابل استفاده ثبت شوند؛
- پاسخ‌ها بر اساس شواهد همان درس تولید و سخت‌گیرانه بررسی شوند؛
- دانشجو قبل از امتحان بتواند بدون AI پاسخ کامل و قابل دفاع بنویسد.

## قابلیت‌های v0.4.0

- workspace جدا برای هر درس و استاد؛
- ورود PDF، DOCX، TXT و Markdown؛
- lexical retrieval محلی؛
- خروجی‌های ساختاریافته و اعتبارسنجی‌شده برای profile، grading و study plan؛
- رد citation جعلی و یک repair attempt کنترل‌شده؛
- دفترچه خطا؛
- **Example Card** برای ثبت سؤال و راه‌حل واقعی استاد؛
- وضعیت `draft` و `confirmed` برای مثال‌ها؛
- فقط مثال‌های تأییدشده وارد retrieval و prompt می‌شوند؛
- اولویت بیشتر برای مثال تأییدشده در retrieval؛
- UI فارسی RTL؛
- ساختار GitHub استاندارد، CI، issue template، PR template و Dependabot؛
- تاریخچه واقعی Git با branch و commitهای Conventional Commits.

## اجرای سریع در ویندوز

فایل `start_windows.bat` را اجرا کن.

راه‌اندازی دستی:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

برنامه در این آدرس باز می‌شود:

```text
http://127.0.0.1:8000
```

## اجرای تست‌ها

تست‌های معمول:

```powershell
pytest -q
```

تمام بررسی‌های توسعه:

```powershell
pip install -r requirements-dev.txt
python scripts/check_all.py
```

## ثبت مثال استاد

1. وارد workspace درس شو.
2. تب «مثال‌های استاد» را باز کن.
3. متن تمیزشده سؤال و راه‌حل را وارد کن.
4. ابتدا به‌صورت پیش‌نویس ذخیره کن.
5. آن را با جزوه، تخته یا ویدئو تطبیق بده.
6. پس از تأیید، وضعیت را به `confirmed` تغییر بده.

کارت پیش‌نویس هرگز برای مدل ارسال نمی‌شود.

## انتقال به GitHub

این بسته خودش یک repository واقعی با `.git`، branchها، merge commit و tag نسخه است. دستورهای دقیق در [docs/GITHUB_SETUP.md](docs/GITHUB_SETUP.md) قرار دارند.

خلاصه:

```powershell
git remote add origin https://github.com/USERNAME/REPOSITORY.git
git push -u origin main
git push origin --all
git push origin --tags
```

## مسیر کوتاه تا نسخه 1.0

- `v0.5.0`: Method Card و فهرست روش‌های مجاز
- `v0.6.0`: کنترل اجباری روش مجاز در تولید و تصحیح پاسخ
- `v0.7.0`: export/import، preview منابع و رفع باگ‌های استفاده واقعی
- `v1.0.0`: نسخه پایدار شخصی

جزئیات در [docs/ROADMAP.md](docs/ROADMAP.md) است.

## محدودیت‌های فعلی

- Example Card به‌صورت دستی یا از متن تمیزشده وارد می‌شود؛ OCR و پردازش ویدئو داخل برنامه نیست.
- هنوز Method Registry مستقل نداریم.
- برنامه نمی‌تواند نمره کامل را تضمین کند.
- retrieval هنوز lexical است.
- رابط فعلی Jinja/JavaScript است؛ مهاجرت به React/Next.js فعلاً عمداً انجام نشده چون برای نسخه شخصی لازم نیست.

راهنمای تست دستی نسخه در [USER_VERIFICATION.md](USER_VERIFICATION.md) قرار دارد.
