# ---------------------------------------------
# agent-nest x Kimi Code uninstaller (Windows)
# ---------------------------------------------

$ErrorActionPreference = "Stop"

$AgentNestPath = (Resolve-Path "$PSScriptRoot\..\..\..").Path
$KimiCodeHome = if ($env:KIMI_CODE_HOME) { $env:KIMI_CODE_HOME } else { "$env:USERPROFILE\.kimi-code" }

# Python is required for the shared uninstaller helpers
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

$HostId = ""
$AgentId = ""
$HostFile = "$env:USERPROFILE\.agent_nest_host"
$IdFile   = "$env:USERPROFILE\.agent_nest_id_kimi"
if (Test-Path $HostFile) { $HostId = (Get-Content $HostFile -Raw).Trim() }
if (Test-Path $IdFile)   { $AgentId = (Get-Content $IdFile -Raw).Trim() }

Write-Host "-> agent-nest path : $AgentNestPath"
Write-Host "-> host           : $(if ($HostId) { $HostId } else { '<unknown>' })"
Write-Host "-> agent id       : $(if ($AgentId) { $AgentId } else { '<unknown>' })"

# 1. Remove the bootstrap block from AGENTS.md (user content preserved), plus
#    the legacy AGENT_NEST.md left by installs made before 2026-08-02.
& $PythonCmd (Join-Path $AgentNestPath "scripts\uninstall\_common\unbootstrap.py") "$KimiCodeHome\AGENTS.md"
$LegacyBootstrap = "$KimiCodeHome\AGENT_NEST.md"
if (Test-Path $LegacyBootstrap) {
    & $PythonCmd (Join-Path $AgentNestPath "scripts\uninstall\_common\unbootstrap.py") $LegacyBootstrap
}

# 2. Remove the agent-nest hook block from config.toml (user hooks preserved)
& $PythonCmd (Join-Path $AgentNestPath "scripts\uninstall\kimi\unhooks.py") "$KimiCodeHome\config.toml"

# 3. Optionally purge this tool's identity file
if ($args -contains "--purge-identity") {
    Remove-Item -Force -Path $IdFile -ErrorAction SilentlyContinue
    Write-Host "[ok] removed $IdFile (next install gets a new agent id)"
}

Write-Host ""
Write-Host "OK agent-nest unbound from Kimi Code"
if ($HostId -and $AgentId) {
    Write-Host "   memory kept : $AgentNestPath\agents\$HostId\$AgentId\"
} else {
    Write-Host "   memory kept : $AgentNestPath\agents\<host>\<agent-id>\"
}
Write-Host "   to rebind   : bash $AgentNestPath\scripts\install\kimi\install.sh"
