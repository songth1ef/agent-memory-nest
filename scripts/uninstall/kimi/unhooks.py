#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# agent-nest hook remover for Kimi Code (inverse of scripts/install/kimi/hooks.py)
#
# Deletes the agent-nest hook block from ~/.kimi-code/config.toml using the same
# comment markers the installer uses. User hooks and other config outside the
# markers are preserved.
#
# Usage:
#   uninstall/kimi/unhooks.py <config.toml>
# -----------------------------------------------------------------------------

import os
import sys

BEGIN_MARK = "# === agent-nest hooks begin ==="
END_MARK   = "# === agent-nest hooks end ==="
# Block written by the former Nestwork installer; treated as our own.
LEGACY_BEGIN_MARK = "# === " + "nest" + "work hooks begin ==="
LEGACY_END_MARK   = "# === " + "nest" + "work hooks end ==="


def adopt_legacy_block(content: str) -> str:
    return content.replace(LEGACY_BEGIN_MARK, BEGIN_MARK).replace(LEGACY_END_MARK, END_MARK)


def strip_block(content: str) -> tuple[str, bool]:
    lines = content.splitlines(keepends=True)
    result = []
    in_block = False
    removed = False
    for line in lines:
        if BEGIN_MARK in line:
            in_block = True
            removed = True
            continue
        if END_MARK in line:
            in_block = False
            continue
        if not in_block:
            result.append(line)
    # Collapse multiple blank lines left by the removed block
    text = "".join(result)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text, removed


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: uninstall/kimi/unhooks.py <config.toml>", file=sys.stderr)
        return 2

    config_path = sys.argv[1]
    if not os.path.exists(config_path):
        print(f"agent-nest Kimi hooks: {config_path} does not exist (nothing to remove)")
        return 0

    with open(config_path, encoding="utf-8-sig") as f:
        content = f.read()
        content = adopt_legacy_block(content)

    content, removed = strip_block(content)
    if not removed:
        print(f"agent-nest Kimi hooks: no marker block in {config_path} (nothing to remove)")
        return 0

    if not content.strip():
        os.remove(config_path)
        print(f"agent-nest Kimi hooks removed; deleted now-empty {config_path}")
    else:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"agent-nest Kimi hooks removed from {config_path} (user config preserved)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
