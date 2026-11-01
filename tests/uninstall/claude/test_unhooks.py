import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
BOOTSTRAP = REPO_ROOT / "scripts" / "install" / "_common" / "bootstrap.py"
HOOKS = REPO_ROOT / "scripts" / "install" / "claude" / "hooks.py"
CODEX_HOOKS = REPO_ROOT / "scripts" / "install" / "codex" / "hooks.py"
ANTIGRAVITY_HOOKS = REPO_ROOT / "scripts" / "install" / "antigravity" / "hooks.py"
UNBOOTSTRAP = REPO_ROOT / "scripts" / "uninstall" / "_common" / "unbootstrap.py"
UNHOOKS = REPO_ROOT / "scripts" / "uninstall" / "claude" / "unhooks.py"
CODEX_UNHOOKS = REPO_ROOT / "scripts" / "uninstall" / "codex" / "unhooks.py"
ANTIGRAVITY_UNHOOKS = REPO_ROOT / "scripts" / "uninstall" / "antigravity" / "unhooks.py"
TMP_ROOT = REPO_ROOT / ".test-tmp"


def run(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *[str(a) for a in args]],
        capture_output=True,
        text=True,
    )


class UnhooksTests(unittest.TestCase):
    def setUp(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        self.settings = TMP_ROOT / "unhooks-settings.json"

    def tearDown(self) -> None:
        self.settings.unlink(missing_ok=True)

    def test_removes_all_events_and_keeps_user_hooks(self) -> None:
        user_hook = {
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": "echo user-hook"}],
        }
        self.settings.write_text(
            json.dumps({"model": "opus", "hooks": {"PreToolUse": [user_hook]}}),
            encoding="utf-8",
        )

        completed = run(HOOKS, self.settings, "/tmp/nest", "hosta", "claude-ab12")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        installed = json.loads(self.settings.read_text(encoding="utf-8"))
        self.assertEqual(sorted(installed["hooks"]), ["PostToolUse", "PreToolUse", "SessionStart", "Stop"])

        completed = run(UNHOOKS, self.settings, "hosta", "claude-ab12")
        self.assertEqual(completed.returncode, 0, completed.stderr)

        cleaned = json.loads(self.settings.read_text(encoding="utf-8"))
        self.assertEqual(cleaned.get("model"), "opus")
        self.assertEqual(cleaned["hooks"], {"PreToolUse": [user_hook]})

    def test_removes_hooks_even_without_identity(self) -> None:
        self.settings.write_text("{}", encoding="utf-8")
        run(HOOKS, self.settings, "/tmp/nest", "hosta", "claude-ab12")

        completed = run(UNHOOKS, self.settings, "", "")
        self.assertEqual(completed.returncode, 0, completed.stderr)

        cleaned = json.loads(self.settings.read_text(encoding="utf-8"))
        self.assertNotIn("hooks", cleaned)

    def test_noop_on_missing_settings(self) -> None:
        completed = run(UNHOOKS, TMP_ROOT / "no-settings.json", "h", "a")
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
