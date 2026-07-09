#Requires -Version 5.1
<#
.SYNOPSIS
    Run the webhook-to-Teams test suite and local harness on Windows.
.DESCRIPTION
    Creates a Python virtual environment, installs dependencies, runs pytest,
    and then sends a sample push event through the local mock server.
.EXAMPLE
    .\test.ps1
.EXAMPLE
    .\test.ps1 -Event workflow_run -Fixture workflow_run
#>
[CmdletBinding()]
param(
    [string]$Event = "push",
    [string]$Fixture = "push"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venvPath = Join-Path $repoRoot ".venv"

function Test-Command($cmd) {
    return [bool](Get-Command $cmd -ErrorAction SilentlyContinue)
}

if (-not (Test-Command "python")) {
    Write-Error "Python is not installed or not on PATH. Install Python 3.8+ and try again."
}

$pythonVersion = & python --version 2>&1
Write-Host "Found $pythonVersion"

# Create virtual environment if missing.
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment at $venvPath ..."
    & python -m venv $venvPath
}

# Activate the virtual environment.
$activate = Join-Path $venvPath "Scripts\Activate.ps1"
& $activate

# Install / upgrade dependencies.
Write-Host "Installing dependencies ..."
& python -m pip install --upgrade pip -q
& python -m pip install -r (Join-Path $repoRoot "requirements-dev.txt") -q

# Run pytest.
Write-Host "`nRunning pytest ..."
& python -m pytest -v
if ($LASTEXITCODE -ne 0) {
    Write-Error "Tests failed."
}

# Run local harness.
Write-Host "`nRunning local harness for event '$Event' with fixture '$Fixture' ..."
& python -m tests.local_send --event $Event --fixture $Fixture
if ($LASTEXITCODE -ne 0) {
    Write-Error "Local harness failed."
}

Write-Host "`nAll checks passed."
