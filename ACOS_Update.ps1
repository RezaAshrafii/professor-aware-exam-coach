param(
    [string]$ZipPath = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Get-HashOrEmpty {
    param([string]$Path)
    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
    }
    return ""
}

function Fail {
    param([string]$Message)
    Write-Host ""
    Write-Host "[ERROR] $Message" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath (Join-Path $Root ".git") -PathType Container)) {
    Fail "Put UPDATE_ACOS.bat and ACOS_Update.ps1 in the root of the Git repository."
}

$trackedChanges = @(& git status --porcelain --untracked-files=no)
if ($LASTEXITCODE -ne 0) {
    Fail "Git status failed."
}
if ($trackedChanges.Count -gt 0) {
    Write-Host "[ERROR] Commit or restore tracked changes before updating." -ForegroundColor Red
    & git status --short
    exit 1
}

if ([string]::IsNullOrWhiteSpace($ZipPath)) {
    $searchDirs = @(
        (Join-Path $env:USERPROFILE "Downloads"),
        $Root,
        (Join-Path $env:USERPROFILE "Desktop")
    ) | Select-Object -Unique

    $candidates = foreach ($dir in $searchDirs) {
        if (Test-Path -LiteralPath $dir -PathType Container) {
            Get-ChildItem -LiteralPath $dir -File -Filter "*.zip" -ErrorAction SilentlyContinue |
                Where-Object {
                    $_.Name -match '(?i)^(professor_aware_exam_coach|ACOS).*v?\d+.*\.zip$'
                }
        }
    }

    $picked = $candidates |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if (-not $picked) {
        Fail "No ACOS release ZIP was found in Downloads, Desktop, or the project folder."
    }

    $ZipPath = $picked.FullName
}

try {
    $ZipPath = (Resolve-Path -LiteralPath $ZipPath).Path
}
catch {
    Fail "ZIP file not found: $ZipPath"
}

Write-Host ""
Write-Host "ACOS updater" -ForegroundColor Cyan
Write-Host "Using ZIP: $ZipPath" -ForegroundColor DarkCyan

$oldRequirementsHash = Get-HashOrEmpty (Join-Path $Root "requirements.txt")
$oldPackageLockHash = Get-HashOrEmpty (Join-Path $Root "web\package-lock.json")

$tempDir = Join-Path $env:TEMP ("acos-update-" + [guid]::NewGuid().ToString("N"))

try {
    New-Item -ItemType Directory -Path $tempDir | Out-Null

    Write-Host "[1/4] Extracting release..." -ForegroundColor Cyan
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $tempDir -Force

    $projectRoots = @($tempDir) + @(
        Get-ChildItem -LiteralPath $tempDir -Directory -Recurse -ErrorAction SilentlyContinue |
            ForEach-Object { $_.FullName }
    )

    $Source = $projectRoots |
        Where-Object {
            (Test-Path -LiteralPath (Join-Path $_ "app") -PathType Container) -and
            (Test-Path -LiteralPath (Join-Path $_ "web") -PathType Container) -and
            (Test-Path -LiteralPath (Join-Path $_ "requirements.txt") -PathType Leaf)
        } |
        Sort-Object Length |
        Select-Object -First 1

    if (-not $Source) {
        throw "The ZIP does not contain a valid ACOS project."
    }

    Write-Host "[2/4] Updating code..." -ForegroundColor Cyan

    $robocopyArgs = @(
        $Source,
        $Root,
        "/MIR",
        "/R:2",
        "/W:1",
        "/XJ",
        "/NFL",
        "/NDL",
        "/NJH",
        "/NJS",
        "/NP",
        "/XD",
        ".git",
        ".venv",
        ".dependency_state",
        "data",
        "node_modules",
        ".next",
        "__pycache__",
        "/XF",
        ".env",
        ".env.local",
        "UPDATE_ACOS.bat",
        "ACOS_Update.ps1",
        "ACOS_One_Click_Updater.bat",
        "update_from_zip.bat"
    )

    & robocopy @robocopyArgs
    $copyCode = $LASTEXITCODE

    if ($copyCode -gt 7) {
        & git reset --hard HEAD | Out-Null
        throw "Robocopy failed with exit code $copyCode."
    }

    Write-Host "[3/4] Checking dependencies..." -ForegroundColor Cyan

    $newRequirementsHash = Get-HashOrEmpty (Join-Path $Root "requirements.txt")
    $newPackageLockHash = Get-HashOrEmpty (Join-Path $Root "web\package-lock.json")

    if ($oldRequirementsHash -ne $newRequirementsHash) {
        Write-Host "Python requirements changed; installing only the new requirements." -ForegroundColor Yellow

        $pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
        if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
            Write-Host "Creating .venv once..." -ForegroundColor Yellow
            & py -3 -m venv (Join-Path $Root ".venv")
            if ($LASTEXITCODE -ne 0) {
                throw "Could not create the Python virtual environment."
            }
        }

        & $pythonExe -m pip install -r (Join-Path $Root "requirements.txt")
        if ($LASTEXITCODE -ne 0) {
            throw "Python dependency installation failed."
        }
    }
    else {
        Write-Host "Python dependencies unchanged; skipped." -ForegroundColor DarkGray
    }

    if ($oldPackageLockHash -ne $newPackageLockHash) {
        Write-Host "Frontend lock file changed; installing only the required frontend dependencies." -ForegroundColor Yellow
        Push-Location (Join-Path $Root "web")
        try {
            if (Test-Path -LiteralPath "package-lock.json" -PathType Leaf) {
                & npm ci
            }
            else {
                & npm install
            }
            if ($LASTEXITCODE -ne 0) {
                throw "Frontend dependency installation failed."
            }
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-Host "Frontend dependencies unchanged; skipped." -ForegroundColor DarkGray
    }

    Write-Host "[4/4] Update completed." -ForegroundColor Green
    Write-Host "Preserved: Git history, data, uploads, API keys, .venv, and node_modules." -ForegroundColor DarkGray
    Write-Host ""
    & git status --short
}
catch {
    Write-Host ""
    Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Tracked files were restored when possible. Local data and API keys were not removed." -ForegroundColor Yellow
    exit 1
}
finally {
    if (Test-Path -LiteralPath $tempDir) {
        Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

exit 0
