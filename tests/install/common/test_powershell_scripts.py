"""Static checks on the PowerShell installers (no PowerShell needed to run them).

Both bugs below were found on a real Windows machine during the 1.0 migration;
the fixes were verified there with Windows PowerShell 5.1.
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
SCRIPTS = sorted(REPO_ROOT.glob("scripts/install/*/install.ps1")) + sorted(REPO_ROOT.glob("scripts/uninstall/*/uninstall.ps1"))


class PowerShellScriptTests(unittest.TestCase):
    def test_every_script_is_covered(self) -> None:
        self.assertEqual(len(SCRIPTS), 20)

    def test_python_candidate_must_actually_run(self) -> None:
        # The WindowsApps python3/python stubs pass Get-Command but exit 9009,
        # which made every installer fail on a machine with a real Python too.
        for script in SCRIPTS:
            text = script.read_text(encoding="utf-8")
            with self.subTest(script=script.relative_to(REPO_ROOT).as_posix()):
                self.assertIn('& $Cand -c "import sys"', text)
                self.assertRegex(text, r"if \(\$LASTEXITCODE -eq 0\) \{ \$PythonCmd = \$Cand; break \}")
                self.assertNotRegex(text, r"SilentlyContinue\) \{ \$PythonCmd = \$Cand; break \}")

    def test_hermes_prefers_the_windows_home(self) -> None:
        for name in ("install/hermes/install.ps1", "uninstall/hermes/uninstall.ps1"):
            text = (REPO_ROOT / "scripts" / name).read_text(encoding="utf-8")
            with self.subTest(script=name):
                self.assertRegex(text, r'elseif \(Test-Path "\$env:LOCALAPPDATA\\hermes"\)')


if __name__ == "__main__":
    unittest.main()
