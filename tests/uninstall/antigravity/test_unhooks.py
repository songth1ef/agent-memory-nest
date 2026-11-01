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


class AntigravityUnhooksTests(unittest.TestCase):
    def setUp(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        self.hooks = TMP_ROOT / "unhooks-antigravity-hooks.json"

    def tearDown(self) -> None:
        self.hooks.unlink(missing_ok=True)

    def test_removes_agent_nest_hooks_and_keeps_user_hooks(self) -> None:
        user_entry = {
            "PreInvocation": [{"type": "command", "command": "echo user-pre"}]
        }
        self.hooks.write_text(
            json.dumps({"my-custom-hook": user_entry}), encoding="utf-8"
        )

        completed = run(
            ANTIGRAVITY_HOOKS, self.hooks, "/tmp/agent-nest", "hosta", "antigravity"
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        installed = json.loads(self.hooks.read_text(encoding="utf-8"))
        self.assertIn("my-custom-hook", installed)
        self.assertIn("agent-nest", installed)
        self.assertEqual(len(installed["agent-nest"]["PreInvocation"]), 1)
        self.assertEqual(len(installed["agent-nest"]["Stop"]), 1)

        completed = run(ANTIGRAVITY_UNHOOKS, self.hooks)
        self.assertEqual(completed.returncode, 0, completed.stderr)

        cleaned = json.loads(self.hooks.read_text(encoding="utf-8"))
        self.assertIn("my-custom-hook", cleaned)
        self.assertNotIn("agent-nest", cleaned)

    def test_noop_on_missing_hooks_file(self) -> None:
        completed = run(ANTIGRAVITY_UNHOOKS, TMP_ROOT / "no-antigravity-hooks.json")
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
