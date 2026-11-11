from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
INSTALL_PY = ROOT / "install.py"


class UninstallTests(unittest.TestCase):
    def run_cmd(self, *args: str) -> subprocess.CompletedProcess:
        cmd = [sys.executable, str(INSTALL_PY)] + list(args)
        return subprocess.run(cmd, text=True, capture_output=True)

    def test_full_uninstall_cleans_files_and_preserves_user_rules(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "project"
            target.mkdir()

            # Create realistic user rules
            (target / "CLAUDE.md").write_text("# My Project Rules\nImportant custom policy.\n", encoding="utf-8")
            (target / "AGENTS.md").write_text("# Organization Standard\nStrict safety rules.\n", encoding="utf-8")
            github_dir = target / ".github"
            github_dir.mkdir()
            (github_dir / "copilot-instructions.md").write_text("# Copilot Custom Directives\nStrict typing.\n", encoding="utf-8")

            # 1. Install all integrations
            r_install = self.run_cmd("--all", str(target))
            self.assertEqual(r_install.returncode, 0, r_install.stderr)

            # Confirm installation
            self.assertTrue((target / ".agents/skills/faultline-preflight/SKILL.md").is_file())
            self.assertTrue((target / ".claude/agents/faultline-runtime-breaker.md").is_file())
            self.assertTrue((target / ".cursor/rules/faultline.mdc").is_file())
            self.assertIn("<!-- faultline:start -->", (target / "CLAUDE.md").read_text(encoding="utf-8"))

            # 2. Run uninstaller
            r_uninst = self.run_cmd("--uninstall", str(target))
            self.assertEqual(r_uninst.returncode, 0, r_uninst.stderr)

            # Confirm all Faultline assets removed
            self.assertFalse((target / ".agents").exists())
            self.assertFalse((target / ".claude").exists())
            self.assertFalse((target / ".kiro").exists())
            self.assertFalse((target / ".opencode").exists())
            self.assertFalse((target / ".cursor").exists())

            # Confirm user rules preserved without markers
            claude_txt = (target / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertIn("Important custom policy.", claude_txt)
            self.assertNotIn("<!-- faultline:start -->", claude_txt)

            agents_txt = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Strict safety rules.", agents_txt)
            self.assertNotIn("<!-- faultline:start -->", agents_txt)

            copilot_txt = (github_dir / "copilot-instructions.md").read_text(encoding="utf-8")
            self.assertIn("Strict typing.", copilot_txt)
            self.assertNotIn("<!-- faultline:start -->", copilot_txt)

    def test_uninstall_deletes_empty_rule_files(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "project"
            target.mkdir()

            # Install into project without prior rule files
            r_install = self.run_cmd(str(target))
            self.assertEqual(r_install.returncode, 0)
            self.assertTrue((target / "AGENTS.md").is_file())

            # Uninstall
            r_uninst = self.run_cmd("--uninstall", str(target))
            self.assertEqual(r_uninst.returncode, 0)

            # AGENTS.md had no prior user content, so it should be deleted cleanly
            self.assertFalse((target / "AGENTS.md").exists())
            self.assertFalse((target / ".agents").exists())


if __name__ == "__main__":
    unittest.main()
