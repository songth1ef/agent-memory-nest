import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
CONFIG = REPO_ROOT / "scripts" / "lib" / "nest_config.py"
CHECKER = REPO_ROOT / "scripts" / "maintenance" / "check-nest.py"

sys.path.insert(0, str(CONFIG.parent))
import nest_config  # noqa: E402

TOPIC = "---\ndescription: Read before touching the build\n---\n\n# Build\n"


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def run_checker(root: Path, *args: str, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root), *args],
        input=stdin, capture_output=True, text=True, check=False,
    )


class ConfigTests(unittest.TestCase):
    def test_defaults_without_any_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = nest_config.load(tmp, "h")
        self.assertEqual(nest_config.get(cfg, "split.max_lines"), 300)
        self.assertIs(nest_config.get(cfg, "check_on_stop"), True)

    def test_machine_config_overrides_nest_config_overrides_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "config.md", "---\nsplit:\n  max_lines: 120  # tighter\nmailbox: off\n---\n# notes\nsplit: 1\n")
            write(root, "agents/laptop/config.md", "---\nsplit:\n  max_kb: 8\n---\n")
            cfg = nest_config.load(root, "laptop")
            other = nest_config.load(root, "desk")
        self.assertEqual(nest_config.get(cfg, "split.max_lines"), 120)
        self.assertEqual(nest_config.get(cfg, "split.max_kb"), 8)
        self.assertEqual(nest_config.get(other, "split.max_kb"), 32)
        self.assertIs(nest_config.get(cfg, "mailbox"), False)
        # Text below the front matter is documentation, never parsed.
        self.assertIsInstance(nest_config.get(cfg, "split"), dict)

    def test_cli_get_prints_lowercase_booleans(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = subprocess.run(
                [sys.executable, str(CONFIG), "get", "upstream_check", "--root", tmp],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
        self.assertEqual(out, "true")

    def test_example_config_parses_to_the_defaults(self) -> None:
        parsed = nest_config.parse_front_matter((REPO_ROOT / "config.example.md").read_text(encoding="utf-8"))
        self.assertEqual(nest_config._merge(nest_config.DEFAULTS, parsed), nest_config.DEFAULTS)


class CheckerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.agent = "agents/laptop/claude-ab12"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_clean_split_folder_passes(self) -> None:
        write(self.root, f"{self.agent}/memory.md", "# Memory\n- [build.md](build.md) — build notes\n")
        write(self.root, f"{self.agent}/build.md", TOPIC)
        result = run_checker(self.root)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_reports_each_rule(self) -> None:
        write(self.root, "config.md", "---\nsplit:\n  max_lines: 5\nresident:\n  max_bytes: 10\n---\n")
        write(self.root, f"{self.agent}/memory.md", "# Memory\n- [gone.md](gone.md)\n")
        write(self.root, f"{self.agent}/resident.md", "x" * 50)
        write(self.root, f"{self.agent}/nodesc.md", "# no front matter\n")
        write(self.root, "projects/big.md", "line\n" * 6)
        write(self.root, "projects/big/part.md", "part\n")
        result = run_checker(self.root)
        out = result.stdout
        self.assertEqual(result.returncode, 1)
        self.assertIn("resident.md: 50 bytes", out)
        self.assertIn("nodesc.md: topic file has no front matter `description`", out)
        self.assertIn("nodesc.md: not linked from", out)
        self.assertIn("links to missing file gone.md", out)
        self.assertIn("projects/big.md: 6 lines", out)
        self.assertIn("projects/big/part.md: not linked from projects/big.md", out)

    def test_ignores_local_outbox_and_carryover_descriptions(self) -> None:
        write(self.root, f"{self.agent}/memory.md", "# Memory\n")
        write(self.root, f"{self.agent}/local/inbox.md", "anything\n" * 999)
        write(self.root, f"{self.agent}/outbox/msg.md", "to: all\n")
        write(self.root, f"{self.agent}/carryover/claude-code.md", "# no description needed\n")
        result = run_checker(self.root, "--scope", self.agent)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_stop_hook_blocks_once_with_the_problems(self) -> None:
        write(self.root, f"{self.agent}/memory.md", "# Memory\n")
        write(self.root, f"{self.agent}/orphan.md", TOPIC)
        args = ("--stop-hook", "--host", "laptop", "--agent", "claude-ab12")
        first = run_checker(self.root, *args, stdin="{}")
        decision = json.loads(first.stdout)
        self.assertEqual(decision["decision"], "block")
        self.assertIn("orphan.md: not linked", decision["reason"])
        again = run_checker(self.root, *args, stdin=json.dumps({"stop_hook_active": True}))
        self.assertEqual(again.stdout, "")

    def test_stop_hook_checks_only_its_own_folder_and_respects_config(self) -> None:
        write(self.root, "agents/desk/codex/stray.md", "# other agent's problem\n")
        write(self.root, f"{self.agent}/memory.md", "# Memory\n")
        args = ("--stop-hook", "--host", "laptop", "--agent", "claude-ab12")
        self.assertEqual(run_checker(self.root, *args).stdout, "")
        write(self.root, f"{self.agent}/orphan.md", TOPIC)
        write(self.root, "agents/laptop/config.md", "---\ncheck_on_stop: false\n---\n")
        self.assertEqual(run_checker(self.root, *args).stdout, "")


    def test_web_links_and_encoded_names_are_handled(self) -> None:
        write(self.root, f"{self.agent}/memory.md",
              "# Memory\n- [spec](https://github.com/x/y/blob/main/AGENTS.md)\n"
              "- [notes](my%20notes.md) — notes\n- [plan](<my plan.md>) — plan\n- [top](#memory)\n")
        write(self.root, f"{self.agent}/my notes.md", TOPIC)
        write(self.root, f"{self.agent}/my plan.md", TOPIC)
        result = run_checker(self.root)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_config_with_a_bom_is_still_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "config.md").write_bytes("\ufeff---\nsplit:\n  max_lines: 42\n---\n".encode("utf-8"))
            self.assertEqual(nest_config.get(nest_config.load(tmp), "split.max_lines"), 42)

if __name__ == "__main__":
    unittest.main()
