# One-click ZIP updates on Windows

`update_from_zip.bat` updates the existing Git working directory from the newest ACOS ZIP found in:

1. the project root;
2. the user's Downloads folder;
3. the user's Desktop.

It preserves `.git`, `data`, `.env`, `web/.env.local`, `.venv`, `.dependency_state`, `web/node_modules`, and `web/.next`.

## Normal use

1. Download the new release ZIP. Leave it in Downloads.
2. Close the ACOS API and Web terminal windows.
3. Double-click `update_from_zip.bat` in the permanent project folder.
4. The updater applies the ZIP and starts ACOS.

You can also drag a specific ZIP onto `update_from_zip.bat` or run:

```powershell
.\update_from_zip.bat "C:\path\to\release.zip"
```

The updater refuses to overwrite tracked local changes. Commit or restore those changes first.
