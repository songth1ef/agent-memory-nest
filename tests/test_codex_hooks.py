import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "scripts" / "install" / "_codex_hooks.py"


class CodexHooksInstallerTests(unittest.TestCase):
    def run_installer(self, root: Path, platform: str = "posix", nest: str = str(REPO_ROOT)) -> tuple[Path, Path]:
        config = root / "config.toml"
        hooks = root / "hooks.json"
        env = os.environ.copy()
        env["AGENT_NEST_CODEX_PLATFORM"] = platform
        completed = subprocess.run(
            [
                sys.executable,
                str(INSTALLER),
                str(config),
                str(hooks),
                nest,
                "test-host",
                "codex",
            ],
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return config, hooks

    def test_registers_per_write_sync_and_stop_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config, hooks = self.run_installer(Path(directory))

            self.assertIn(
                f'hooksPath = "{hooks.as_posix()}"',
                config.read_text(encoding="utf-8"),
            )
            data = json.loads(hooks.read_text(encoding="utf-8"))["hooks"]
            # Per-write sync: same agent-nest.sh phases as Claude Code / Kimi Code,
            # scoped to Codex's file-edit tool (apply_patch, Edit/Write aliases).
            for event, phase in (("PreToolUse", "pre"), ("PostToolUse", "post")):
                with self.subTest(event=event):
                    (entry,) = data[event]
                    self.assertEqual(entry["matcher"], "^(apply_patch|Edit|Write)$")
                    command = entry["hooks"][0]["command"]
                    self.assertIn("scripts/hooks/agent-nest.sh", command)
                    self.assertTrue(command.endswith(f" {phase} test-host codex"), command)
            (stop,) = data["Stop"]
            self.assertNotIn("matcher", stop)
            self.assertTrue(stop["hooks"][0]["command"].endswith(" stop test-host codex"))
            # Local-history sync was removed; nothing is registered on SessionEnd.
            self.assertNotIn("SessionEnd", data)

    def test_reinstall_is_idempotent_and_preserves_user_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "config.toml"
            hooks = root / "hooks.json"
            config.write_text('[core]\nhooksPath = "old.json"\n\n[profiles.test]\nmodel = "x"\n')
            hooks.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "Stop": [
                                {"hooks": [{"type": "command", "command": "keep-this"}]},
                                {
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": "bash /old/agent-nest/scripts/hooks/sync-local-history.sh host codex",
                                        }
                                    ]
                                },
                            ],
                            "SessionEnd": [
                                {"hooks": [{"type": "command", "command": "keep-end"}]},
                                {"hooks": [{"type": "command", "command": "py /old/scripts/hooks/launch-local-history-sync.py /old h codex"}]},
                            ],
                            "PreToolUse": [
                                {"hooks": [{"type": "command", "command": "bash /old/scripts/hooks/" + "nest" + "work.sh pre h codex"}]}
                            ],
                            "Other": [{"hooks": [{"command": "untouched"}]}],
                        }
                    }
                ),
                encoding="utf-8",
            )

            self.run_installer(root)
            self.run_installer(root)

            updated_config = config.read_text(encoding="utf-8")
            self.assertEqual(updated_config.count("hooksPath ="), 1)
            self.assertIn("[profiles.test]", updated_config)
            updated_hooks = json.loads(hooks.read_text(encoding="utf-8"))
            stops = updated_hooks["hooks"]["Stop"]
            # The user's hook survives, the legacy sync-local-history entry is
            # gone, and two installs leave exactly one agent-nest Stop entry.
            self.assertEqual([s["hooks"][0]["command"] for s in stops][0], "keep-this")
            self.assertEqual(len(stops), 2)
            self.assertIn("agent-nest.sh stop", stops[1]["hooks"][0]["command"])
            self.assertFalse(any("sync-local-history.sh" in s["hooks"][0]["command"] for s in stops))
            for event in ("PreToolUse", "PostToolUse"):
                self.assertEqual(len(updated_hooks["hooks"][event]), 1, event)
            # Entries left by the former Nestwork installer are replaced, the
            # user's own SessionEnd hook is kept.
            ends = updated_hooks["hooks"]["SessionEnd"]
            self.assertEqual([e["hooks"][0]["command"] for e in ends], ["keep-end"])
            pre = updated_hooks["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
            self.assertIn("agent-nest.sh pre", pre)
            self.assertEqual(updated_hooks["hooks"]["Other"][0]["hooks"][0]["command"], "untouched")

    def test_reinstall_from_a_path_without_agent_nest_in_it(self) -> None:
        # Regression: ownership used to require the substring "agent-nest" in the
        # hook command, so a nest at e.g. /opt/my-memory stacked a new copy of
        # every hook on each re-install.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for _ in range(2):
                _, hooks = self.run_installer(root, nest="/opt/my-memory")
            data = json.loads(hooks.read_text(encoding="utf-8"))["hooks"]
            for event in ("PreToolUse", "PostToolUse", "Stop"):
                self.assertEqual(len(data[event]), 1, event)

    def test_ownership_ignores_unrelated_hooks(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("codex_hooks", INSTALLER)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        self.assertTrue(mod.is_agent_nest_hook("bash /opt/my-memory/scripts/hooks/agent-nest.sh post h a"))
        self.assertTrue(mod.is_agent_nest_hook(r"py C:\mem\scripts\hooks\launch-local-history-sync.py C:/mem h a"))
        self.assertTrue(mod.is_agent_nest_hook("bash /opt/mem/scripts/hooks/" + "nest" + "work.sh stop h a"))
        self.assertFalse(mod.is_agent_nest_hook("echo agent-nest is great"))
        self.assertFalse(mod.is_agent_nest_hook("bash ~/tools/agent-nest-backup.sh"))

    def test_windows_sync_hooks_run_through_bash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, hooks = self.run_installer(Path(directory), platform="windows")
            data = json.loads(hooks.read_text(encoding="utf-8"))["hooks"]
            command = data["PreToolUse"][0]["hooks"][0]["command"]
            self.assertTrue(command.startswith("bash "), command)
            self.assertIn("scripts/hooks/agent-nest.sh pre test-host codex", command)


if __name__ == "__main__":
    unittest.main()
