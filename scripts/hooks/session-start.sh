#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# agent-nest SessionStart hook (tiered loading)
#
# Usage (registered by installer in Claude Code settings.json):
#   session-start.sh <host> <agent-id>
#
# Emits resident file paths only, keeping stdout independent of memory size.
# Resident = rules, shared/agent summaries and a generated recent-activity digest.
# History, strategy, projects, workflows and inbox contents are on demand.
# Missing resident summaries never fall back to loading historical memory.
# Always exits 0 so unavailable context does not block the host application.
# -----------------------------------------------------------------------------

set -u
HOST_ID="${1:-}"
AGENT_ID="${2:-}"
AGENT_NEST_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

[ -z "$HOST_ID" ] && exit 0
[ -z "$AGENT_ID" ] && exit 0

cd "$AGENT_NEST_PATH" || exit 0

PYTHON_BIN="$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)"

# Settings come from config.md and agents/<host>/config.md (see config.example.md).
# A missing python or config file falls back to the given default.
cfg() {
  local value=""
  if [ -n "$PYTHON_BIN" ] && [ -f scripts/lib/nest_config.py ]; then
    value="$("$PYTHON_BIN" scripts/lib/nest_config.py get "$1" --root "$AGENT_NEST_PATH" --host "$HOST_ID" 2>/dev/null || true)"
  fi
  printf '%s' "${value:-$2}"
}

# Native-format path for the manifest. On Git Bash / MSYS the pwd above yields
# `/f/code/...`, which the agent's Read tool on Windows cannot resolve. cygpath
# -m converts to mixed format (`C:/code/...`); on POSIX hosts cygpath is absent
# and we keep the original POSIX path.
if command -v cygpath >/dev/null 2>&1; then
  AGENT_NEST_PATH_NATIVE="$(cygpath -m "$AGENT_NEST_PATH" 2>/dev/null || printf '%s' "$AGENT_NEST_PATH")"
else
  AGENT_NEST_PATH_NATIVE="$AGENT_NEST_PATH"
fi

# Branch guard: the nest must be on its default branch, otherwise every agent
# silently reads another branch's context (e.g. an upstream feature branch left
# checked out in a private instance) and the pull below rebases that branch.
# Warn and skip the pull; never switch branches on the user's behalf.
BRANCH_WARNING=""
CURRENT_BRANCH="$(git symbolic-ref -q --short HEAD 2>/dev/null || true)"
DEFAULT_BRANCH="$(git symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null || true)"
DEFAULT_BRANCH="${DEFAULT_BRANCH#origin/}"
if [ -n "$DEFAULT_BRANCH" ] && [ "$CURRENT_BRANCH" != "$DEFAULT_BRANCH" ]; then
  BRANCH_WARNING="[!] agent-memory-nest checkout is on '${CURRENT_BRANCH:-detached HEAD}', not '$DEFAULT_BRANCH': context below may not be this instance's; pull skipped. Tell the user; fix with: git -C $AGENT_NEST_PATH_NATIVE switch $DEFAULT_BRANCH"
else
  # Refresh, but never block on failure (offline, conflict, etc.)
  git pull --rebase --autostash -q 2>/dev/null || git rebase --abort 2>/dev/null || true
fi

# Recent-activity digest: one nest-level file shared by every
# agent. It is derived only from synced git history, so every machine computes
# the same content; it stays git-ignored and is rebuilt each session instead of
# being committed (no per-session commits, no cross-machine conflicts).
RECENT_REL="local/recent.md"
# Instances created before 3.2 lack `/local/` in .gitignore (update.sh does not
# touch it), so ignore it via the repo-local exclude file; an untracked digest
# would otherwise dirty the tree and block update.sh.
EXCLUDE_FILE="$(git rev-parse --git-path info/exclude 2>/dev/null || true)"
if [ -n "$EXCLUDE_FILE" ] && ! git check-ignore -q "$RECENT_REL" 2>/dev/null; then
  mkdir -p "$(dirname "$EXCLUDE_FILE")" 2>/dev/null || true
  printf '/local/\n' >> "$EXCLUDE_FILE" 2>/dev/null || true
fi
if [ "$(cfg recent_digest true)" = "true" ] && [ -n "$PYTHON_BIN" ] && [ -f scripts/maintenance/recent-digest.py ]; then
  "$PYTHON_BIN" scripts/maintenance/recent-digest.py --out "$RECENT_REL" >/dev/null 2>&1 || true
fi

# Agent mailbox (on demand): refresh this agent's unread-message snapshot into its
# git-ignored local/ dir. List it only in READ-ON-DEMAND; refreshing the snapshot
# does not require the agent to read messages at every startup.
# Deletes the snapshot when there is nothing unread. Never blocks startup.
if [ "$(cfg mailbox true)" = "true" ] && [ -f scripts/comms/read.sh ]; then
  AGENT_NEST_SELF="$HOST_ID/$AGENT_ID" \
    bash scripts/comms/read.sh --write "agents/$HOST_ID/$AGENT_ID/local/inbox.md" 2>/dev/null || true
