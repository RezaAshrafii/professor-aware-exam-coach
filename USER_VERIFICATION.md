# User Verification — v0.7.1

## Required manual test

1. Keep the v0.7.1 ZIP in Downloads.
2. In the permanent project folder, double-click `update_from_zip.bat`.
3. Confirm the updater reports that `.git`, `data`, API keys, `.venv`, and `node_modules` were preserved.
4. Confirm ACOS opens at `http://localhost:3000`.
5. Confirm the existing course, uploaded PDF, and saved model connection are still present.
6. Run the same differential-equations grading request once.

## Pass gate

The version passes only if no Python or npm reinstall occurs when dependency files are unchanged, existing data remains available, and the selected real model produces a non-demo response.
