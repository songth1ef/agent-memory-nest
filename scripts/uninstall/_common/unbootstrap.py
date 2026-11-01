#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# agent-nest bootstrap remover (shared by every scripts/uninstall/<tool>/uninstall.*)
#
# Inverse of scripts/install/_common/bootstrap.py: deletes the agent-nest marker block
# (current and legacy marker names) from a tool-specific markdown file while
# preserving every byte of user content outside the markers.
#
# Behaviour:
#   - File does not exist            -> no-op
#   - Markers present                -> remove block (plus surrounding blank run)
#   - File empty after removal       -> delete the file (installer created it)
#   - No markers                     -> no-op, report "not installed"
#
# Never touches agents/<host>/<id>/ memory or identity files.
#
# Usage:
#   _unbootstrap.py <target_md>
# -----------------------------------------------------------------------------

import os
import re
import sys

BEGIN = "<!-- agent-nest:begin -->"
END   = "<!-- agent-nest:end -->"
LEGACY_MARKERS = [
    (f"<!-- {n}:begin -->", f"<!-- {n}:end -->") for n in ("hive" + "queen", "nest" + "work")
]


def strip_block(content: str, begin: str, end: str) -> tuple[str, bool]:
    pattern = re.compile(
        r"[ \t]*" + re.escape(begin) + r".*?" + re.escape(end) + r"[ \t]*\n?",
        re.DOTALL,
    )
    stripped, count = pattern.subn("", content)
    if count:
        # Collapse the blank run left where the block used to sit.
        stripped = re.sub(r"\n{3,}", "\n\n", stripped)
    return stripped, bool(count)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: _unbootstrap.py <target_md>", file=sys.stderr)
        return 2

    target = sys.argv[1]
    if not os.path.exists(target):
        print(f"agent-nest bootstrap: {target} does not exist (nothing to remove)")
        return 0

    with open(target, encoding="utf-8") as f:
        content = f.read()

    content, removed = strip_block(content, BEGIN, END)
    removed_legacy = False
    for legacy_begin, legacy_end in LEGACY_MARKERS:
        content, hit = strip_block(content, legacy_begin, legacy_end)
        removed_legacy = removed_legacy or hit

    if not (removed or removed_legacy):
        print(f"agent-nest bootstrap: no marker block in {target} (nothing to remove)")
        return 0

    if not content.strip():
        os.remove(target)
        print(f"agent-nest bootstrap removed; deleted now-empty {target}")
    else:
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"agent-nest bootstrap removed from {target} (user content preserved)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
