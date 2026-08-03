@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title ACOS One-Click Updater

if not exist ".git" (
  echo [ERROR] Put this file in the ACOS project root, beside README.md and the app folder.
  pause
  exit /b 1
)

where powershell >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Windows PowerShell was not found.
  pause
  exit /b 1
)

for /f "delims=" %%S in ('git status --porcelain --untracked-files=no') do (
  echo [ERROR] Tracked project files have local changes.
  echo Commit or restore them before updating, then run this file again.
  git status --short
  pause
  exit /b 1
)

set "ACOS_ROOT=%CD%"
set "ACOS_ZIP=%~1"

echo [1/4] Finding the newest ACOS ZIP...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$root=$env:ACOS_ROOT;" ^
  "$requested=$env:ACOS_ZIP;" ^
  "if($requested){$zip=(Resolve-Path -LiteralPath $requested).Path}else{" ^
  "  $homeDir=[Environment]::GetFolderPath('UserProfile');" ^
  "  $dirs=@($root,(Join-Path $homeDir 'Downloads'),(Join-Path $homeDir 'Desktop')) | Select-Object -Unique;" ^
  "  $files=foreach($dir in $dirs){if(Test-Path -LiteralPath $dir){Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue | Where-Object {$_.Name -match '^(professor_aware_exam_coach|ACOS)[_-]?v?\d+.*\.zip$'}}};" ^
  "  $picked=$files | Sort-Object LastWriteTime -Descending | Select-Object -First 1;" ^
  "  if(-not $picked){throw 'No ACOS version ZIP was found in the project folder, Downloads, or Desktop.'};" ^
  "  $zip=$picked.FullName" ^
  "};" ^
  "Write-Host ('Using: '+$zip) -ForegroundColor Cyan;" ^
  "$tmp=Join-Path $env:TEMP ('acos-update-'+[guid]::NewGuid().ToString('N'));" ^
  "New-Item -ItemType Directory -Path $tmp | Out-Null;" ^
  "try{" ^
  "  Write-Host '[2/4] Extracting update...' -ForegroundColor DarkCyan;" ^
  "  Expand-Archive -LiteralPath $zip -DestinationPath $tmp -Force;" ^
  "  $candidates=@($tmp)+@(Get-ChildItem -LiteralPath $tmp -Directory -Recurse | ForEach-Object {$_.FullName});" ^
  "  $src=$candidates | Where-Object {(Test-Path (Join-Path $_ 'app')) -and (Test-Path (Join-Path $_ 'web')) -and (Test-Path (Join-Path $_ 'requirements.txt'))} | Sort-Object Length | Select-Object -First 1;" ^
  "  if(-not $src){throw 'The ZIP does not contain a valid ACOS project.'};" ^
  "  $version='unknown'; $project=Join-Path $src 'pyproject.toml'; if(Test-Path $project){$m=[regex]::Match((Get-Content $project -Raw),'version\s*=\s*\"([^\"]+)\"'); if($m.Success){$version=$m.Groups[1].Value}};" ^
  "  Write-Host ('Updating to v'+$version+'...') -ForegroundColor Green;" ^
  "  Write-Host '[3/4] Replacing code while preserving Git, data, keys and dependencies...' -ForegroundColor DarkCyan;" ^
  "  $tracked=& git -C $root ls-files;" ^
  "  foreach($relative in $tracked){if($relative -eq 'update_from_zip.bat'){continue}; $target=Join-Path $root $relative; if(Test-Path -LiteralPath $target -PathType Leaf){Remove-Item -LiteralPath $target -Force}};" ^
  "  & robocopy $src $root /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /XD .git .venv .dependency_state data node_modules .next /XF .env .env.local update_from_zip.bat;" ^
  "  $rc=$LASTEXITCODE; if($rc -gt 7){& git -C $root reset --hard HEAD | Out-Null; throw ('Copy failed with robocopy code '+$rc)};" ^
  "  Write-Host '[4/4] Update complete.' -ForegroundColor Green;" ^
  "  Write-Host 'Preserved: .git, data, API keys, .venv and web/node_modules.' -ForegroundColor Gray;" ^
  "} finally {if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue}}"

if errorlevel 1 (
  echo.
  echo Update failed. Nothing in data, API keys, .venv or node_modules was removed.
  pause
  exit /b 1
)

echo.
echo Starting ACOS. Dependencies install only if their requirement files changed...
call "%~dp0start_product_windows.bat"
exit /b %errorlevel%
