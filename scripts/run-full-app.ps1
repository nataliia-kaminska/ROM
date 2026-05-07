param(
    [switch]$SkipWorker,
    [switch]$SkipScheduler,
    [switch]$NoDockerRedis,
    [switch]$RequireBackground
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Frontend = Join-Path $Root "frontend"

if (-not (Test-Path $Python)) {
    throw "Virtual environment not found at .venv. Run setup first."
}

if (-not (Test-Path (Join-Path $Frontend "node_modules"))) {
    throw "Frontend dependencies not found. Run setup first."
}

function Test-Redis {
    try {
        $connection = Test-NetConnection -ComputerName "127.0.0.1" -Port 6379 -WarningAction SilentlyContinue
        return [bool]$connection.TcpTestSucceeded
    }
    catch {
        return $false
    }
}

function Try-Start-Redis {
    if ($NoDockerRedis) {
        return $false
    }

    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $docker) {
        return $false
    }

    Write-Host "Redis is not reachable on 127.0.0.1:6379. Trying 'docker compose up -d redis'..." -ForegroundColor Yellow
    try {
        Push-Location $Root
        docker compose up -d redis | Out-Host
    }
    catch {
        Write-Host "Could not start Redis through Docker Compose: $($_.Exception.Message)" -ForegroundColor Yellow
        return $false
    }
    finally {
        Pop-Location
    }

    for ($attempt = 1; $attempt -le 10; $attempt++) {
        if (Test-Redis) {
            return $true
        }
        Start-Sleep -Seconds 1
    }

    return $false
}

function Start-AppProcess {
    param(
        [string]$Title,
        [string]$Command,
        [string]$WorkingDirectory
    )

    $escapedTitle = $Title.Replace("'", "''")
    $escapedCommand = $Command.Replace("'", "''")
    $escapedWorkingDirectory = $WorkingDirectory.Replace("'", "''")
    $processCommand = "Set-Location '$escapedWorkingDirectory'; `$host.UI.RawUI.WindowTitle = '$escapedTitle'; $escapedCommand"

    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-Command", $processCommand
    )
}

$redisReady = Test-Redis
if (-not $redisReady) {
    $redisReady = Try-Start-Redis
}

if (-not $redisReady -and $RequireBackground) {
    throw "Redis is required for worker/scheduler but is not reachable on 127.0.0.1:6379. Start Redis or run without -RequireBackground."
}

Start-AppProcess -Title "ROM backend :8000" -WorkingDirectory $Root -Command ".\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
Start-AppProcess -Title "ROM frontend :3000" -WorkingDirectory $Frontend -Command "npm run dev"

if (-not $SkipWorker -and $redisReady) {
    Start-AppProcess -Title "ROM worker" -WorkingDirectory $Root -Command ".\.venv\Scripts\python.exe -m app.workers.worker"
}

if (-not $SkipScheduler -and $redisReady) {
    Start-AppProcess -Title "ROM scheduler" -WorkingDirectory $Root -Command ".\.venv\Scripts\python.exe -m app.workers.scheduler"
}

Write-Host "Started Research Opportunity Matcher." -ForegroundColor Green
Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "Frontend: http://127.0.0.1:3000"
if ($redisReady) {
    Write-Host "Background: worker and scheduler started with Redis on 127.0.0.1:6379"
}
else {
    Write-Host "Background: worker and scheduler skipped because Redis is not reachable on 127.0.0.1:6379" -ForegroundColor Yellow
    Write-Host "To enable them, start Redis or Docker Desktop, then rerun this script."
    Write-Host "You can force failure instead of skipping with: .\scripts\run-full-app.ps1 -RequireBackground"
}
Write-Host ""
Write-Host "Windows note: PowerShell does not include GNU Make by default."
Write-Host "Use '.\scripts\run-full-app.ps1' directly, or install Make and run 'make run-full-app'."
