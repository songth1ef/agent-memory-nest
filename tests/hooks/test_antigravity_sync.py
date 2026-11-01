import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
SYNC = REPO_ROOT / "scripts" / "hooks" / "antigravity-sync.py"
ENV = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=ENV)


class AntigravitySyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.origin = base / "origin.git"
        subprocess.run(["git", "init", "--bare", "-q", "-b", "main", str(self.origin)], check=True, env=ENV)
        self.a, self.b = base / "a", base / "b"
        self.a.mkdir()
        self.memory_rel = "agents/h1/a1/memory.md"
        (self.a / "agents/h1/a1").mkdir(parents=True)
        (self.a / self.memory_rel).write_text("line one\n", encoding="utf-8")
        for args in (("init", "-q", "-b", "main"), ("config", "user.name", "t"), ("config", "user.email", "t@example.com"),
                     ("add", "."), ("commit", "-qm", "init"), ("remote", "add", "origin", str(self.origin)),
                     ("push", "-q", "-u", "origin", "main")):
            self.assertEqual(git(self.a, *args).returncode, 0, args)
        subprocess.run(["git", "clone", "-q", str(self.origin), str(self.b)], check=True, env=ENV)
        for args in (("config", "user.name", "t"), ("config", "user.email", "t@example.com")):
            git(self.b, *args)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_sync(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SYNC), str(self.a), "h1", "a1"],
            input=json.dumps({}), capture_output=True, text=True, env=ENV,
        )

    def test_pushes_a_plain_memory_change(self) -> None:
        (self.a / self.memory_rel).write_text("line one\nline two\n", encoding="utf-8")
        result = self.run_sync()
        self.assertEqual(result.stdout.strip(), "{}")
        self.assertEqual(git(self.a, "rev-parse", "HEAD").stdout, git(self.origin, "rev-parse", "main").stdout)

    def test_conflicting_remote_edit_never_publishes_conflict_markers(self) -> None:
        # Codex review on PR #1: the old soft reset + autostash pull committed and
        # pushed `<<<<<<<` markers when another clone edited the same memory file.
        (self.b / self.memory_rel).write_text("line one\nedited elsewhere\n", encoding="utf-8")
        git(self.b, "commit", "-qam", "remote edit")
        git(self.b, "push", "-q")
        (self.a / self.memory_rel).write_text("line one\nedited here\n", encoding="utf-8")

        result = self.run_sync()

        self.assertEqual(result.stdout.strip(), "{}")
        self.assertIn("rebase conflict", result.stderr)
        remote = git(self.origin, "show", f"main:{self.memory_rel}").stdout
        self.assertEqual(remote, "line one\nedited elsewhere\n")
        local = (self.a / self.memory_rel).read_text(encoding="utf-8")
        self.assertNotIn("<<<<<<<", local)
        self.assertIn("edited here", git(self.a, "show", f"HEAD:{self.memory_rel}").stdout)


    def test_clean_tree_still_delivers_a_commit_whose_push_failed(self) -> None:
        git(self.a, "remote", "set-url", "--push", "origin", str(self.origin) + "-missing")
        (self.a / self.memory_rel).write_text("line one\noffline\n", encoding="utf-8")
        self.run_sync()
        self.assertNotEqual(git(self.a, "rev-parse", "HEAD").stdout, git(self.origin, "rev-parse", "main").stdout)
        git(self.a, "remote", "set-url", "--push", "origin", str(self.origin))
        self.run_sync()
        self.assertEqual(git(self.a, "rev-parse", "HEAD").stdout, git(self.origin, "rev-parse", "main").stdout)

if __name__ == "__main__":
    unittest.main()
