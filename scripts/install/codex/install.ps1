# ---------------------------------------------
# agent-nest x Codex installer (Windows)
# ---------------------------------------------

$ErrorActionPreference = "Stop"

$AgentNestPath = (Resolve-Path "$PSScriptRoot\..\..\..").Path
$CodexDir = "$env:USERPROFILE\.codex"
$CodexAgents = "$CodexDir\AGENTS.md"
$CodexInstructions = "$CodexDir\instructions.md"
$CodexConfig = "$CodexDir\config.toml"
$CodexHooks = "$CodexDir\hooks.json"

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
    throw "python3 (or python / py) not found -- required by agent-nest installer"
}

$IdentityLines = @(& $PythonCmd (Join-Path $AgentNestPath "scripts\install\_common\identity.py") codex)
if ($LASTEXITCODE -ne 0) { throw "identity resolver failed (exit $LASTEXITCODE)" }
if ($IdentityLines.Count -lt 2) {
    throw "identity resolver returned $($IdentityLines.Count) line(s); expected host + agent-id"
}
$NestHost = $IdentityLines[0].Trim()
$AgentId  = $IdentityLines[1].Trim()
if (-not $NestHost -or -not $AgentId) {
    throw "identity resolver returned an empty host or agent-id"
}
$AgentDir = "$AgentNestPath\agents\$NestHost\$AgentId"

Write-Host "-> agent-nest path : $AgentNestPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"

# 1. Create this agent's memory directory
New-Item -ItemType Directory -Force -Path $AgentDir | Out-Null
$MemoryFile = "$AgentDir\memory.md"
if (-not (Test-Path $MemoryFile)) {
    @"
# MEMORY -- $NestHost/$AgentId

> Private memory for this agent instance.
> Only $NestHost/$AgentId writes here.

---

_No memory yet._
"@ | Set-Content -Path $MemoryFile -Encoding UTF8
    Write-Host "v created $MemoryFile"
}

# 2. Inject agent-nest bootstrap (marker-preserved).
New-Item -ItemType Directory -Force -Path $CodexDir | Out-Null
& $PythonCmd (Join-Path $AgentNestPath "scripts\install\_common\bootstrap.py") `
    "$CodexAgents" $AgentNestPath $NestHost $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "Codex AGENTS.md bootstrap injection failed (exit $LASTEXITCODE)"
}
& $PythonCmd (Join-Path $AgentNestPath "scripts\install\_common\bootstrap.py") `
    "$CodexInstructions" $AgentNestPath $NestHost $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "Codex instructions.md compatibility bootstrap injection failed (exit $LASTEXITCODE)"
}

# 3. Register the Codex hooks: PreToolUse / PostToolUse on apply_patch and Stop
#    run scripts/hooks/agent-nest.sh for per-write memory sync (bash required;
#    on Windows that means Git Bash on PATH). Current Codex reads config.toml +
#    hooks.json; the old config.json session.end_hook entry is ignored.
$env:AGENT_NEST_CODEX_PLATFORM = "windows"
& $PythonCmd (Join-Path $AgentNestPath "scripts\install\codex\hooks.py") `
    "$CodexConfig" "$CodexHooks" $AgentNestPath $NestHost $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "Codex hook registration failed (exit $LASTEXITCODE)"
}
Remove-Item Env:\AGENT_NEST_CODEX_PLATFORM

Write-Host ""
Write-Host "OK agent-nest installed for Codex"
Write-Host "   agent: $NestHost/$AgentId"
Write-Host "   memory: $MemoryFile"
