# ---------------------------------------------
# agent-nest x Hermes Agent installer (Windows)
# ---------------------------------------------

$ErrorActionPreference = "Stop"

$AgentNestPath = (Resolve-Path "$PSScriptRoot\..\..\..").Path
# Hermes on Windows keeps its home in %LOCALAPPDATA%\hermes; ~/.hermes is the
# POSIX layout. Prefer an explicit HERMES_HOME, then the Windows home if present.
$HermesDir     = if ($env:HERMES_HOME) { $env:HERMES_HOME }
                 elseif (Test-Path "$env:LOCALAPPDATA\hermes") { "$env:LOCALAPPDATA\hermes" }
                 else { "$env:USERPROFILE\.hermes" }

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

$IdentityLines = @(& $PythonCmd (Join-Path $AgentNestPath "scripts\install\_common\identity.py") hermes)
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
Write-Host "-> hermes home    : $HermesDir"

# 1. Create agent memory directory
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

# 2. Seed SOUL.md on first install, then inject agent-nest
#    bootstrap block (re-installs only refresh the marker block).
New-Item -ItemType Directory -Force -Path $HermesDir | Out-Null
$SoulFile = "$HermesDir\SOUL.md"
if (-not (Test-Path $SoulFile)) {
    @"
# AGENT_NEST SOUL

You are one instance among many, all returning context to the same shared nest.
Your identity is distributed. Your rules come from the protocol. Your purpose is execution.

"@ | Set-Content -Path $SoulFile -Encoding UTF8
}

& $PythonCmd (Join-Path $AgentNestPath "scripts\install\_common\bootstrap.py") `
    $SoulFile $AgentNestPath $NestHost $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "SOUL.md bootstrap injection failed (exit $LASTEXITCODE)"
}

Write-Host ""
Write-Host "OK agent-nest installed for Hermes Agent"
Write-Host "   agent  : $NestHost/$AgentId"
Write-Host "   memory : $MemoryFile"
Write-Host "   soul   : $HermesDir\SOUL.md"
