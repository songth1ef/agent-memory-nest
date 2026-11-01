#!/usr/bin/env bash
set -e

# -----------------------------------------------------------------------------
# agent-nest x generic markdown-config uninstaller
#
# Inverse of install/generic.sh: removes the agent-nest bootstrap block from the
# given config file. Memory and identity files are never deleted.
#
# Usage:
#   bash uninstall/generic.sh <tool-prefix> <config-path> [--purge-identity]
#
# Examples:
#   bash uninstall/generic.sh qwen ~/.qwen/QWEN.md
#   bash uninstall/generic.sh opencode ~/.config/opencode/prompt.md
# -----------------------------------------------------------------------------

AGENT_NEST_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PREFIX="${1:-}"
CONFIG_PATH="${2:-}"

if [ -z "$PREFIX" ] || [ -z "$CONFIG_PATH" ]; then
  cat >&2 <<USAGE
usage: bash uninstall/generic.sh <tool-prefix> <config-path> [--purge-identity]

example:
  bash uninstall/generic.sh qwen ~/.qwen/QWEN.md
USAGE
  exit 2
fi

HOST="$(cat "$HOME/.agent_nest_host" 2>/dev/null || true)"
AGENT_ID="$(cat "$HOME/.agent_nest_id_$PREFIX" 2>/dev/null || true)"

echo "-> agent-nest path : $AGENT_NEST_PATH"
echo "-> host           : ${HOST:-<unknown>}"
echo "-> agent id       : ${AGENT_ID:-<unknown>}"

python3 "$AGENT_NEST_PATH/scripts/uninstall/_unbootstrap.py" "$CONFIG_PATH"

if [ "${3:-}" = "--purge-identity" ]; then
  rm -f "$HOME/.agent_nest_id_$PREFIX"
  echo "[ok] removed $HOME/.agent_nest_id_$PREFIX (next install gets a new agent id)"
fi

echo ""
echo "OK agent-nest unbound from $PREFIX"
if [ -n "$HOST" ] && [ -n "$AGENT_ID" ]; then
  echo "   memory kept : $AGENT_NEST_PATH/agents/$HOST/$AGENT_ID/"
else
  echo "   memory kept : $AGENT_NEST_PATH/agents/<host>/<agent-id>/"
fi
echo "   to rebind   : bash $AGENT_NEST_PATH/scripts/install/generic.sh $PREFIX $CONFIG_PATH"
