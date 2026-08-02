# PR: Add GitHub foundation and professor Example Cards

## Goal

Make the project maintainable on GitHub and let the user register cleaned professor examples without sending unverified notes to the model.

## Main changes

- repository standards and CI;
- Example Card schema and SQLite table;
- draft/confirmed workflow;
- confirmed cards included in retrieval;
- Persian review UI;
- isolation and retrieval tests.

## Out of scope

- Method Registry;
- OCR/video processing;
- React/Next.js migration;
- embeddings;
- fine-tuning;
- stateful exams.

## Verification

- 22 automated tests pass;
- JavaScript syntax check passes;
- manual checks are documented in `USER_VERIFICATION.md`.
