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


    def test_kimi_reinstall_removes_old_hook_tables_without_markers(self) -> None:
        # Review finding: Kimi may rewrite config.toml and drop the comment
        # markers, so old [[hooks]] tables must be matched by their command.
        config = self.root / "config.toml"
        config.write_text(
            'model = "k2"\n\n[[hooks]]\nevent = "Stop"\ncommand = "bash /old/scripts/hooks/' + OLD + '.sh stop h a"\n\n'
            '[[hooks]]\nevent = "Stop"\ncommand = "echo mine"\n',
            encoding="utf-8",
        )
        self.assertEqual(run(INSTALL / "kimi" / "hooks.py", config, "/n", "h", "a").returncode, 0)
        self.assertEqual(run(INSTALL / "kimi" / "hooks.py", config, "/n", "h", "a").returncode, 0)
        text = config.read_text(encoding="utf-8")
        self.assertNotIn(f"{OLD}.sh", text)
        self.assertIn('command = "echo mine"', text)
        self.assertEqual(text.count("scripts/hooks/agent-nest.sh"), 3)
        # Simulate Kimi dropping the markers, then uninstall.
        config.write_text(text.replace("# === agent-nest hooks begin ===", "").replace("# === agent-nest hooks end ===", ""), encoding="utf-8")
        self.assertEqual(run(REPO_ROOT / "scripts/uninstall/kimi/unhooks.py", config).returncode, 0)
        left = config.read_text(encoding="utf-8")
        self.assertNotIn("agent-nest", left)
        self.assertIn("echo mine", left)

    def test_antigravity_reinstall_replaces_the_old_entry(self) -> None:
        hooks = self.root / "hooks.json"
        hooks.write_text(json.dumps({OLD: {"Stop": "old"}, "mine": {"Stop": "keep"}}), encoding="utf-8")
        self.assertEqual(run(INSTALL / "antigravity" / "hooks.py", hooks, "/n", "h", "a").returncode, 0)
        self.assertEqual(sorted(json.loads(hooks.read_text(encoding="utf-8"))), ["agent-nest", "mine"])
        hooks.write_text(json.dumps({OLD: {"Stop": "old"}, "mine": {"Stop": "keep"}}), encoding="utf-8")
        self.assertEqual(run(REPO_ROOT / "scripts/uninstall/antigravity/unhooks.py", hooks).returncode, 0)
        self.assertEqual(list(json.loads(hooks.read_text(encoding="utf-8"))), ["mine"])

    def test_claude_reinstall_keeps_unrelated_user_hooks(self) -> None:
        settings = self.root / "settings.json"
        mine = "bash ~/tools/session-start.sh"
        settings.write_text(json.dumps({"hooks": {"SessionStart": [
            {"matcher": "", "hooks": [{"type": "command", "command": mine}]},
            {"matcher": "", "hooks": [{"type": "command", "command": "echo shared-entry"},
                                      {"type": "command", "command": f"bash /old/scripts/hooks/{OLD}.sh stop h a"}]},
        ]}}), encoding="utf-8")
        self.assertEqual(run(INSTALL / "claude" / "hooks.py", settings, "/n", "h", "a").returncode, 0)
        commands = [h["command"] for e in json.loads(settings.read_text(encoding="utf-8"))["hooks"]["SessionStart"] for h in e["hooks"]]
        self.assertIn(mine, commands)
        self.assertIn("echo shared-entry", commands)
        self.assertFalse(any(f"{OLD}.sh" in c for c in commands))

if __name__ == "__main__":
    unittest.main()
