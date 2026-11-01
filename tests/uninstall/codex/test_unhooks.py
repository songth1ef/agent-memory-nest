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


class CodexUnhooksTests(unittest.TestCase):
    def setUp(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        self.config = TMP_ROOT / "unhooks-config.toml"
        self.hooks = TMP_ROOT / "unhooks-hooks.json"

    def tearDown(self) -> None:
        self.config.unlink(missing_ok=True)
        self.hooks.unlink(missing_ok=True)

    def test_removes_all_agent_nest_hooks_and_keeps_user_hooks(self) -> None:
        user_entry = {
            "hooks": [{"type": "command", "command": "echo user-stop", "timeout": 5}]
        }
        self.hooks.write_text(
            json.dumps({"hooks": {"Stop": [user_entry]}}), encoding="utf-8"
        )

        completed = run(
            CODEX_HOOKS, self.config, self.hooks, "/tmp/agent-nest", "hosta", "codex"
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        installed = json.loads(self.hooks.read_text(encoding="utf-8"))["hooks"]
        self.assertEqual(installed["Stop"][0], user_entry)
        self.assertEqual(len(installed["Stop"]), 2)
        for event in ("PreToolUse", "PostToolUse"):
            self.assertEqual(len(installed[event]), 1, event)
        self.assertNotIn("SessionEnd", installed)

        completed = run(CODEX_UNHOOKS, self.hooks)
        self.assertEqual(completed.returncode, 0, completed.stderr)

        cleaned = json.loads(self.hooks.read_text(encoding="utf-8"))["hooks"]
        self.assertEqual(cleaned["Stop"], [user_entry])
        for event in ("PreToolUse", "PostToolUse", "SessionEnd"):
            self.assertNotIn(event, cleaned)

    def test_noop_on_missing_hooks_file(self) -> None:
        completed = run(CODEX_UNHOOKS, TMP_ROOT / "no-hooks.json")
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
