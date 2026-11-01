# ---------------------------------------------
# agent-nest x Antigravity uninstaller (Windows)
#
# Usage:
#   .\agent-nest\scripts\uninstall\antigravity\uninstall.ps1 [-PurgeIdentity]
# ---------------------------------------------

param(
    [switch]$PurgeIdentity
)

$ErrorActionPreference = "Stop"

$AgentNestPath = (Resolve-Path "$PSScriptRoot\..\..\..").Path
$GeminiDir     = if ($env:ANTIGRAVITY_HOME) { $env:ANTIGRAVITY_HOME } elseif ($env:GEMINI_HOME) { $env:GEMINI_HOME } else { "$env:USERPROFILE\.gemini" }
$GeminiMd      = "$GeminiDir\GEMINI.md"
$HooksJson     = "$GeminiDir\config\hooks.json"

$HostFile = "$env:USERPROFILE\.agent_nest_host"
$IdFile   = "$env:USERPROFILE\.agent_nest_id_antigravity"

$NestHost = if (Test-Path $HostFile) { (Get-Content $HostFile -Raw).Trim() } else { "<unknown>" }
$AgentId  = if (Test-Path $IdFile)   { (Get-Content $IdFile -Raw).Trim() }   else { "<unknown>" }

Write-Host "-> agent-nest path : $AgentNestPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"

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

# 1. Remove bootstrap block from GEMINI.md
& $PythonCmd (Join-Path $AgentNestPath "scripts\uninstall\_common\unbootstrap.py") $GeminiMd
if ($LASTEXITCODE -ne 0) {
    throw "unbootstrap failed (exit $LASTEXITCODE)"
}

# 2. Remove hooks from hooks.json
& $PythonCmd (Join-Path $AgentNestPath "scripts\uninstall\antigravity\unhooks.py") $HooksJson
if ($LASTEXITCODE -ne 0) {
    throw "unhooks failed (exit $LASTEXITCODE)"
}

# 3. Optionally purge identity
if ($PurgeIdentity) {
    if (Test-Path $IdFile) {
        Remove-Item -Force $IdFile
        Write-Host "v removed $IdFile (next install gets a new agent id)"
    }
}

Write-Host ""
Write-Host "OK agent-nest unbound from Antigravity"
Write-Host "   memory kept : $AgentNestPath\agents\$NestHost\$AgentId\"
Write-Host "   to rebind   : .\agent-nest\scripts\install\antigravity\install.ps1"
