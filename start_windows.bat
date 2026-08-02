@echo off
setlocal
cd /d %~dp0

if not exist .venv\Scripts\python.exe (
  echo [1/3] Creating virtual environment...
  py -3.11 -m venv .venv 2>nul || python -m venv .venv
  if errorlevel 1 goto :error
  echo [2/3] Installing dependencies...
  .venv\Scripts\python.exe -m pip install --upgrade pip
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 goto :error
)

if not exist .env copy /Y .env.example .env >nul

echo [3/3] Starting Exam Coach at http://127.0.0.1:8000
.venv\Scripts\python.exe run.py
goto :eof

:error
echo.
echo Setup failed. Review the error above.
pause
exit /b 1
