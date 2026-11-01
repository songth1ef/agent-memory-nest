import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
GUARD = REPO_ROOT / "scripts" / "git-hooks" / "pre-push"
NESTWORK = "nest" + "work"


class PushGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        shutil.copytree(REPO_ROOT / "scripts" / "lib", self.root / "scripts" / "lib")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def push(self, url: str) -> int:
        return subprocess.run(
            ["bash", str(GUARD), "origin", url],
            cwd=self.root, capture_output=True, text=True, check=False,
        ).returncode

    def make_nest(self) -> None:
        agent = self.root / "agents" / "laptop" / "claude-ab12"
        agent.mkdir(parents=True)
        (agent / "memory.md").write_text("# Memory\n", encoding="utf-8")

    def test_nest_cannot_push_to_the_public_template(self) -> None:
        self.make_nest()
        for url in (
            "https://github.com/songth1ef/agent-memory-nest.git",
            "git@github.com:songth1ef/agent-memory-nest.git",
            f"https://github.com/SongTh1ef/{NESTWORK}",
            "ssh://git@github.com:22/songth1ef/agent-memory-nest.git",
            "ssh://git@ssh.github.com:443/songth1ef/agent-memory-nest.git",
            "git@github.com:/songth1ef/agent-memory-nest.git",
            "https://github.com//songth1ef/agent-memory-nest/",
        ):
            with self.subTest(url=url):
                self.assertEqual(self.push(url), 1)

    def test_nest_can_push_to_its_own_private_remote(self) -> None:
        self.make_nest()
        self.assertEqual(self.push("git@github.com:me/my-nest.git"), 0)
        # A different repository whose name only starts the same is not blocked.
        self.assertEqual(self.push("https://github.com/songth1ef/agent-memory-nest-private"), 0)

    def test_template_itself_can_push(self) -> None:
        (self.root / "agents").mkdir()
        (self.root / "agents" / ".gitkeep").write_text("", encoding="utf-8")
        self.assertEqual(self.push("https://github.com/songth1ef/agent-memory-nest.git"), 0)

    def test_extra_public_remotes_from_config(self) -> None:
        self.make_nest()
        (self.root / "config.md").write_text(
            '---\npublic_remotes: "gitlab.com/me/blog, github.com/me/site"\n---\n', encoding="utf-8"
        )
        self.assertEqual(self.push("https://gitlab.com/me/blog.git"), 1)
        self.assertEqual(self.push("git@github.com:me/site.git"), 1)
        self.assertEqual(self.push("git@github.com:me/my-nest.git"), 0)


if __name__ == "__main__":
    unittest.main()
