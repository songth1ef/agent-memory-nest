# ---------------------------------------------
# agent-nest x OpenClaw uninstaller (Windows)
#
# Unbinds only: removes the bootstrap block from the workspace AGENTS.md and
# the SOUL.md symlink (only if it still points into this agent-nest checkout).
# Memory and identity files are never deleted.
#
# Usage:
#   .\uninstall\openclaw\uninstall.ps1 [-PurgeIdentity]
# ---------------------------------------------

param([switch]$PurgeIdentity)

$ErrorActionPreference = "Stop"

$AgentNestPath = (Resolve-Path "$PSScriptRoot\..\..\..").Path
$OpenClawDir   = "$env:USERPROFILE\.openclaw\workspace"

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
if (Test-Path "$env:USERPROFILE\.agent_nest_id_openclaw") {
    $AgentId = (Get-Content "$env:USERPROFILE\.agent_nest_id_openclaw" -Raw).Trim()
}

Write-Host "-> agent-nest path : $AgentNestPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"

# 1. Remove the bootstrap block from workspace AGENTS.md
& $PythonCmd (Join-Path $AgentNestPath "scripts\uninstall\_common\unbootstrap.py") `
    "$OpenClawDir\AGENTS.md"
if ($LASTEXITCODE -ne 0) { throw "AGENTS.md bootstrap removal failed (exit $LASTEXITCODE)" }

# 2. Remove the SOUL.md link left by older installs, if it was ours
$SoulPath = "$OpenClawDir\SOUL.md"
if (Test-Path $SoulPath) {
    $Item = Get-Item $SoulPath -Force
    if ($Item.LinkType -and $Item.Target -eq (Join-Path $AgentNestPath "SOUL.md")) {
        Remove-Item -Force $SoulPath
        Write-Host "v removed SOUL.md symlink"
    }
}

# 3. Optionally purge this tool's identity file
if ($PurgeIdentity) {
    Remove-Item -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.agent_nest_id_openclaw"
    Write-Host "v removed .agent_nest_id_openclaw (next install gets a new agent id)"
}

Write-Host ""
Write-Host "OK agent-nest unbound from OpenClaw"
if ($NestHost -and $AgentId) {
    Write-Host "   memory kept : $AgentNestPath\agents\$NestHost\$AgentId\"
} else {
    Write-Host "   memory kept : $AgentNestPath\agents\<host>\<agent-id>\"
}
Write-Host "   to rebind   : .\scripts\install\openclaw\install.ps1"
