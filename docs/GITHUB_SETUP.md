# GitHub setup

این پوشه از قبل یک Git repository واقعی است. تاریخچه را بررسی کن:

```powershell
git log --oneline --graph --decorate --all
```

## ساخت repository

1. در GitHub یک repository خالی بساز.
2. README یا `.gitignore` خودکار GitHub را فعال نکن، چون پروژه از قبل این فایل‌ها را دارد.
3. داخل پوشه پروژه اجرا کن:

```powershell
git remote add origin https://github.com/USERNAME/REPOSITORY.git
git push -u origin main
git push origin --all
git push origin --tags
```

## تنظیم branch protection

در GitHub:

`Settings → Branches → Add branch protection rule`

برای `main`:

- Require a pull request before merging
- Require status checks to pass before merging
- انتخاب check با نام `quality`
- Require conversation resolution
- Block force pushes

## اجرای توسعه بعدی

```powershell
git switch main
git pull
git switch -c feat/method-cards
```

پس از تغییر:

```powershell
python scripts/check_all.py
git add .
git commit -m "feat(methods): add method cards"
git push -u origin feat/method-cards
```

سپس در GitHub Pull Request بساز.

## بررسی رابط محصول پس از push

در اولین Pull Request، هر سه مرحله زیر باید سبز شوند:

- backend tests و contract checks؛
- TypeScript type-check؛
- Next.js production build.

پس از سبزشدن CI، تست دستی `USER_VERIFICATION.md` را انجام بده.
