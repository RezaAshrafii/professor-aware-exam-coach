# User Verification — v0.7.2

## Update

1. Commit and push v0.7.1 so `git status` is clean.
2. Keep `professor_aware_exam_coach_v0_7_2.zip` in Downloads; do not extract it.
3. Put `UPDATE_ACOS.bat` and `ACOS_Update.ps1` in the permanent project root once.
4. Close the API and Web windows, then double-click `UPDATE_ACOS.bat`.
5. Confirm the updater prints that Python and frontend dependencies were skipped when their declarations did not change.

## Grading UI

1. Open the differential-equations course and choose «مربی پاسخ».
2. Confirm that question, answer and score are separate fields and no template must be typed.
3. Run the known incorrect solution for `y'=x+y`; expect a low score, the first divergence and a corrected answer.
4. Run the correct solution; expect a near-full/full score.
5. Confirm rubric items are cards, not a horizontally scrolling table.
6. Confirm natural-language report text is Persian and formulas appear in separate left-to-right blocks where possible.
7. Confirm only up to three evidence snippets are visible under a collapsed evidence section.
8. On an incorrect answer, click «ثبت در دفترچه خطا» and verify the mistake appears in the mistake log.
9. Run another grading request and verify the backend prompt includes prior mistake memory through the automated test suite.

## Git after successful verification

```powershell
git add -A
git commit -m "feat: release v0.7.2 simplified grading workflow"
git tag -a v0.7.2 -m "ACOS v0.7.2"
git push origin main --follow-tags
```
