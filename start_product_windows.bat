@echo off
setlocal
cd /d %~dp0
title Exam Coach Launcher

where node >nul 2>nul
if errorlevel 1 (
  echo Node.js 20.9 or newer is required.
  pause
  exit /b 1
)

py -3 scripts\bootstrap.py 2>nul || python scripts\bootstrap.py
if errorlevel 1 goto :error

echo [1/3] Starting FastAPI...
start "Exam Coach API" cmd /k "cd /d %~dp0 && .venv\Scripts\python.exe run.py"

echo [2/3] Starting Next.js UI...
start "Exam Coach Web" cmd /k "cd /d %~dp0web && set NEXT_PUBLIC_API_URL=&& set BACKEND_INTERNAL_URL=http://127.0.0.1:8000&& npm run dev"

echo [3/3] Waiting for both services...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$api=$false; $web=$false; for($i=0;$i -lt 60;$i++){ try { $r=Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health -TimeoutSec 1; if($r.StatusCode -eq 200){$api=$true} } catch {}; try { $r=Invoke-WebRequest -UseBasicParsing http://localhost:3000/backend/health -TimeoutSec 1; if($r.StatusCode -eq 200){$web=$true} } catch {}; if($api -and $web){break}; Start-Sleep -Milliseconds 700 }; if(-not $api){Write-Host 'Backend did not become ready.' -ForegroundColor Red; exit 1}; if(-not $web){Write-Host 'Frontend did not become ready.' -ForegroundColor Red; exit 2}"
if errorlevel 1 goto :error

start "" http://localhost:3000
echo.
echo Exam Coach is ready. Future starts skip dependency installation unless files changed.
exit /b 0

:error
echo.
echo Startup failed. Keep the API and Web windows open and review the first red error.
pause
exit /b 1
