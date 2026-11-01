# ---------------------------------------------
# agent-nest x Hermes Agent uninstaller (Windows)
#
# Unbinds only: removes the bootstrap block from SOUL.md; the SOUL prose and
# anything outside the markers is preserved. Memory and identity files are
# never deleted.
#
# Usage:
#   .\uninstall\hermes\uninstall.ps1 [-PurgeIdentity]
# ---------------------------------------------

param([switch]$PurgeIdentity)

$ErrorActionPreference = "Stop"

$AgentNestPath = (Resolve-Path "$PSScriptRoot\..\..\..").Path
# Hermes on Windows keeps its home in %LOCALAPPDATA%\hermes; ~/.hermes is the
# POSIX layout. Prefer an explicit HERMES_HOME, then the Windows home if present.
$HermesDir     = if ($env:HERMES_HOME) { $env:HERMES_HOME }
                 elseif (Test-Path "$env:LOCALAPPDATA\hermes") { "$env:LOCALAPPDATA\hermes" }
                 else { "$env:USERPROFILE\.hermes" }

$PythonCmd = $null
foreach ($Cand in @("python3", "python", "py")) {
    # The WindowsApps "python3"/"python" stubs exist as commands but only open the
    # Store (exit 9009), so a candidate counts only if it actually runs.
    if (Get-Command $Cand -ErrorAction SilentlyContinue) {
        & $Cand -c "import sys" 2>$null
        if ($LASTEXITCODE -eq 0) { $PythonCmd = $Cand; break }
    }
}
if (-not $PythonCmd) {
    throw "python3 (or python / py) not found -- required by agent-nest uninstaller"
}

$NestHost = ""
$AgentId  = ""
if (Test-Path "$env:USERPROFILE\.agent_nest_host") {
    $NestHost = (Get-Content "$env:USERPROFILE\.agent_nest_host" -Raw).Trim()
}
if (Test-Path "$env:USERPROFILE\.agent_nest_id_hermes") {
    $AgentId = (Get-Content "$env:USERPROFILE\.agent_nest_id_hermes" -Raw).Trim()
}

Write-Host "-> agent-nest path : $AgentNestPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"

& $PythonCmd (Join-Path $AgentNestPath "scripts\uninstall\_common\unbootstrap.py") `
    "$HermesDir\SOUL.md"
if ($LASTEXITCODE -ne 0) { throw "SOUL.md bootstrap removal failed (exit $LASTEXITCODE)" }

if ($PurgeIdentity) {
    Remove-Item -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.agent_nest_id_hermes"
    Write-Host "v removed .agent_nest_id_hermes (next install gets a new agent id)"
}

Write-Host ""
Write-Host "OK agent-nest unbound from Hermes Agent"
if ($NestHost -and $AgentId) {
    Write-Host "   memory kept : $AgentNestPath\agents\$NestHost\$AgentId\"
} else {
    Write-Host "   memory kept : $AgentNestPath\agents\<host>\<agent-id>\"
}
Write-Host "   to rebind   : .\scripts\install\hermes\install.ps1"