fi

manifest_line() {
  local rel="$1"
  if [ -f "$AGENT_NEST_PATH/$rel" ]; then
    printf -- '- %s/%s\n' "$AGENT_NEST_PATH_NATIVE" "$rel"
  fi
}

printf 'agent-nest context bundle for %s/%s\n' "$HOST_ID" "$AGENT_ID"
[ -n "$BRANCH_WARNING" ] && printf '%s\n' "$BRANCH_WARNING"
printf '\n=== READ-ON-START (resident files only) ===\n'
manifest_line "queen/agent-rules.md"
manifest_line "shared/resident.md"
manifest_line "agents/$HOST_ID/$AGENT_ID/resident.md"
manifest_line "$RECENT_REL"
if [ ! -f queen/agent-rules.md ]; then
  printf '[!] Missing queen/agent-rules.md; report missing rules, do not guess.\n'
fi
if [ ! -f shared/resident.md ]; then
  printf '[!] Resident summary absent; history remains on demand. See AGENTS.md section 1.\n'
fi

printf '\n=== READ-ON-DEMAND (search relevant sections, do not load all) ===\n'
manifest_line "queen/strategy.md"
manifest_line "shared/memory.md"
manifest_line "agents/$HOST_ID/$AGENT_ID/memory.md"
manifest_line "agents/$HOST_ID/$AGENT_ID/local/inbox.md"
printf -- '- %s/projects/ and %s/workflow/ (select by task)\n' "$AGENT_NEST_PATH_NATIVE" "$AGENT_NEST_PATH_NATIVE"

# Distillation reminder: shared memory changes only through distillation, which
# the user triggers by hand. Remind once it has gone `distill.reminder_days`
# without one (0 disables). Measured from the last `memory: distill` commit,
# or from the first commit when the nest has never been distilled.
distill_reminder() {
  local days last now age
  days="$(cfg distill.reminder_days 30)"
  case "$days" in ''|*[!0-9]*|0) return 0 ;; esac
  last="$(git log -1 --format=%ct --grep='^memory: distill' 2>/dev/null || true)"
  [ -z "$last" ] && last="$(git log --reverse --format=%ct 2>/dev/null | head -n1)"
  [ -z "$last" ] && return 0
  now="$(date +%s 2>/dev/null || echo 0)"
  age=$(( (now - last) / 86400 ))
  if [ "$age" -ge "$days" ]; then
    printf '\n[i] Shared memory was last distilled %s days ago (reminder every %s). Suggest to the user: run a distillation (AGENTS.md section 5).\n' "$age" "$days"
  fi
}
distill_reminder || true

# Upstream protocol-version check (AGENTS.md, Upstream updates).
# Compressed to one line so a triggered advisory does not blow the ~2KB budget.
# 24h cache to avoid hitting the network every session start. Never blocks.
check_upstream_version() {
  local cache_dir="${HOME:-/tmp}/.cache/agent-nest"
  local cache_file="${cache_dir}/upstream-check"
  local upstream_url="https://raw.githubusercontent.com/songth1ef/agent-memory-nest/main/AGENTS.md"
  local now upstream_ver=""
  local local_ver=""
  now="$(date +%s 2>/dev/null || echo 0)"

  local_ver="$(grep -oE 'protocol-version: [0-9]+\.[0-9]+' AGENTS.md 2>/dev/null | awk '{print $2}')"
  [ -z "$local_ver" ] && return 0

  if [ -f "$cache_file" ]; then
    local cached_ts="" cached_ver=""
    read -r cached_ts cached_ver < "$cache_file" 2>/dev/null || true
    if [ -n "$cached_ts" ] && [ -n "$cached_ver" ] && \
       [ "$((now - cached_ts))" -lt 86400 ] 2>/dev/null; then
      upstream_ver="$cached_ver"
    fi
  fi

  if [ -z "$upstream_ver" ]; then
    upstream_ver="$(curl -sf -m 3 "$upstream_url" 2>/dev/null \
      | grep -oE 'protocol-version: [0-9]+\.[0-9]+' \
      | awk '{print $2}')"
    if [ -n "$upstream_ver" ]; then
      mkdir -p "$cache_dir" 2>/dev/null || true
      printf '%s %s\n' "$now" "$upstream_ver" > "$cache_file" 2>/dev/null || true
    fi
  fi

  [ -z "$upstream_ver" ] && return 0
  [ "$upstream_ver" = "$local_ver" ] && return 0

  local newer
  newer="$(printf '%s\n%s\n' "$local_ver" "$upstream_ver" | sort -V | tail -n1)"
  if [ "$newer" = "$upstream_ver" ]; then
    printf '\n[!] agent-nest upstream protocol-version %s available (local %s) -- run `bash scripts/maintenance/update.sh` to review.\n' \
      "$upstream_ver" "$local_ver"
  fi
}
[ "$(cfg upstream_check true)" = "true" ] && { check_upstream_version || true; }

exit 0
