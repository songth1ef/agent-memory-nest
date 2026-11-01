# -----------------------------------------------------------------------------
# agent-nest x generic markdown-config uninstaller (Windows)
#
# Inverse of install/generic/install.ps1: removes the agent-nest bootstrap block from the
# given config file. Memory and identity files are never deleted.
#
# Usage:
#   .\uninstall\generic\uninstall.ps1 <tool-prefix> <config-path> [-PurgeIdentity]
#
# Example:
#   .\uninstall\generic\uninstall.ps1 qwen "$env:USERPROFILE\.qwen\QWEN.md"
# -----------------------------------------------------------------------------

param(
    [Parameter(Mandatory = $true)][string]$Prefix,
    [Parameter(Mandatory = $true)][string]$ConfigPath,
    [switch]$PurgeIdentity
)

$ErrorActionPreference = "Stop"

$AgentNestPath = (Resolve-Path "$PSScriptRoot\..\..\..").Path

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
if (Test-Path "$env:USERPROFILE\.agent_nest_id_$Prefix") {
    $AgentId = (Get-Content "$env:USERPROFILE\.agent_nest_id_$Prefix" -Raw).Trim()
}

Write-Host "-> agent-nest path : $AgentNestPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"

& $PythonCmd (Join-Path $AgentNestPath "scripts\uninstall\_common\unbootstrap.py") $ConfigPath
if ($LASTEXITCODE -ne 0) { throw "bootstrap removal failed (exit $LASTEXITCODE)" }

if ($PurgeIdentity) {
    Remove-Item -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.agent_nest_id_$Prefix"
    Write-Host "v removed .agent_nest_id_$Prefix (next install gets a new agent id)"
}

Write-Host ""
Write-Host "OK agent-nest unbound from $Prefix"
if ($NestHost -and $AgentId) {
    Write-Host "   memory kept : $AgentNestPath\agents\$NestHost\$AgentId\"
} else {
    Write-Host "   memory kept : $AgentNestPath\agents\<host>\<agent-id>\"
}
Write-Host "   to rebind   : .\scripts\install\generic\install.ps1 $Prefix $ConfigPath"
