#!/usr/bin/env bash
set -e

# ---------------------------------------------
# agent-nest x Codex uninstaller
#
# Unbinds only: removes the bootstrap block from ~/.codex/AGENTS.md and
# instructions.md, and the agent-nest hooks (PreToolUse / PostToolUse / Stop /
# SessionEnd) from hooks.json. `hooksPath`
# in config.toml is left alone (generic pointer; hooks.json may still hold
# user hooks). Memory and identity files are never deleted.
#
# Usage:
#   bash uninstall/codex.sh [--purge-identity]
# ---------------------------------------------

AGENT_NEST_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CODEX_DIR="$HOME/.codex"

HOST="$(cat "$HOME/.agent_nest_host" 2>/dev/null || true)"
AGENT_ID="$(cat "$HOME/.agent_nest_id_codex" 2>/dev/null || true)"

echo "-> agent-nest path : $AGENT_NEST_PATH"
echo "-> host           : ${HOST:-<unknown>}"
echo "-> agent id       : ${AGENT_ID:-<unknown>}"

# 1. Remove the bootstrap block from Codex startup files (user content preserved)
python3 "$AGENT_NEST_PATH/scripts/uninstall/_unbootstrap.py" "$CODEX_DIR/AGENTS.md"
python3 "$AGENT_NEST_PATH/scripts/uninstall/_unbootstrap.py" "$CODEX_DIR/instructions.md"

# 2. Remove the agent-nest hooks from hooks.json (user hooks preserved)
python3 "$AGENT_NEST_PATH/scripts/uninstall/_codex_unhooks.py" "$CODEX_DIR/hooks.json"

# 3. Optionally purge this tool's identity file
if [ "${1:-}" = "--purge-identity" ]; then
  rm -f "$HOME/.agent_nest_id_codex"
  echo "[ok] removed $HOME/.agent_nest_id_codex (next install gets a new agent id)"
fi

echo ""
echo "OK agent-nest unbound from Codex"
if [ -n "$HOST" ] && [ -n "$AGENT_ID" ]; then
  echo "   memory kept : $AGENT_NEST_PATH/agents/$HOST/$AGENT_ID/"
else
  echo "   memory kept : $AGENT_NEST_PATH/agents/<host>/<agent-id>/"
fi
echo "   to rebind   : bash $AGENT_NEST_PATH/scripts/install/codex.sh"
