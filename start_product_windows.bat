@echo off
setlocal
cd /d %~dp0

where node >nul 2>nul
if errorlevel 1 (
  echo Node.js 20.9 or newer is required for the product UI.
  pause
  exit /b 1
)

if not exist .venv\Scripts\python.exe (
  echo [1/5] Creating Python environment...
  py -3.11 -m venv .venv 2>nul || python -m venv .venv
  if errorlevel 1 goto :error
  .venv\Scripts\python.exe -m pip install --upgrade pip
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 goto :error
)

if not exist .env copy /Y .env.example .env >nul
if not exist web\.env.local copy /Y web\.env.local.example web\.env.local >nul

if not exist web\node_modules\next (
  echo [2/5] Installing Next.js frontend dependencies...
  pushd web
  call npm install --no-audit --no-fund
  if errorlevel 1 (popd & goto :error)
  popd
)

echo [3/5] Starting FastAPI at http://127.0.0.1:8000
start "Exam Coach API" /min cmd /c ".venv\Scripts\python.exe run.py"

echo [4/5] Starting Next.js at http://localhost:3000
timeout /t 2 /nobreak >nul
start "" http://localhost:3000

echo [5/5] Product UI is running. Close this window or press Ctrl+C to stop the frontend.
pushd web
call npm run dev
popd
exit /b 0

:error
echo.
echo Setup failed. Review the error above.
pause
exit /b 1
