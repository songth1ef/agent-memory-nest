#!/usr/bin/env bash
set -e

# ---------------------------------------------
# agent-nest x Gemini CLI uninstaller
#
# Unbinds only: removes the bootstrap block from ~/.gemini/GEMINI.md.
# Memory and identity files are never deleted.
#
# Usage:
#   bash uninstall/gemini.sh [--purge-identity]
# ---------------------------------------------

AGENT_NEST_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GEMINI_DIR="${GEMINI_HOME:-$HOME/.gemini}"

HOST="$(cat "$HOME/.agent_nest_host" 2>/dev/null || true)"
AGENT_ID="$(cat "$HOME/.agent_nest_id_gemini" 2>/dev/null || true)"

echo "-> agent-nest path : $AGENT_NEST_PATH"
echo "-> host           : ${HOST:-<unknown>}"
echo "-> agent id       : ${AGENT_ID:-<unknown>}"

python3 "$AGENT_NEST_PATH/scripts/uninstall/_unbootstrap.py" "$GEMINI_DIR/GEMINI.md"

if [ "${1:-}" = "--purge-identity" ]; then
  rm -f "$HOME/.agent_nest_id_gemini"
  echo "[ok] removed $HOME/.agent_nest_id_gemini (next install gets a new agent id)"
fi

echo ""
echo "OK agent-nest unbound from Gemini CLI"
if [ -n "$HOST" ] && [ -n "$AGENT_ID" ]; then
  echo "   memory kept : $AGENT_NEST_PATH/agents/$HOST/$AGENT_ID/"
else
  echo "   memory kept : $AGENT_NEST_PATH/agents/<host>/<agent-id>/"
fi
echo "   to rebind   : bash $AGENT_NEST_PATH/scripts/install/gemini.sh"
