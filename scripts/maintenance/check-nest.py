#!/usr/bin/env python3
"""Check that nest markdown follows the wiki-style layout rules.

Agents write memory and keep the indexes themselves; this script only detects
mistakes, so the check is mechanical and costs no model tokens. A Stop hook
runs it after each turn and hands any problems back to the agent to fix.

Rules (limits come from config.md, see scripts/lib/nest_config.py):
  1. A context file over split.max_lines or split.max_kb must be split:
     foo.md keeps an index of links and the content moves into foo/.
  2. resident.md must stay within resident.max_bytes.
  3. Every topic file in a memory scope (shared/ or agents/<host>/<id>/) starts
     with front matter carrying a `description`.
  4. Every markdown file in a scope root is linked from that scope's memory.md,
     and every file in a split folder foo/ is linked from foo.md.
  5. Index links point at files that exist.

Usage:
  check-nest.py [--root DIR] [--scope PATH ...] [--host HOST]
  check-nest.py --stop-hook --root DIR --host HOST --agent ID
      Stop-hook mode: checks only the agent's own folder. On problems it
      prints a Claude Code block decision so the agent fixes them before the
      turn ends; it never blocks twice in a row (stop_hook_active).

Exit status: 0 clean, 1 problems found (always 0 in --stop-hook mode).
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import nest_config  # noqa: E402

CONTEXT_DIRS = ("queen", "shared", "agents", "projects", "workflow")
SKIP_PARTS = {"local", "outbox", "comms", "inbox", "archive"}
INDEX_NAMES = {"memory.md", "resident.md", "config.md"}
LINK_RE = re.compile(r"\]\(([^)#\s]+\.md)(?:#[^)]*)?\)")


def _skipped(rel: Path) -> bool:
    return any(p in SKIP_PARTS or p.startswith((".", "_")) for p in rel.parts)


def _context_files(root: Path, scopes):
    bases = [root / s for s in scopes] if scopes else [root / d for d in CONTEXT_DIRS]
    for base in bases:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            if not _skipped(path.relative_to(root)):
                yield path


def _scope_root(root: Path, path: Path):
    rel = path.relative_to(root).parts
    if rel[0] == "shared":
        return root / "shared"
    if rel[0] == "agents" and len(rel) >= 4:
        return root / rel[0] / rel[1] / rel[2]
    return None


def _has_description(text: str) -> bool:
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    return end != -1 and re.search(r"^description:\s*\S", text[3:end], re.M) is not None


def _links(index: Path):
    try:
        text = index.read_text(encoding="utf-8")
    except OSError:
        return set()
    return {(index.parent / m).resolve() for m in LINK_RE.findall(text)}


def check(root: Path, scopes, host=None):
    cfg = nest_config.load(root, host)
    max_lines = nest_config.get(cfg, "split.max_lines")
    max_bytes = nest_config.get(cfg, "split.max_kb") * 1024
    resident_bytes = nest_config.get(cfg, "resident.max_bytes")
    problems = []
    files = list(_context_files(root, scopes))

    for path in files:
        rel = path.relative_to(root).as_posix()
        data = path.read_bytes()
        lines = data.count(b"\n") + (0 if data.endswith(b"\n") or not data else 1)
        if path.name == "resident.md":
            if len(data) > resident_bytes:
                problems.append(f"{rel}: {len(data)} bytes, over the resident budget of {resident_bytes}; move detail to memory.md or a topic file")
            continue
        if lines > max_lines or len(data) > max_bytes:
            problems.append(f"{rel}: {lines} lines / {len(data) // 1024} KB, over the split limit ({max_lines} lines / {max_bytes // 1024} KB); keep {path.name} as an index and move the content into {path.stem}/")

        scope = _scope_root(root, path)
        if scope is not None and path.name not in INDEX_NAMES and path.parent.name != "carryover":
            if not _has_description(data.decode("utf-8", "replace")):
                problems.append(f"{rel}: topic file has no front matter `description` (say when to read it)")

    for path in files:
        rel = path.relative_to(root).as_posix()
        scope = _scope_root(root, path)
        if scope is not None and path.parent == scope and path.name not in INDEX_NAMES:
            index = scope / "memory.md"
        elif (path.parent.parent / f"{path.parent.name}.md").exists():
            index = path.parent.parent / f"{path.parent.name}.md"
        else:
            continue
        if path.resolve() not in _links(index):
            problems.append(f"{rel}: not linked from {index.relative_to(root).as_posix()}; add a line with its description")

    indexes = {p for p in files if p.name == "memory.md" or (p.parent / p.stem).is_dir()}
    for index in sorted(indexes):
        for target in sorted(_links(index)):
            if not target.exists():
                problems.append(f"{index.relative_to(root).as_posix()}: links to missing file {target.name}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--scope", action="append", default=[])
    parser.add_argument("--host")
    parser.add_argument("--agent")
    parser.add_argument("--stop-hook", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    if args.stop_hook:
        if not (args.host and args.agent):
            return 0
        try:
            payload = json.loads(sys.stdin.read() or "{}")
        except ValueError:
            payload = {}
        cfg = nest_config.load(root, args.host)
        if not nest_config.get(cfg, "check_on_stop", True) or payload.get("stop_hook_active"):
            return 0
        problems = check(root, [f"agents/{args.host}/{args.agent}"], args.host)
        if problems:
            reason = "agent-memory-nest layout check failed; fix these before finishing:\n- " + "\n- ".join(problems)
            print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
        return 0

    problems = check(root, args.scope, args.host)
    for problem in problems:
        print(problem)
    if not problems:
        print("OK: nest layout follows the rules")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
