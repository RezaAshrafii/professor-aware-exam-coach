# Git workflow

## شاخه پایدار

`main` فقط باید شامل نسخه‌ای باشد که تست خودکار و تست دستی لازم را پاس کرده است.

## مسیر هر قابلیت

```text
main
  └── feat/example-cards
        ├── schema/database commit
        ├── API/UI commit
        └── tests/docs commit
```

## پیام commit

```text
feat(examples): add example card persistence
fix(retrieval): include confirmed examples in evidence
 test(examples): cover create and delete workflow
```

## تنظیم پیشنهادی GitHub

در Settings → Branches برای `main`:

- Require a pull request before merging
- Require status checks to pass
- انتخاب check با نام `quality`
- Block force pushes
- Require conversation resolution

برای یک مخزن شخصی، یک approval اجباری لازم نیست؛ هدف این است که خود PR و CI سابقه تصمیم را نگه دارند.
