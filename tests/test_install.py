from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
INSTALL_SH = ROOT / "install.sh"
INSTALL_PY = ROOT / "install.py"


class InstallerTests(unittest.TestCase):
    def run_install(self, target: Path | None, *args: str, env: dict | None = None, use_sh: bool = True):
        cmd = [str(INSTALL_SH)] if use_sh else [sys.executable, str(INSTALL_PY)]
        cmd.extend(args)
        if target is not None:
            cmd.append(str(target))
        return subprocess.run(cmd, text=True, capture_output=True, env=env)

    def test_preserves_existing_agents_and_installs_both_hosts(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "project"
            target.mkdir()
            (target / "AGENTS.md").write_text("# User rules\nKeep this.\n", encoding="utf-8")
            r = self.run_install(target)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("Keep this.", (target / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertTrue((target / ".agents/skills/faultline-break-sweep/SKILL.md").is_file())
            self.assertTrue((target / ".agents/agents/faultline-runtime-breaker.md").is_file())
            self.assertTrue((target / ".opencode/agents/faultline-orchestrator.md").is_file())

    def test_refuses_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "project"
            self.assertEqual(self.run_install(target).returncode, 0)
            r = self.run_install(target)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("already exists", r.stderr)

    def test_force_refreshes_faultline_block_and_preserves_unrelated_rules(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "project"
            self.assertEqual(self.run_install(target).returncode, 0)
            agents = target / "AGENTS.md"
            agents.write_text(agents.read_text(encoding="utf-8") + "\n# Later user addition\nKeep too.\n", encoding="utf-8")
            r = self.run_install(target, "--force")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            txt = agents.read_text(encoding="utf-8")
            self.assertEqual(txt.count("<!-- faultline:start -->"), 1)
            self.assertIn("Keep too.", txt)

    def test_unmatched_start_marker_fails(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "project"
            target.mkdir()
            (target / "AGENTS.md").write_text("# Corrupt\n<!-- faultline:start -->\nMissing end\n", encoding="utf-8")
            r = self.run_install(target, "--force")
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("unmatched Faultline start marker", r.stderr)

    def test_host_agent_options(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "project"
            r = self.run_install(target, "--no-antigravity-agents")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertFalse((target / ".agents/agents").exists())
            self.assertTrue((target / ".opencode/agents/faultline-orchestrator.md").exists())

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "project"
            r = self.run_install(target, "--no-opencode")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue((target / ".agents/agents/faultline-runtime-breaker.md").exists())
            self.assertFalse((target / ".opencode/agents").exists())

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "project"
            r = self.run_install(target, "--no-antigravity")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertFalse((target / ".agents").exists())
            self.assertFalse((target / "AGENTS.md").exists())
            self.assertTrue((target / ".opencode/agents/faultline-orchestrator.md").exists())

    def test_auto_detection_github_copilot(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "project"
            (target / ".github").mkdir(parents=True)
            r = self.run_install(target)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            copilot_file = target / ".github" / "copilot-instructions.md"
            self.assertTrue(copilot_file.is_file())
            self.assertIn("<!-- faultline:start -->", copilot_file.read_text(encoding="utf-8"))

    def test_auto_detection_cursor(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "project"
            (target / ".cursor").mkdir(parents=True)
            r = self.run_install(target)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            cursor_rule = target / ".cursor" / "rules" / "faultline.mdc"
            self.assertTrue(cursor_rule.is_file())
            self.assertIn("Faultline Adversarial Engineering Gate", cursor_rule.read_text(encoding="utf-8"))

    def test_auto_detection_claude(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "project"
            (target / ".claude").mkdir(parents=True)
            r = self.run_install(target)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue((target / ".claude/skills/faultline-preflight/SKILL.md").is_file())
            self.assertTrue((target / ".claude/agents/faultline-runtime-breaker.md").is_file())
            claude_md = target / "CLAUDE.md"
            self.assertTrue(claude_md.is_file())
            self.assertIn("<!-- faultline:start -->", claude_md.read_text(encoding="utf-8"))

    def test_auto_detection_kiro(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "project"
            (target / ".kiro").mkdir(parents=True)
            r = self.run_install(target)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue((target / ".kiro/skills/faultline-preflight/SKILL.md").is_file())
            self.assertTrue((target / ".kiro/agents/faultline-runtime-breaker.md").is_file())
            self.assertTrue((target / ".kiro/hooks/faultline-gate.json").is_file())

    def test_all_flag_installs_all_hosts(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "project"
            r = self.run_install(target, "--all")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue((target / ".agents/skills/faultline-preflight/SKILL.md").is_file())
            self.assertTrue((target / ".claude/skills/faultline-preflight/SKILL.md").is_file())
            self.assertTrue((target / ".kiro/skills/faultline-preflight/SKILL.md").is_file())
            self.assertTrue((target / ".cursor/rules/faultline.mdc").is_file())
            self.assertTrue((target / ".github/copilot-instructions.md").is_file())
            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertTrue((target / "CLAUDE.md").is_file())

    def test_dry_run_makes_no_changes(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "project"
            target.mkdir()
            r = self.run_install(target, "--dry-run")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("Would install skills:", r.stdout)
            self.assertEqual(list(target.iterdir()), [])

    def test_global_scope_install(self):
        with tempfile.TemporaryDirectory() as td:
            fake_home = Path(td) / "home"
            fake_home.mkdir()
            custom_env = os.environ.copy()
            custom_env["HOME"] = str(fake_home)
            r = self.run_install(None, "--global", env=custom_env, use_sh=False)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue((fake_home / ".agents/skills/faultline-preflight/SKILL.md").is_file())
            self.assertTrue((fake_home / ".claude/skills/faultline-preflight/SKILL.md").is_file())
            self.assertTrue((fake_home / ".kiro/skills/faultline-preflight/SKILL.md").is_file())
            self.assertTrue((fake_home / ".agents/agents/faultline-runtime-breaker.md").is_file())
            self.assertTrue((fake_home / ".claude/agents/faultline-runtime-breaker.md").is_file())
            self.assertTrue((fake_home / ".kiro/agents/faultline-runtime-breaker.md").is_file())


if __name__ == "__main__":
    unittest.main()
