#!/usr/bin/env python3
"""Register the agent-memory-nest Codex hooks in current Codex configuration.

Hooks written to ~/.codex/hooks.json:
  PreToolUse  (apply_patch) -> agent-nest.sh pre   pull --rebase before a memory write
  PostToolUse (apply_patch) -> agent-nest.sh post  commit + push the write
  Stop                      -> agent-nest.sh stop  safety net + layout check

Re-running is idempotent: every prior agent-nest entry is dropped before the
current set is appended, and entries that are not agent-nest's are kept.
Entries left by the former Nestwork installer (nestwork.sh, the SessionEnd
local-history launcher) are recognised and removed too.
"""

import json
import os
import re
import shlex
import sys


def toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def install_hooks_path(config: str, hooks_path: str) -> str:
    line = f"hooksPath = {toml_string(hooks_path)}"
    core = re.search(r"(?ms)^\[core\]\s*\n(?P<body>.*?)(?=^\[|\Z)", config)
    if core:
        body = core.group("body")
        if re.search(r"(?m)^\s*hooksPath\s*=", body):
            body = re.sub(r"(?m)^\s*hooksPath\s*=.*$", line, body, count=1)
        else:
            body = line + "\n" + body
        return config[: core.start("body")] + body + config[core.end("body") :]
    suffix = "" if not config or config.endswith("\n") else "\n"
    prefix = "" if not config else "\n"
    return config + suffix + prefix + "[core]\n" + line + "\n"


# Codex hands apply_patch edits to hooks with tool_name "apply_patch" and
# also accepts the Edit / Write aliases in matchers; anchor so unrelated tools
# (e.g. mcp__*__write_file) never spawn the hook.
WRITE_MATCHER = "^(apply_patch|Edit|Write)$"
# SessionEnd is no longer registered, but stays listed so a reinstall clears
# the local-history entry an older install left there.
AGENT_NEST_EVENTS = ("PreToolUse", "PostToolUse", "Stop", "SessionEnd")
LEGACY_SCRIPTS = (
    "scripts/hooks/" + "nest" + "work.sh",
    "scripts/hooks/launch-local-history-sync.py",
    "scripts/hooks/sync-local-history.sh",
)


def is_agent_nest_hook(command: str) -> bool:
    # Match on agent-nest's own script paths, like the Claude installer does. Do
    # not require "agent-nest" in the command: a nest cloned to ~/memory or
    # ~/my-nest has no such substring, and re-installing would stack duplicate
    # hooks instead of replacing them.
    command = command.replace("\\", "/")
    return "scripts/hooks/agent-nest.sh" in command or any(
        script in command for script in LEGACY_SCRIPTS
    )


def remove_existing_agent_nest_hooks(hooks: dict) -> None:
    events = hooks.setdefault("hooks", {})
    for event in AGENT_NEST_EVENTS:
        retained = []
        for entry in events.get(event, []):
            commands = [
                hook.get("command", "")
                for hook in entry.get("hooks", [])
                if isinstance(hook, dict)
            ]
            if not any(is_agent_nest_hook(item) for item in commands):
                retained.append(entry)
        if retained:
            events[event] = retained
        else:
            events.pop(event, None)


def upsert_agent_nest_hooks(
    hooks: dict, agent_nest_path: str, host: str, agent_id: str, platform: str
) -> None:
    remove_existing_agent_nest_hooks(hooks)
    events = hooks["hooks"]

    def add(event: str, command: str, timeout: int, matcher: str = "") -> None:
        entry: dict = {}
        if matcher:
            entry["matcher"] = matcher
        entry["hooks"] = [{"type": "command", "command": command, "timeout": timeout}]
        events.setdefault(event, []).append(entry)

    add("PreToolUse", sync_command("pre", agent_nest_path, host, agent_id, platform),
        30, WRITE_MATCHER)
    add("PostToolUse", sync_command("post", agent_nest_path, host, agent_id, platform),
        60, WRITE_MATCHER)
    add("Stop", sync_command("stop", agent_nest_path, host, agent_id, platform), 60)


def join_command(args: list, platform: str) -> str:
    if platform == "windows":
        import subprocess

        return subprocess.list2cmdline(args)
    return shlex.join(args)


def sync_command(
    phase: str, agent_nest_path: str, host: str, agent_id: str, platform: str
) -> str:
    # Same per-write sync script as Claude Code / Kimi Code; on Windows it
    # needs Git Bash's `bash` on PATH, exactly like the Claude installer.
    script = f"{agent_nest_path}/scripts/hooks/agent-nest.sh"
    return join_command(["bash", script, phase, host, agent_id], platform)


def main() -> int:
    if len(sys.argv) != 6:
        print(
            "usage: _codex_hooks.py <config.toml> <hooks.json> "
            "<agent_nest_path> <host> <agent_id>",
            file=sys.stderr,
        )
        return 2

    config_path, hooks_path, agent_nest_path, host, agent_id = sys.argv[1:]
    platform = os.environ.get("AGENT_NEST_CODEX_PLATFORM", "posix")
    if platform not in {"posix", "windows"}:
        print("AGENT_NEST_CODEX_PLATFORM must be posix or windows", file=sys.stderr)
        return 2

    agent_nest_path = agent_nest_path.replace("\\", "/").rstrip("/")
    hooks_path = hooks_path.replace("\\", "/")
    os.makedirs(os.path.dirname(config_path) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(hooks_path) or ".", exist_ok=True)

    config = ""
    if os.path.exists(config_path):
        with open(config_path, encoding="utf-8") as file:
            config = file.read()
    updated_config = install_hooks_path(config, hooks_path)
    with open(config_path, "w", encoding="utf-8") as file:
        file.write(updated_config)

    hooks = {}
    if os.path.exists(hooks_path):
        with open(hooks_path, encoding="utf-8") as file:
            hooks = json.load(file)
    upsert_agent_nest_hooks(hooks, agent_nest_path, host, agent_id, platform)
    with open(hooks_path, "w", encoding="utf-8") as file:
        json.dump(hooks, file, indent=2)
        file.write("\n")

    print(f"agent-nest Codex hooks registered in {hooks_path} for {host}/{agent_id}")
    print(f"  PreToolUse  ({WRITE_MATCHER}) -> agent-nest.sh pre")
    print(f"  PostToolUse ({WRITE_MATCHER}) -> agent-nest.sh post")
    print("  Stop                                 -> agent-nest.sh stop")
    print("  Codex asks you to review and trust new or changed hooks: run /hooks once.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
