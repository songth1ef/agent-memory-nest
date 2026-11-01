#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------
# agent-nest x WorkBuddy AI uninstaller
#
# Unbinds only: removes the bootstrap block from the WorkBuddy rules file.
# Memory and identity files are never deleted.
#
# Usage:
#   bash uninstall/workbuddy/uninstall.sh [--purge-identity]
# ---------------------------------------------

AGENT_NEST_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
WORKBUDDY_DIR="${WORKBUDDY_HOME:-$HOME/.workbuddy-ai}"
TARGET_MD="${WORKBUDDY_AGENT_NEST_MD:-$WORKBUDDY_DIR/agent-nest.md}"

HOST="$(cat "$HOME/.agent_nest_host" 2>/dev/null || true)"
AGENT_ID="$(cat "$HOME/.agent_nest_id_workbuddy" 2>/dev/null || true)"

echo "-> agent-nest path  : $AGENT_NEST_PATH"
echo "-> host           : ${HOST:-<unknown>}"
echo "-> agent id       : ${AGENT_ID:-<unknown>}"

python3 "$AGENT_NEST_PATH/scripts/uninstall/_common/unbootstrap.py" "$TARGET_MD"

if [ "${1:-}" = "--purge-identity" ]; then
  rm -f "$HOME/.agent_nest_id_workbuddy"
  echo "[ok] removed $HOME/.agent_nest_id_workbuddy (next install gets a new agent id)"
fi

echo ""
echo "OK agent-nest unbound from WorkBuddy AI"
if [ -n "$HOST" ] && [ -n "$AGENT_ID" ]; then
  echo "   memory kept : $AGENT_NEST_PATH/agents/$HOST/$AGENT_ID/"
else
  echo "   memory kept : $AGENT_NEST_PATH/agents/<host>/<agent-id>/"
fi
echo "   to rebind   : bash $AGENT_NEST_PATH/scripts/install/workbuddy/install.sh"
