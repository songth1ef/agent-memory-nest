#!/usr/bin/env bash
set -e

# ---------------------------------------------
# agent-nest x Antigravity uninstaller
#
# Unbinds only: removes the bootstrap block from ~/.gemini/GEMINI.md and
# deregisters agent-nest hooks from ~/.gemini/config/hooks.json.
# Memory and identity files are never deleted.
#
# Usage:
#   bash uninstall/antigravity.sh [--purge-identity]
# ---------------------------------------------

AGENT_NEST_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GEMINI_DIR="${GEMINI_HOME:-$HOME/.gemini}"
[ -n "${ANTIGRAVITY_HOME:-}" ] && GEMINI_DIR="$ANTIGRAVITY_HOME"
GEMINI_MD="$GEMINI_DIR/GEMINI.md"
HOOKS_JSON="$GEMINI_DIR/config/hooks.json"

HOST="$(cat "$HOME/.agent_nest_host" 2>/dev/null || true)"
AGENT_ID="$(cat "$HOME/.agent_nest_id_antigravity" 2>/dev/null || true)"

echo "-> agent-nest path : $AGENT_NEST_PATH"
echo "-> host           : ${HOST:-<unknown>}"
echo "-> agent id       : ${AGENT_ID:-<unknown>}"

python3 "$AGENT_NEST_PATH/scripts/uninstall/_unbootstrap.py" "$GEMINI_MD"
python3 "$AGENT_NEST_PATH/scripts/uninstall/_antigravity_unhooks.py" "$HOOKS_JSON"

if [ "${1:-}" = "--purge-identity" ]; then
  rm -f "$HOME/.agent_nest_id_antigravity"
  echo "[ok] removed $HOME/.agent_nest_id_antigravity (next install gets a new agent id)"
fi

echo ""
echo "OK agent-nest unbound from Antigravity"
if [ -n "$HOST" ] && [ -n "$AGENT_ID" ]; then
  echo "   memory kept : $AGENT_NEST_PATH/agents/$HOST/$AGENT_ID/"
else
  echo "   memory kept : $AGENT_NEST_PATH/agents/<host>/<agent-id>/"
fi
echo "   to rebind   : bash $AGENT_NEST_PATH/scripts/install/antigravity.sh"
