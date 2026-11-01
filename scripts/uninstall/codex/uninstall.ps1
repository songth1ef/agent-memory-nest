# ---------------------------------------------
# agent-nest x Codex uninstaller (Windows)
#
# Unbinds only: removes the bootstrap block from AGENTS.md / instructions.md
# and the agent-nest hooks (PreToolUse / PostToolUse / Stop / SessionEnd) from
# hooks.json. `hooksPath` in config.toml is
# left alone. Memory and identity files are never deleted.
#
# Usage:
#   .\uninstall\codex\uninstall.ps1 [-PurgeIdentity]
# ---------------------------------------------

param([switch]$PurgeIdentity)

$ErrorActionPreference = "Stop"

$AgentNestPath = (Resolve-Path "$PSScriptRoot\..\..\..").Path
$CodexDir      = "$env:USERPROFILE\.codex"

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
if (Test-Path "$env:USERPROFILE\.agent_nest_id_codex") {
    $AgentId = (Get-Content "$env:USERPROFILE\.agent_nest_id_codex" -Raw).Trim()
}

Write-Host "-> agent-nest path : $AgentNestPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"

# 1. Remove the bootstrap block from Codex startup files (user content preserved)
& $PythonCmd (Join-Path $AgentNestPath "scripts\uninstall\_common\unbootstrap.py") `
    "$CodexDir\AGENTS.md"
if ($LASTEXITCODE -ne 0) { throw "AGENTS.md bootstrap removal failed (exit $LASTEXITCODE)" }
& $PythonCmd (Join-Path $AgentNestPath "scripts\uninstall\_common\unbootstrap.py") `
    "$CodexDir\instructions.md"
if ($LASTEXITCODE -ne 0) { throw "instructions.md bootstrap removal failed (exit $LASTEXITCODE)" }

# 2. Remove the agent-nest hooks from hooks.json (user hooks preserved)
& $PythonCmd (Join-Path $AgentNestPath "scripts\uninstall\codex\unhooks.py") `
    "$CodexDir\hooks.json"
if ($LASTEXITCODE -ne 0) { throw "Codex hook removal failed (exit $LASTEXITCODE)" }

# 3. Optionally purge this tool's identity file
if ($PurgeIdentity) {
    Remove-Item -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.agent_nest_id_codex"
    Write-Host "v removed .agent_nest_id_codex (next install gets a new agent id)"
}

Write-Host ""
Write-Host "OK agent-nest unbound from Codex"
if ($NestHost -and $AgentId) {
    Write-Host "   memory kept : $AgentNestPath\agents\$NestHost\$AgentId\"
} else {
    Write-Host "   memory kept : $AgentNestPath\agents\<host>\<agent-id>\"
}
Write-Host "   to rebind   : .\scripts\install\codex\install.ps1"
