#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# agent-nest unified hook entry
#
# Usage (registered by the Claude Code, Kimi Code and Codex CLI installers):
#   hook-agent-nest.sh pre  <host> <agent-id>   -- PreToolUse
#   hook-agent-nest.sh post <host> <agent-id>   -- PostToolUse
#   hook-agent-nest.sh stop <host> <agent-id>   -- Stop safety-net + layout check
#
# Payload parsing (Claude/Kimi tool_input.file_path, Codex apply_patch patch
# text) lives in _match-file.py.
#
# Design: atomic per-write sync.
# - pre:  pull --rebase before memory write; abort write on conflict
# - post: commit + push with retry; surface rebase conflict to Claude
# - stop: same as post (safety net for writes that skipped post), then run the
#         layout checker on this agent's folder. Only Claude Code reads a block
#         decision from a Stop hook, so the installer passes `--block` there;
#         other hosts get the problems on stderr.
# -----------------------------------------------------------------------------

set -u
PHASE="${1:-}"
HOST_ID="${2:-}"
AGENT_ID="${3:-}"
BLOCK_MODE="${4:-}"
AGENT_NEST_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MATCHER_SCRIPT="$AGENT_NEST_PATH/scripts/hooks/_match-file.py"

[ -z "$PHASE" ] && exit 0
[ -z "$HOST_ID" ] && exit 0
[ -z "$AGENT_ID" ] && exit 0

# Diagnostics only ever go to stderr. Codex parses a Stop hook's stdout as
# JSON when it exits 0 and flags plain text as invalid output, so keep stdout
# empty (git chatter included) for every host.
# fd 3 keeps the real stdout for the one structured reply: a Claude Code
# Stop-hook block decision from the layout checker.
exec 3>&1 1>&2

AGENT_REL_PATH="agents/$HOST_ID/$AGENT_ID"

# -- Check whether the Write/Edit target is under agents/<host>/<id>/ ----------
match_agent_file() {
  python3 "$MATCHER_SCRIPT" "$AGENT_NEST_PATH" "$HOST_ID" "$AGENT_ID"
}

# -- git pull --rebase, abort on conflict --------------------------------------
#
# --autostash stashes any uncommitted working-tree change before rebasing. If
# re-applying that stash conflicts, git leaves the changes parked in the stash,
# resets the working tree clean, and STILL EXITS 0 — a later Write would then
# silently overwrite the parked edit. Detect the leftover stash entry (locale-
# independent, unlike grepping git's message) and treat it as a conflict.
pull_rebase() {
  cd "$AGENT_NEST_PATH" || return 1
  local stash_before stash_after
  stash_before=$(git stash list 2>/dev/null | wc -l)
  if git pull --rebase --autostash -q 2>/dev/null; then
    stash_after=$(git stash list 2>/dev/null | wc -l)
    if [ "$stash_after" -gt "$stash_before" ]; then
      echo "[!] agent-nest[$HOST_ID/$AGENT_ID]: autostash conflict -- uncommitted changes were parked in 'git stash'; run 'git stash pop' and resolve before writing memory" >&2
      return 1
    fi
    return 0
  fi
  git rebase --abort 2>/dev/null || true
  return 1
}

# -- commit + push with retry; warn on persistent conflict ---------------------
#
# IMPORTANT: scope all commits to agents/<host>/<agent-id>/ via explicit
# pathspec to avoid vacuuming unrelated staged files.
commit_push_retry() {
  cd "$AGENT_NEST_PATH" || return 1
  git add "$AGENT_REL_PATH/" >/dev/null 2>&1 || return 1
  if ! git diff --cached --quiet -- "$AGENT_REL_PATH/"; then
    git commit -m "memory: update $HOST_ID/$AGENT_ID" -q -- "$AGENT_REL_PATH/" || return 1
  fi

  # Push whenever local commits are ahead of upstream, not only right after a
  # commit: an earlier push may have failed (offline, rejected) and a clean
  # tree must not stop the safety net from delivering it.
  git rev-parse -q --verify '@{u}' >/dev/null 2>&1 || return 0
  [ "$(git rev-list --count '@{u}..HEAD' 2>/dev/null || echo 0)" -gt 0 ] || return 0

  local attempt
  for attempt in 1 2 3; do
    if git push -q 2>/dev/null; then
      return 0
    fi
    # Push rejected: back off with jitter (~0.5s, ~1s, ~2s) so agents that
    # commit at the same moment do not collide again, then replay the local
    # commits on top of the remote and retry.
    sleep "$(awk -v a="$attempt" 'BEGIN{srand(); printf "%.2f", (2^(a-1))*0.5 + rand()*0.3}')"
    if ! pull_rebase; then
      echo "[!] agent-nest[$HOST_ID/$AGENT_ID]: rebase conflict, memory not pushed, manual merge needed" >&2
      return 1
    fi
  done
  echo "[!] agent-nest[$HOST_ID/$AGENT_ID]: push retried 3 times, all failed; local commit kept, the next hook retries" >&2
  return 1
}

case "$PHASE" in
  pre)
    match_agent_file || exit 0
    pull_rebase || {
      echo "[!] agent-nest[$HOST_ID/$AGENT_ID]: upstream has conflicting changes, resolve manually before writing memory" >&2
      exit 2   # exit 2 blocks the write tool (Claude Write/Edit, Codex apply_patch)
    }
    ;;
  post)
    match_agent_file || exit 0
    commit_push_retry || exit 0   # don't block; warning already emitted
    ;;
  stop)
    payload="$(cat 2>/dev/null || true)"
    commit_push_retry || true
    checker="$AGENT_NEST_PATH/scripts/maintenance/check-nest.py"
    if [ -f "$checker" ]; then
      decision="$(printf '%s' "$payload" | python3 "$checker" --stop-hook \
        --root "$AGENT_NEST_PATH" --host "$HOST_ID" --agent "$AGENT_ID" 2>/dev/null || true)"
      if [ -n "$decision" ]; then
        if [ "$BLOCK_MODE" = "--block" ]; then
          printf '%s\n' "$decision" >&3
        else
          printf '%s' "$decision" | python3 -c 'import json,sys; print(json.load(sys.stdin)["reason"])' >&2 || true
        fi
      fi
    fi
    ;;
  *)
    exit 0
    ;;
esac
exit 0
