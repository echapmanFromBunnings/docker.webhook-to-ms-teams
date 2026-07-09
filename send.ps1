#Requires -Version 5.1
<#
.SYNOPSIS
    Send a sample GitHub event to a real Teams Power Automate workflow URL.
.DESCRIPTION
    Reads WORKFLOW_WEBHOOK_URL from the environment or a .env file, then sends
    a sample event payload. Use --dry-run to preview the payload without sending.
.EXAMPLE
    $env:WORKFLOW_WEBHOOK_URL = "https://prod-xx.westus.logic.azure.com/..."
    .\send.ps1 -Event push -Fixture push
.EXAMPLE
    .\send.ps1 -Event pull_request -Fixture pull_request -DryRun
#>
[CmdletBinding()]
param(
    [Parameter()]
    [string]$Url = $env:WORKFLOW_WEBHOOK_URL,

    [Parameter()]
    [string]$Event = "push",

    [Parameter()]
    [string]$Fixture = "push",

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$fixturePath = Join-Path $repoRoot "tests\fixtures\$Fixture.json"

# Load .env if present and Url not already supplied.
$envFile = Join-Path $repoRoot ".env"
if (-not $Url -and (Test-Path $envFile)) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#\s=]+)\s*=\s*(.*?)\s*$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
    $Url = $env:WORKFLOW_WEBHOOK_URL
}

if (-not $Url -and -not $DryRun) {
    Write-Error "WORKFLOW_WEBHOOK_URL is required. Set it in .env, as an environment variable, or pass -Url."
}

if (-not (Test-Path $fixturePath)) {
    Write-Error "Fixture not found: $fixturePath"
}

# Build argument list for the Python sender.
$argsList = @("-m", "src", "--event", $Event, "--payload", $fixturePath)
if ($Url) { $argsList += @("--url", $Url) }
if ($DryRun) { $argsList += "--dry-run" }

Write-Host "Sending event '$Event' using fixture '$Fixture'$(if ($DryRun) { " (dry run)" })..."
& python $argsList
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to send webhook."
}
