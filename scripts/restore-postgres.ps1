param(
    [Parameter(Mandatory = $true)]
    [string]$BackupPath,
    [string]$DatabaseUrl = $env:DATABASE_URL,
    [string]$DockerService = "postgres"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $BackupPath)) {
    throw "Backup file not found: $BackupPath"
}

function Test-Command($Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

if ($DatabaseUrl -and (Test-Command "pg_restore")) {
    Write-Host "Restoring PostgreSQL backup with local pg_restore..."
    pg_restore --clean --if-exists --no-owner --no-acl --dbname $DatabaseUrl $BackupPath
    Write-Host "Restore complete."
    exit 0
}

if (Test-Command "docker") {
    Write-Host "Restoring PostgreSQL backup through docker compose service '$DockerService'..."
    $fileName = Split-Path $BackupPath -Leaf
    $containerBackupPath = "/tmp/$fileName"
    docker compose cp $BackupPath "${DockerService}:$containerBackupPath"
    docker compose exec -T $DockerService pg_restore -U research -d research_matcher --clean --if-exists --no-owner --no-acl $containerBackupPath
    docker compose exec -T $DockerService rm $containerBackupPath
    Write-Host "Restore complete."
    exit 0
}

throw "Cannot restore backup. Install PostgreSQL client tools or run Docker Compose PostgreSQL."
