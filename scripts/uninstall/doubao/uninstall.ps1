# ---------------------------------------------
# agent-nest x Doubao Work uninstaller (Windows)
#
# Unbinds only: removes the bootstrap block from the Doubao rules file.
# Memory and identity files are never deleted.
#
# Usage:
#   .\uninstall\doubao\uninstall.ps1 [-PurgeIdentity]
# ---------------------------------------------

param([switch]$PurgeIdentity)

$ErrorActionPreference = "Stop"

$AgentNestPath = (Resolve-Path "$PSScriptRoot\..\..\..").Path
$DoubaoDir     = if ($env:DOUBAO_HOME) { $env:DOUBAO_HOME } else { "$env:USERPROFILE\.doubao" }
$TargetMd      = if ($env:DOUBAO_AGENT_NEST_MD) { $env:DOUBAO_AGENT_NEST_MD } else { "$DoubaoDir\agent-nest.md" }

$PythonCmd = $null
foreach ($Cand in @("python3", "python", "py")) {
    if (Get-Command $Cand -ErrorAction SilentlyContinue) { $PythonCmd = $Cand; break }
}
if (-not $PythonCmd) {
    throw "python3 (or python / py) not found -- required by agent-nest uninstaller"
}

$NestHost = ""
$AgentId  = ""
if (Test-Path "$env:USERPROFILE\.agent_nest_host") {
    $NestHost = (Get-Content "$env:USERPROFILE\.agent_nest_host" -Raw).Trim()
}
if (Test-Path "$env:USERPROFILE\.agent_nest_id_doubao") {
    $AgentId = (Get-Content "$env:USERPROFILE\.agent_nest_id_doubao" -Raw).Trim()
}

Write-Host "-> agent-nest path : $AgentNestPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"

& $PythonCmd (Join-Path $AgentNestPath "scripts\uninstall\_common\unbootstrap.py") `
    $TargetMd
if ($LASTEXITCODE -ne 0) { throw "Doubao rules bootstrap removal failed (exit $LASTEXITCODE)" }

if ($PurgeIdentity) {
    Remove-Item -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.agent_nest_id_doubao"
    Write-Host "v removed .agent_nest_id_doubao (next install gets a new agent id)"
}

Write-Host ""
Write-Host "OK agent-nest unbound from Doubao Work"
if ($NestHost -and $AgentId) {
    Write-Host "   memory kept : $AgentNestPath\agents\$NestHost\$AgentId\"
} else {
    Write-Host "   memory kept : $AgentNestPath\agents\<host>\<agent-id>\"
}
Write-Host "   to rebind   : .\scripts\install\doubao\install.ps1"
