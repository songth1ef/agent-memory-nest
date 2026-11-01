#!/usr/bin/env python3
"""Read agent-memory-nest settings from config.md files.

Settings live in the YAML front matter of two markdown files, so people read
the explanation under the front matter while scripts read only the block:

  config.md                    nest-wide settings, shared by every machine
  agents/<host>/config.md      overrides for one machine, written only by it

Precedence: DEFAULTS < config.md < agents/<host>/config.md. A missing file or
key falls back to the layer below, so a config file only lists what it changes.

The parser accepts the small YAML subset the config uses: `key: value` pairs,
one level of nesting by indentation, `#` comments, and scalar values
(true/false, integers, plain or quoted strings). No third-party dependency.

CLI:
  nest_config.py get <dotted.key> [--root DIR] [--host HOST]
  nest_config.py dump [--root DIR] [--host HOST]
"""
import argparse
import json
import sys
from pathlib import Path

DEFAULTS = {
    "split": {
        # A context markdown file over either limit must be split wiki-style:
        # foo.md keeps an index of links and the content moves into foo/.
        "max_lines": 300,
        "max_kb": 32,
    },
    "resident": {
        # Byte budget for each resident.md, read at every session start.
        "max_bytes": 4096,
    },
    "distill": {
        # Session start reminds the user once shared memory has gone this many
        # days without a distillation. 0 turns the reminder off.
        "reminder_days": 30,
    },
    "check_on_stop": True,
    "recent_digest": True,
    "mailbox": True,
    "upstream_check": True,
}


def _scalar(raw: str):
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    lowered = value.lower()
    if lowered in ("true", "yes", "on"):
        return True
    if lowered in ("false", "no", "off"):
        return False
    try:
        return int(value)
    except ValueError:
        return value


def parse_front_matter(text: str) -> dict:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    result: dict = {}
    section = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        content = line.split(" #", 1)[0].rstrip() if not line.lstrip().startswith("#") else ""
        if not content.strip() or ":" not in content:
            continue
        indented = content[:1] in (" ", "\t")
        key, _, value = content.strip().partition(":")
        key = key.strip()
        if indented and section is not None:
            result[section][key] = _scalar(value)
        elif value.strip():
            result[key] = _scalar(value)
            section = None
        else:
            result[key] = {}
            section = key
    return result


def _merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _read(path: Path) -> dict:
    try:
        return parse_front_matter(path.read_text(encoding="utf-8"))
    except OSError:
        return {}


def load(root, host=None) -> dict:
    root = Path(root)
    config = _merge(DEFAULTS, _read(root / "config.md"))
    if host:
        config = _merge(config, _read(root / "agents" / host / "config.md"))
    return config


def get(config: dict, dotted: str, default=None):
    node = config
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def _format(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["get", "dump"])
    parser.add_argument("key", nargs="?")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--host")
    args = parser.parse_args()
    config = load(args.root, args.host)
    if args.command == "dump":
        print(json.dumps(config, ensure_ascii=False, indent=2))
        return 0
    if not args.key:
        parser.error("get needs a key")
    value = get(config, args.key)
    if value is None:
        return 1
    print(_format(value))
    return 0


if __name__ == "__main__":
    sys.exit(main())
