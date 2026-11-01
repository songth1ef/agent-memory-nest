import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
IDENTITY = REPO_ROOT / "scripts" / "install" / "_common" / "identity.py"
NESTWORK = "nest" + "work"
LEGACY_ID = f".{NESTWORK}_id"
TMP_ROOT = REPO_ROOT / ".test-tmp"


class IdentityTests(unittest.TestCase):
    def run_identity(self, home: Path, tool: str, *args: str) -> list[str]:
        env = os.environ.copy()
        env["USERPROFILE"] = str(home)
        env["HOME"] = str(home)
        env.pop("AGENT_NEST_HOST", None)
        env.pop("AGENT_NEST_AGENT_ID", None)

        completed = subprocess.run(
            [sys.executable, str(IDENTITY), tool, *args],
            capture_output=True,
            env=env,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        return completed.stdout.strip().splitlines()

    def test_persists_host_and_agent_id_per_tool(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmp:
            home = Path(tmp)

            first = self.run_identity(home, "codex")
            second = self.run_identity(home, "codex")

            self.assertEqual(first, second)
            self.assertEqual((home / ".agent_nest_host").read_text(encoding="utf-8").strip(), first[0])
            self.assertEqual((home / ".agent_nest_id_codex").read_text(encoding="utf-8").strip(), first[1])

    def test_migrates_existing_claude_identity_to_tool_specific_file(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmp:
            home = Path(tmp)
            (home / ".agent_nest_host").write_text("workstation\n", encoding="utf-8")
            (home / LEGACY_ID).write_text("claude-b4d8\n", encoding="utf-8")

            identity = self.run_identity(home, "claude", "--with-suffix")

            self.assertEqual(identity, ["workstation", "claude-b4d8"])
            self.assertEqual(
                (home / ".agent_nest_id_claude").read_text(encoding="utf-8").strip(),
                "claude-b4d8",
            )

    def test_codex_install_does_not_replace_existing_claude_identity(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmp:
            home = Path(tmp)
            (home / ".agent_nest_host").write_text("workstation\n", encoding="utf-8")
            (home / LEGACY_ID).write_text("claude-e5f6\n", encoding="utf-8")

            codex = self.run_identity(home, "codex")
            claude = self.run_identity(home, "claude", "--with-suffix")

            self.assertEqual(codex, ["workstation", "codex"])
            self.assertEqual(claude, ["workstation", "claude-e5f6"])
            self.assertEqual((home / LEGACY_ID).read_text(encoding="utf-8").strip(), "claude-e5f6")
            self.assertEqual((home / ".agent_nest_id_codex").read_text(encoding="utf-8").strip(), "codex")
            self.assertEqual((home / ".agent_nest_id_claude").read_text(encoding="utf-8").strip(), "claude-e5f6")

    def test_carries_over_nestwork_host_and_tool_ids(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmp:
            home = Path(tmp)
            (home / f".{NESTWORK}_host").write_text("Laptop\n", encoding="utf-8")
            (home / f".{NESTWORK}_id_claude").write_text("claude-k9x2\n", encoding="utf-8")
            (home / f".{NESTWORK}_id_codex").write_text("codex\n", encoding="utf-8")

            claude = self.run_identity(home, "claude", "--with-suffix")
            codex = self.run_identity(home, "codex")

            self.assertEqual(claude, ["laptop", "claude-k9x2"])
            self.assertEqual(codex, ["laptop", "codex"])
            self.assertEqual((home / ".agent_nest_id_claude").read_text(encoding="utf-8").strip(), "claude-k9x2")
            # The old files are kept so an un-migrated tool on this machine still works.
            self.assertTrue((home / f".{NESTWORK}_id_claude").exists())

    def test_new_identity_wins_over_nestwork_files(self) -> None:
        TMP_ROOT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TMP_ROOT) as tmp:
            home = Path(tmp)
            (home / ".agent_nest_host").write_text("desk\n", encoding="utf-8")
            (home / ".agent_nest_id_claude").write_text("claude-new1\n", encoding="utf-8")
            (home / f".{NESTWORK}_host").write_text("old\n", encoding="utf-8")
            (home / f".{NESTWORK}_id_claude").write_text("claude-old1\n", encoding="utf-8")

            self.assertEqual(self.run_identity(home, "claude", "--with-suffix"), ["desk", "claude-new1"])

    @classmethod
    def tearDownClass(cls) -> None:
        if TMP_ROOT.exists():
            shutil.rmtree(TMP_ROOT)


if __name__ == "__main__":
    unittest.main()
