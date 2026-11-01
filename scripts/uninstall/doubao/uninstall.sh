#!/usr/bin/env bash
set -e

# ---------------------------------------------
# agent-nest x Doubao Work uninstaller
#
# Unbinds only: removes the bootstrap block from the Doubao rules file.
# Memory and identity files are never deleted.
#
# Usage:
#   bash uninstall/doubao/uninstall.sh [--purge-identity]
# ---------------------------------------------

AGENT_NEST_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DOUBAO_DIR="${DOUBAO_HOME:-$HOME/.doubao}"
TARGET_MD="${DOUBAO_AGENT_NEST_MD:-$DOUBAO_DIR/agent-nest.md}"

HOST="$(cat "$HOME/.agent_nest_host" 2>/dev/null || true)"
AGENT_ID="$(cat "$HOME/.agent_nest_id_doubao" 2>/dev/null || true)"

echo "-> agent-nest path : $AGENT_NEST_PATH"
echo "-> host           : ${HOST:-<unknown>}"
echo "-> agent id       : ${AGENT_ID:-<unknown>}"

python3 "$AGENT_NEST_PATH/scripts/uninstall/_common/unbootstrap.py" "$TARGET_MD"

if [ "${1:-}" = "--purge-identity" ]; then
  rm -f "$HOME/.agent_nest_id_doubao"
  echo "[ok] removed $HOME/.agent_nest_id_doubao (next install gets a new agent id)"
fi

echo ""
echo "OK agent-nest unbound from Doubao Work"
if [ -n "$HOST" ] && [ -n "$AGENT_ID" ]; then
  echo "   memory kept : $AGENT_NEST_PATH/agents/$HOST/$AGENT_ID/"
else
  echo "   memory kept : $AGENT_NEST_PATH/agents/<host>/<agent-id>/"
fi
echo "   to rebind   : bash $AGENT_NEST_PATH/scripts/install/doubao/install.sh"
