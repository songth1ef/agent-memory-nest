#!/usr/bin/env bash
set -e

# ---------------------------------------------
# agent-nest x Hermes Agent uninstaller
#
# Unbinds only: removes the bootstrap block from ~/.hermes/SOUL.md. The SOUL
# prose seeded at install (and anything the user added outside the markers)
# is preserved. Memory and identity files are never deleted.
#
# Usage:
#   bash uninstall/hermes.sh [--purge-identity]
# ---------------------------------------------

AGENT_NEST_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HERMES_DIR="${HERMES_HOME:-$HOME/.hermes}"

HOST="$(cat "$HOME/.agent_nest_host" 2>/dev/null || true)"
AGENT_ID="$(cat "$HOME/.agent_nest_id_hermes" 2>/dev/null || true)"

echo "-> agent-nest path : $AGENT_NEST_PATH"
echo "-> host           : ${HOST:-<unknown>}"
echo "-> agent id       : ${AGENT_ID:-<unknown>}"

python3 "$AGENT_NEST_PATH/scripts/uninstall/_unbootstrap.py" "$HERMES_DIR/SOUL.md"

if [ "${1:-}" = "--purge-identity" ]; then
  rm -f "$HOME/.agent_nest_id_hermes"
  echo "[ok] removed $HOME/.agent_nest_id_hermes (next install gets a new agent id)"
fi

echo ""
echo "OK agent-nest unbound from Hermes Agent"
if [ -n "$HOST" ] && [ -n "$AGENT_ID" ]; then
  echo "   memory kept : $AGENT_NEST_PATH/agents/$HOST/$AGENT_ID/"
else
  echo "   memory kept : $AGENT_NEST_PATH/agents/<host>/<agent-id>/"
fi
echo "   to rebind   : bash $AGENT_NEST_PATH/scripts/install/hermes.sh"
