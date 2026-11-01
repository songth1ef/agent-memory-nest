# ---------------------------------------------
# agent-nest x WorkBuddy AI uninstaller (Windows)
#
# Unbinds only: removes the bootstrap block from the WorkBuddy rules file.
# Memory and identity files are never deleted.
#
# Usage:
#   .\uninstall\workbuddy\uninstall.ps1 [-PurgeIdentity]
# ---------------------------------------------

param([switch]$PurgeIdentity)

$ErrorActionPreference = "Stop"

$AgentNestPath = (Resolve-Path "$PSScriptRoot\..\..\..").Path
$WorkBuddyDir  = if ($env:WORKBUDDY_HOME) { $env:WORKBUDDY_HOME } else { "$env:USERPROFILE\.workbuddy-ai" }
$TargetMd      = if ($env:WORKBUDDY_AGENT_NEST_MD) { $env:WORKBUDDY_AGENT_NEST_MD } else { "$WorkBuddyDir\agent-nest.md" }

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
if (Test-Path "$env:USERPROFILE\.agent_nest_id_workbuddy") {
    $AgentId = (Get-Content "$env:USERPROFILE\.agent_nest_id_workbuddy" -Raw).Trim()
}

Write-Host "-> agent-nest path  : $AgentNestPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"

& $PythonCmd (Join-Path $AgentNestPath "scripts\uninstall\_common\unbootstrap.py") `
    $TargetMd
if ($LASTEXITCODE -ne 0) { throw "WorkBuddy rules bootstrap removal failed (exit $LASTEXITCODE)" }

if ($PurgeIdentity) {
    Remove-Item -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.agent_nest_id_workbuddy"
    Write-Host "v removed .agent_nest_id_workbuddy (next install gets a new agent id)"
}

Write-Host ""
Write-Host "OK agent-nest unbound from WorkBuddy AI"
if ($NestHost -and $AgentId) {
    Write-Host "   memory kept : $AgentNestPath\agents\$NestHost\$AgentId\"
} else {
    Write-Host "   memory kept : $AgentNestPath\agents\<host>\<agent-id>\"
}
Write-Host "   to rebind   : .\scripts\install\workbuddy\install.ps1"
