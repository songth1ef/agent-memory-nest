# ---------------------------------------------
# agent-nest x Claude Code installer (Windows)
# ---------------------------------------------

$ErrorActionPreference = "Stop"

$AgentNestPath = (Resolve-Path "$PSScriptRoot\..\..\..").Path
$ClaudeDir     = "$env:USERPROFILE\.claude"
$Settings      = "$ClaudeDir\settings.json"

# Python is required for the shared installer helpers
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

# Resolve (host, agent-id) via shared identity helper. Claude uses a random
# suffix so multiple installs on one machine stay distinct.
$IdentityLines = @(& $PythonCmd (Join-Path $AgentNestPath "scripts\install\_common\identity.py") claude --with-suffix)
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

# 2. Inject agent-nest bootstrap into global CLAUDE.md (preserves user content).
New-Item -ItemType Directory -Force -Path $ClaudeDir | Out-Null
& $PythonCmd (Join-Path $AgentNestPath "scripts\install\_common\bootstrap.py") `
    "$ClaudeDir\CLAUDE.md" $AgentNestPath $NestHost $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "CLAUDE.md bootstrap injection failed (exit $LASTEXITCODE)"
}

# 3. Register SessionStart/Pre/Post/Stop hooks via shared Python helper
#    (avoids PowerShell's ConvertTo-Json bug on nested single-element arrays).
if (-not (Test-Path $Settings)) {
    '{}' | Set-Content -Path $Settings -Encoding UTF8
}
& $PythonCmd (Join-Path $AgentNestPath "scripts\install\claude\hooks.py") `
    $Settings $AgentNestPath $NestHost $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "hook installation failed (exit $LASTEXITCODE)"
}

Write-Host ""
Write-Host "OK agent-nest installed for Claude Code"
Write-Host "   agent : $NestHost/$AgentId"
Write-Host "   memory: $MemoryFile"
