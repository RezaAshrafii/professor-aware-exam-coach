@echo off
setlocal
cd /d %~dp0
if not exist .venv\Scripts\python.exe (
  echo First setup has not run. Use start_product_windows.bat once.
  pause
  exit /b 1
)
if not exist web\node_modules\next (
  echo Frontend dependencies are missing. Use start_product_windows.bat once.
  pause
  exit /b 1
)
start "Exam Coach API" cmd /k "cd /d %~dp0 && .venv\Scripts\python.exe run.py"
start "Exam Coach Web" cmd /k "cd /d %~dp0web && set NEXT_PUBLIC_API_URL=&& set BACKEND_INTERNAL_URL=http://127.0.0.1:8000&& npm run dev"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ready=$false; for($i=0;$i -lt 50;$i++){ try { $r=Invoke-WebRequest -UseBasicParsing http://localhost:3000/backend/health -TimeoutSec 1; if($r.StatusCode -eq 200){$ready=$true; break} } catch {}; Start-Sleep -Milliseconds 500 }; if(-not $ready){exit 1}"
if errorlevel 1 (
  echo Services did not become ready. Review the API and Web windows.
  pause
  exit /b 1
)
start "" http://localhost:3000
