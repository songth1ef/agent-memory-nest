#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# agent-nest hook installer (shared by claude/install.sh and claude/install.ps1)
#
# Merges SessionStart / PreToolUse / PostToolUse / Stop hooks into Claude Code
# settings.json. Safe to re-run: removes prior agent-nest entries (including
# those left by the former Nestwork installer) before inserting new ones.
#
# Usage:
#   install/claude/hooks.py <settings.json> <agent_nest_path> <host> <agent_id>
#
# Why a separate script: PowerShell's ConvertTo-Json mishandles single-element
# nested arrays (serializes them as objects), and repeating the merge logic in
# two shells invites drift. Centralising in Python keeps behaviour identical.
# -----------------------------------------------------------------------------

import json
import os
import shlex
import sys


def is_agent_nest_hook(cmd: str, host: str, agent_id: str) -> bool:
    """Return True if a stored hook command was installed by agent-nest.

    Matches legacy flat layout, v1 subdir layout, and current v2 layout so
    re-running the installer cleanly supersedes any prior install.
    """
    if "hook-agent-nest.sh" in cmd or "hooks/agent-nest.sh" in cmd:
        return True
    for legacy_hook in ("hive" + "queen.sh", "nest" + "work.sh"):
        if f"hook-{legacy_hook}" in cmd or f"hooks/{legacy_hook}" in cmd:
            return True
    if "export-claude-mem.sh" in cmd:
        return True
    if "sync-local-history.sh" in cmd:
        return True
    if "scripts/hooks/session-start.sh" in cmd.replace("\\", "/"):
        return True
    if f"memory: update {agent_id}" in cmd or f"memory: update {host}/{agent_id}" in cmd:
        return True
    if agent_id in cmd and "git push" in cmd:
        return True
    return False


def strip_entry(entry: dict, host: str, agent_id: str):
    """Return the entry without agent-nest commands, or None if nothing is left.

    Every hook in the entry is checked, so a user's own command that shares an
    entry with ours survives.
    """
    hooks = entry.get("hooks") or []
    kept = [h for h in hooks
            if not is_agent_nest_hook((h or {}).get("command", ""), host, agent_id)]
    if not kept:
        return None
    if len(kept) == len(hooks):
        return entry
    return {**entry, "hooks": kept}


def strip_event(hooks: dict, event: str, host: str, agent_id: str) -> list:
    return [e for e in (strip_entry(e, host, agent_id) for e in hooks.get(event, [])) if e]


def upsert(hooks: dict, event: str, matcher: str, cmd: str,
           host: str, agent_id: str) -> None:
    filtered = strip_event(hooks, event, host, agent_id)
    filtered.append({
        "matcher": matcher,
        "hooks":   [{"type": "command", "command": cmd}],
    })
    hooks[event] = filtered


def remove_entries(hooks: dict, event: str, host: str, agent_id: str) -> None:
    """Drop agent-nest entries from an event no longer registered."""
    kept = strip_event(hooks, event, host, agent_id)
    if kept:
        hooks[event] = kept
    else:
        hooks.pop(event, None)


def main() -> int:
    if len(sys.argv) < 5:
        print(
            "usage: install/claude/hooks.py <settings_path> <agent_nest_path> <host> <agent_id>",
            file=sys.stderr,
        )
        return 2

    settings_path  = sys.argv[1]
    agent_nest_path = sys.argv[2].replace("\\", "/").rstrip("/")
    host           = sys.argv[3]
    agent_id       = sys.argv[4]

    hook_script   = f"{agent_nest_path}/scripts/hooks/agent-nest.sh"
    session_start = f"{agent_nest_path}/scripts/hooks/session-start.sh"

    start_cmd = "bash " + shlex.join([session_start, host, agent_id])
    pre_cmd  = "bash " + shlex.join([hook_script, "pre", host, agent_id])
    post_cmd = "bash " + shlex.join([hook_script, "post", host, agent_id])
    # --block: Claude Code reads a Stop-hook block decision, so layout problems
    # found by the checker go back to the agent to fix before the turn ends.
    stop_cmd = "bash " + shlex.join([hook_script, "stop", host, agent_id, "--block"])

    os.makedirs(os.path.dirname(settings_path) or ".", exist_ok=True)
    if not os.path.exists(settings_path):
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump({}, f)

    with open(settings_path, encoding="utf-8-sig") as f:
        settings = json.load(f)

    hooks = settings.setdefault("hooks", {})
    upsert(hooks, "SessionStart", "",           start_cmd,       host, agent_id)
    upsert(hooks, "PreToolUse",   "Write|Edit", pre_cmd,         host, agent_id)
    upsert(hooks, "PostToolUse",  "Write|Edit", post_cmd,        host, agent_id)
    upsert(hooks, "Stop",         "",           stop_cmd,        host, agent_id)
    remove_entries(hooks, "SessionEnd", host, agent_id)

    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

    print(f"agent-nest hooks registered in {settings_path} for {host}/{agent_id}")
    print(f"  SessionStart             -> {start_cmd}")
    print(f"  PreToolUse  (Write|Edit) -> {pre_cmd}")
    print(f"  PostToolUse (Write|Edit) -> {post_cmd}")
    print(f"  Stop                     -> {stop_cmd}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
