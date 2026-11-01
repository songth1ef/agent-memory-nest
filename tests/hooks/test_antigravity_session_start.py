import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
HOOK = REPO_ROOT / "scripts" / "hooks" / "antigravity-session-start.py"


@unittest.skipIf(os.name == "nt", "the mailbox refresh runs through bash")
class AntigravitySessionStartTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.nest = base / "nest"
        self.project = base / "project"
        self.project.mkdir()
        self.env = dict(os.environ, HOME=str(base), ANTIGRAVITY_HOME=str(base / "gemini"),
                        GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
        subprocess.run(["git", "init", "-q", str(self.nest)], check=True, env=self.env)
        shutil.copytree(REPO_ROOT / "scripts" / "comms", self.nest / "scripts" / "comms")
        for args in (("config", "user.name", "t"), ("config", "user.email", "t@example.com")):
            subprocess.run(["git", "-C", str(self.nest), *args], check=True, env=self.env)
        (self.nest / "agents" / "h1" / "a1").mkdir(parents=True)
        (self.nest / "agents" / "h1" / "a1" / "memory.md").write_text("# m\n", encoding="utf-8")
        subprocess.run(
            ["bash", str(self.nest / "scripts" / "comms" / "send.sh"), "h1/a1", "message", "hello"],
            cwd=self.nest, input="ping\n", text=True, capture_output=True,
            env=dict(self.env, AGENT_NEST_SELF="h2/b2"),
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_inbox_refresh_reads_the_nest_not_the_current_project(self) -> None:
        # Codex review on PR #1: read.sh resolves the repository from the
        # working directory, and Antigravity usually runs inside a project.
        result = subprocess.run(
            [sys.executable, str(HOOK), str(self.nest), "h1", "a1"],
            cwd=self.project, input=json.dumps({"conversationId": "c1"}),
            capture_output=True, text=True, env=self.env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        inbox = self.nest / "agents" / "h1" / "a1" / "local" / "inbox.md"
        self.assertTrue(inbox.exists(), result.stdout)
        self.assertIn("hello", inbox.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
