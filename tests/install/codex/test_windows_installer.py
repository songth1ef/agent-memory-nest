import unittest
from pathlib import Path


REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
CODEX_INSTALLER = REPO_ROOT / "scripts" / "install" / "codex" / "install.ps1"
CODEX_INSTALLER_SH = REPO_ROOT / "scripts" / "install" / "codex" / "install.sh"


class CodexWindowsInstallerTests(unittest.TestCase):
    def test_installer_bootstraps_codex_agents_md(self) -> None:
        content = CODEX_INSTALLER.read_text(encoding="utf-8")

        self.assertIn('$CodexAgents = "$CodexDir\\AGENTS.md"', content)
        self.assertRegex(
            content,
            r'bootstrap\.py"\)\s+`\s+"\$CodexAgents"',
            msg="Codex installer should inject agent-nest bootstrap into ~/.codex/AGENTS.md",
        )

    def test_windows_installer_registers_current_codex_hooks_file(self) -> None:
        content = CODEX_INSTALLER.read_text(encoding="utf-8")
        self.assertIn('$CodexConfig = "$CodexDir\\config.toml"', content)
        self.assertIn('$CodexHooks = "$CodexDir\\hooks.json"', content)
        self.assertIn("codex/hooks.py", content.replace("\\", "/"))
        self.assertNotIn('$Settings = "$CodexDir\\config.json"', content)

    def test_bash_installer_registers_current_codex_hooks_file(self) -> None:
        content = CODEX_INSTALLER_SH.read_text(encoding="utf-8")

        self.assertIn('CODEX_CONFIG="$CODEX_DIR/config.toml"', content)
        self.assertIn('CODEX_HOOKS="$CODEX_DIR/hooks.json"', content)
        self.assertIn("codex/hooks.py", content.replace("\\", "/"))
        self.assertNotIn('SETTINGS="$CODEX_DIR/config.json"', content)


if __name__ == "__main__":
    unittest.main()
