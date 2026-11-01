import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())


class GenericInstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.home = base / "home"
        self.home.mkdir()
        self.nest = base / "nest"
        shutil.copytree(REPO_ROOT / "scripts", self.nest / "scripts")
        subprocess.run(["git", "init", "-q", str(self.nest)], check=True)
        self.env = dict(os.environ, HOME=str(self.home), AGENT_NEST_HOST="h1",
                        GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def install(self, config_path: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(self.nest / "scripts/install/generic/install.sh"), "qwen", config_path],
            capture_output=True, text=True, env=self.env,
        )

    def test_config_path_with_spaces_is_kept_literal(self) -> None:
        # Codex review on PR #1: `eval` split this path and ran `config/rules.md`.
        target = Path(self.tmp.name) / "tool config" / "rules.md"
        result = self.install(str(target))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("<!-- agent-nest:begin -->", target.read_text(encoding="utf-8"))

    def test_leading_tilde_expands_to_home(self) -> None:
        result = self.install("~/.qwen/QWEN.md")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.home / ".qwen" / "QWEN.md").is_file())

    def test_shell_characters_are_not_executed(self) -> None:
        marker = Path(self.tmp.name) / "pwned"
        self.install(str(Path(self.tmp.name) / f"x$(touch {marker})" / "rules.md"))
        self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
