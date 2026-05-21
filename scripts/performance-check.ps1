param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8000",
    [string]$FrontendDir = "frontend",
    [string]$Token = $env:ROM_ACCESS_TOKEN,
    [int]$ProfileId = $env:ROM_PROFILE_ID,
    [int]$ThresholdMs = 3000,
    [switch]$RunFrontendBuild
)

$ErrorActionPreference = "Stop"

function Measure-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [hashtable]$Headers = @{}
    )

    $watch = [System.Diagnostics.Stopwatch]::StartNew()
    $status = "OK"
    try {
        Invoke-WebRequest -Uri $Url -Headers $Headers -UseBasicParsing | Out-Null
    } catch {
        $status = "FAILED: $($_.Exception.Message)"
    }
    $watch.Stop()
    $duration = [math]::Round($watch.Elapsed.TotalMilliseconds, 2)
    $meetsThreshold = $duration -le $ThresholdMs -and $status -eq "OK"
    [PSCustomObject]@{
        Check = $Name
        DurationMs = $duration
        ThresholdMs = $ThresholdMs
        Passed = $meetsThreshold
        Status = $status
    }
}

$headers = @{}
if ($Token) {
    $headers["Authorization"] = "Bearer $Token"
}

$results = @()
$results += Measure-Endpoint -Name "GET /opportunities" -Url "$ApiBaseUrl/opportunities?active_only=true&limit=18&offset=0"

if ($Token) {
    $results += Measure-Endpoint -Name "GET /profiles/me" -Url "$ApiBaseUrl/profiles/me" -Headers $headers
}

if ($Token -and $ProfileId) {
    $results += Measure-Endpoint -Name "GET /recommendations/{profile_id}" -Url "$ApiBaseUrl/recommendations/$ProfileId?limit=18&offset=0&include_total=true" -Headers $headers
}

if ($RunFrontendBuild) {
    $watch = [System.Diagnostics.Stopwatch]::StartNew()
    Push-Location $FrontendDir
    try {
        npm run build | Out-Host
        $status = "OK"
    } catch {
        $status = "FAILED: $($_.Exception.Message)"
    } finally {
        Pop-Location
    }
    $watch.Stop()
    $results += [PSCustomObject]@{
        Check = "npm run build"
        DurationMs = [math]::Round($watch.Elapsed.TotalMilliseconds, 2)
        ThresholdMs = $null
        Passed = $status -eq "OK"
        Status = $status
    }
}

$results | Format-Table -AutoSize

if ($results.Passed -contains $false) {
    exit 1
}
