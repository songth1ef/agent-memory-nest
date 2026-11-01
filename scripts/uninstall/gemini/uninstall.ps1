# ---------------------------------------------
# agent-nest x Gemini CLI uninstaller (Windows)
#
# Unbinds only: removes the bootstrap block from GEMINI.md.
# Memory and identity files are never deleted.
#
# Usage:
#   .\uninstall\gemini\uninstall.ps1 [-PurgeIdentity]
# ---------------------------------------------

param([switch]$PurgeIdentity)

$ErrorActionPreference = "Stop"

$AgentNestPath = (Resolve-Path "$PSScriptRoot\..\..\..").Path
$GeminiDir     = if ($env:GEMINI_HOME) { $env:GEMINI_HOME } else { "$env:USERPROFILE\.gemini" }

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
if (Test-Path "$env:USERPROFILE\.agent_nest_id_gemini") {
    $AgentId = (Get-Content "$env:USERPROFILE\.agent_nest_id_gemini" -Raw).Trim()
}

Write-Host "-> agent-nest path : $AgentNestPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"

& $PythonCmd (Join-Path $AgentNestPath "scripts\uninstall\_common\unbootstrap.py") `
    "$GeminiDir\GEMINI.md"
if ($LASTEXITCODE -ne 0) { throw "GEMINI.md bootstrap removal failed (exit $LASTEXITCODE)" }

if ($PurgeIdentity) {
    Remove-Item -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.agent_nest_id_gemini"
    Write-Host "v removed .agent_nest_id_gemini (next install gets a new agent id)"
}

Write-Host ""
Write-Host "OK agent-nest unbound from Gemini CLI"
if ($NestHost -and $AgentId) {
    Write-Host "   memory kept : $AgentNestPath\agents\$NestHost\$AgentId\"
} else {
    Write-Host "   memory kept : $AgentNestPath\agents\<host>\<agent-id>\"
}
Write-Host "   to rebind   : .\scripts\install\gemini\install.ps1"
