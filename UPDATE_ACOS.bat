@echo off
setlocal
cd /d "%~dp0"
title ACOS Update

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0ACOS_Update.ps1" %*
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if "%EXIT_CODE%"=="0" (
    echo Update finished successfully.
    echo Test the app, then commit and push the changes.
) else (
    echo Update failed. Read the error above.
)

pause
exit /b %EXIT_CODE%
