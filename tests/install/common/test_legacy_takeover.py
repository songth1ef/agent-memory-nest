"""A reinstall over a former Nestwork install replaces its pieces in place.

Machines installed before the rename carry hooks, bootstrap blocks and Kimi
config blocks that use the old name. Reinstalling must swap them for the new
ones instead of stacking a second copy next to them.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
INSTALL = REPO_ROOT / "scripts" / "install"
OLD = "nest" + "work"


def run(script: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *map(str, args)],
        capture_output=True, text=True, check=False,
    )


class LegacyTakeoverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_claude_hooks_replace_old_entries_and_block_on_stop(self) -> None:
        settings = self.root / "settings.json"
        old = f"/home/u/{OLD}/scripts/hooks"
        user = {"matcher": "", "hooks": [{"type": "command", "command": "echo mine"}]}
        settings.write_text(json.dumps({"hooks": {
            "Stop": [user, {"matcher": "", "hooks": [{"type": "command", "command": f"bash {old}/{OLD}.sh stop h a"}]}],
            "SessionEnd": [{"matcher": "", "hooks": [{"type": "command",
                "command": f"bash {old}/export-claude-mem.sh h a; bash {old}/sync-local-history.sh h a"}]}],
        }}), encoding="utf-8")

        result = run(INSTALL / "claude" / "hooks.py", settings, "/home/u/agent-memory-nest", "h", "a")
        self.assertEqual(result.returncode, 0, result.stderr)

        hooks = json.loads(settings.read_text(encoding="utf-8"))["hooks"]
        stops = [e["hooks"][0]["command"] for e in hooks["Stop"]]
        self.assertEqual(stops[0], "echo mine")
        self.assertEqual(len(stops), 2)
        self.assertTrue(stops[1].endswith("agent-nest.sh stop h a --block"), stops[1])
        self.assertNotIn("SessionEnd", hooks)

    def test_claude_hooks_accept_a_bom_settings_file(self) -> None:
        # Windows PowerShell 5.1 `Set-Content -Encoding UTF8` writes a BOM
        # (Codex review on PR #1); the installer must still read the file.
        settings = self.root / "settings.json"
        settings.write_bytes(b"\xef\xbb\xbf{}")
        result = run(INSTALL / "claude" / "hooks.py", settings, "/home/u/nest", "h", "a")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Stop", json.loads(settings.read_text(encoding="utf-8-sig"))["hooks"])

    def test_hook_commands_survive_spaces_in_the_nest_path(self) -> None:
        import shlex
        settings = self.root / "settings.json"
        nest = self.root / "my nest"
        run(INSTALL / "claude" / "hooks.py", settings, nest, "h", "a")
        hooks = json.loads(settings.read_text(encoding="utf-8"))["hooks"]
        start = shlex.split(hooks["SessionStart"][0]["hooks"][0]["command"])
        stop = shlex.split(hooks["Stop"][0]["hooks"][0]["command"])
        self.assertEqual(start, ["bash", f"{nest.as_posix()}/scripts/hooks/session-start.sh", "h", "a"])
        self.assertEqual(stop[1:], [f"{nest.as_posix()}/scripts/hooks/agent-nest.sh", "stop", "h", "a", "--block"])

    def test_bootstrap_upgrades_the_old_block_and_enables_the_push_guard(self) -> None:
        nest = self.root / "nest"
        (nest / "scripts" / "git-hooks").mkdir(parents=True)
        (nest / "scripts" / "git-hooks" / "pre-push").write_text("#!/bin/sh\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(nest)], check=True)
        target = self.root / "CLAUDE.md"
        target.write_text(
            f"# my notes\n\n<!-- {OLD}:begin -->\nold protocol\n<!-- {OLD}:end -->\n\nmore notes\n",
            encoding="utf-8",
        )

        result = run(INSTALL / "_common" / "bootstrap.py", target, nest, "h", "a")
        self.assertEqual(result.returncode, 0, result.stderr)

        text = target.read_text(encoding="utf-8")
        self.assertEqual(text.count("<!-- agent-nest:begin -->"), 1)
        self.assertNotIn(f"{OLD}:begin", text)
        self.assertNotIn("old protocol", text)
        self.assertIn("# my notes", text)
        self.assertIn("more notes", text)
        self.assertIn("Never push the nest", text)
        hooks_path = subprocess.run(
            ["git", "-C", str(nest), "config", "core.hooksPath"],
            capture_output=True, text=True, check=False,
        ).stdout.strip()
        self.assertEqual(hooks_path, "scripts/git-hooks")

    def test_kimi_reinstall_replaces_the_old_block(self) -> None:
        config = self.root / "config.toml"
        config.write_text(
            f'model = "k2"\n\n# === {OLD} hooks begin ===\n[[hooks]]\nevent = "Stop"\n'
            f'command = "bash /old/{OLD}.sh stop h a"\n# === {OLD} hooks end ===\n',
            encoding="utf-8",
        )

        result = run(INSTALL / "kimi" / "hooks.py", config, "/home/u/agent-memory-nest", "h", "a")
        self.assertEqual(result.returncode, 0, result.stderr)

        text = config.read_text(encoding="utf-8")
        self.assertIn('model = "k2"', text)
        self.assertNotIn(f"{OLD}.sh", text)
        self.assertEqual(text.count("# === agent-nest hooks begin ==="), 1)


if __name__ == "__main__":
    unittest.main()
