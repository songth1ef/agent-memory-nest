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


class UnbootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        self.target = TMP_ROOT / "unbootstrap-test.md"

    def tearDown(self) -> None:
        self.target.unlink(missing_ok=True)

    def install_block(self, preexisting: str = "") -> None:
        if preexisting:
            self.target.write_text(preexisting, encoding="utf-8")
        completed = run(BOOTSTRAP, self.target, "/tmp/nest", "hosta", "claude-ab12")
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_removes_block_and_preserves_user_content(self) -> None:
        user_content = "# My own rules\n\nKeep me around.\n"
        self.install_block(preexisting=user_content)
        installed = self.target.read_text(encoding="utf-8")
        self.assertIn("agent-memory-nest Startup Protocol", installed)

        completed = run(UNBOOTSTRAP, self.target)
        self.assertEqual(completed.returncode, 0, completed.stderr)

        remaining = self.target.read_text(encoding="utf-8")
        self.assertNotIn("agent-nest:begin", remaining)
        self.assertNotIn("agent-memory-nest Startup Protocol", remaining)
        self.assertIn("# My own rules", remaining)
        self.assertIn("Keep me around.", remaining)

    def test_deletes_file_that_only_held_the_block(self) -> None:
        self.install_block()
        completed = run(UNBOOTSTRAP, self.target)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse(self.target.exists())

    def test_noop_without_markers(self) -> None:
        content = "# Unrelated file\n"
        self.target.write_text(content, encoding="utf-8")
        completed = run(UNBOOTSTRAP, self.target)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(self.target.read_text(encoding="utf-8"), content)
        self.assertIn("nothing to remove", completed.stdout)

    def test_noop_on_missing_file(self) -> None:
        completed = run(UNBOOTSTRAP, TMP_ROOT / "does-not-exist.md")
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_install_uninstall_roundtrip_is_stable(self) -> None:
        user_content = "before\n"
        self.install_block(preexisting=user_content)
        run(UNBOOTSTRAP, self.target)
        first = self.target.read_text(encoding="utf-8")
        self.install_block(preexisting="")
        run(UNBOOTSTRAP, self.target)
        second = self.target.read_text(encoding="utf-8")
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
