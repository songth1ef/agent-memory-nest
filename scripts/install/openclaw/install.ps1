# ---------------------------------------------
# agent-nest x OpenClaw installer (Windows)
# ---------------------------------------------

$ErrorActionPreference = "Stop"

$AgentNestPath = (Resolve-Path "$PSScriptRoot\..\..\..").Path
$OpenclawDir   = "$env:USERPROFILE\.openclaw\workspace"

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

$IdentityLines = @(& $PythonCmd (Join-Path $AgentNestPath "scripts\install\_common\identity.py") openclaw)
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
Write-Host "-> openclaw ws    : $OpenclawDir"

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

# 2. Create OpenClaw workspace directory
New-Item -ItemType Directory -Force -Path $OpenclawDir | Out-Null

# 3. Inject agent-nest bootstrap into AGENTS.md (marker-preserved).
& $PythonCmd (Join-Path $AgentNestPath "scripts\install\_common\bootstrap.py") `
    "$OpenclawDir\AGENTS.md" $AgentNestPath $NestHost $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "OpenClaw AGENTS.md bootstrap injection failed (exit $LASTEXITCODE)"
}

Write-Host ""
Write-Host "OK agent-nest installed for OpenClaw"
Write-Host "   agent  : $NestHost/$AgentId"
Write-Host "   memory : $MemoryFile"
Write-Host "   ws     : $OpenclawDir"
