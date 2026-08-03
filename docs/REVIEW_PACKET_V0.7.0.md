# External Review Packet — v0.7.0

Review the diff from `v0.6.0` to `v0.7.0`.

## Goal

Replace the demo-only OpenAI-specific runtime with a small, provider-neutral two-slot runtime and eliminate repeated dependency installation.

## Review questions

1. آیا API key از backend به frontend نشت می‌کند؟
2. آیا provider abstraction بیش از نیاز پیچیده شده است؟
3. آیا مدل‌ها واقعاً dynamic هستند یا catalog مخفی هاردکد شده؟
4. آیا fallback از Chat Completions به Responses محدود و قابل فهم است؟
5. آیا active connection در هر run تازه resolve می‌شود؟
6. آیا bootstrap فقط هنگام تغییر dependency نصب می‌کند؟
7. چه failure path مهمی تست نشده است؟

## Out of scope

- OAuth provider login؛
- encrypted multi-user vault؛
- streaming؛
- model pricing optimizer؛
- automatic provider fallback between slots.
