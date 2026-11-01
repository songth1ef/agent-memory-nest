#!/usr/bin/env python3
"""Register the agent-memory-nest Antigravity hooks in hooks.json.

Hooks written to ~/.gemini/config/hooks.json (under "agent-nest" key):
  PreInvocation -> antigravity-session-start.py
  Stop          -> antigravity-sync.py

Re-running is idempotent: existing "agent-nest" hook entry is updated,
while user-defined hooks in hooks.json are preserved.
"""

import json
import os
import sys


def upsert_agent_nest_hooks(
    data: dict, agent_nest_path: str, host: str, agent_id: str, platform: str
) -> None:
    py_bin = "python" if platform == "windows" else "python3"
    start_script = f"{agent_nest_path}/scripts/hooks/antigravity-session-start.py"
    sync_script = f"{agent_nest_path}/scripts/hooks/antigravity-sync.py"

    start_cmd = f'{py_bin} "{start_script}" "{agent_nest_path}" "{host}" "{agent_id}"'
    sync_cmd = f'{py_bin} "{sync_script}" "{agent_nest_path}" "{host}" "{agent_id}"'

    data["agent-nest"] = {
        "PreInvocation": [
            {
                "type": "command",
                "command": start_cmd,
                "timeout": 30,
            }
        ],
        "Stop": [
            {
                "type": "command",
                "command": sync_cmd,
                "timeout": 45,
            }
        ],
    }


def main() -> int:
    if len(sys.argv) < 5:
        print(
            "usage: install/antigravity/hooks.py <hooks_json> <agent_nest_path> <host> <agent_id>",
            file=sys.stderr,
        )
        return 2

    hooks_path, agent_nest_path, host, agent_id = sys.argv[1:5]
    platform = os.environ.get("AGENT_NEST_ANTIGRAVITY_PLATFORM", "windows" if os.name == "nt" else "posix")

    agent_nest_path = agent_nest_path.replace("\\", "/").rstrip("/")
    hooks_path = os.path.abspath(hooks_path)
    os.makedirs(os.path.dirname(hooks_path) or ".", exist_ok=True)

    data = {}
    if os.path.exists(hooks_path):
        try:
            with open(hooks_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
        except Exception:
            data = {}

    upsert_agent_nest_hooks(data, agent_nest_path, host, agent_id, platform)

    with open(hooks_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"agent-nest Antigravity hooks registered in {hooks_path} for {host}/{agent_id}")
    print("  PreInvocation -> antigravity-session-start.py")
    print("  Stop          -> antigravity-sync.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
