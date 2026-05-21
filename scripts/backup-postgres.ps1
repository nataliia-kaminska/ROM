param(
    [string]$OutputDir = "backups",
    [string]$DatabaseUrl = $env:DATABASE_URL,
    [string]$DockerService = "postgres"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = Join-Path $OutputDir "research-matcher-$timestamp.dump"

function Test-Command($Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

if ($DatabaseUrl -and (Test-Command "pg_dump")) {
    Write-Host "Creating PostgreSQL backup with local pg_dump..."
    pg_dump --format=custom --no-owner --no-acl --file $backupPath $DatabaseUrl
    Write-Host "Backup created: $backupPath"
    exit 0
}

if (Test-Command "docker") {
    Write-Host "Creating PostgreSQL backup through docker compose service '$DockerService'..."
    $containerBackupPath = "/tmp/research-matcher-$timestamp.dump"
    docker compose exec -T $DockerService pg_dump -U research -d research_matcher --format=custom --no-owner --no-acl --file $containerBackupPath
    docker compose cp "${DockerService}:$containerBackupPath" $backupPath
    docker compose exec -T $DockerService rm $containerBackupPath
    Write-Host "Backup created: $backupPath"
    exit 0
}

throw "Cannot create backup. Install PostgreSQL client tools or run Docker Compose PostgreSQL."
