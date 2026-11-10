from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SkillTests(unittest.TestCase):
    def test_skill_validator(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_skills.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_build_adapters_check(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_adapters.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_all_host_adapters_reference_only_current_roles(self):
        with open(ROOT / "definitions" / "specialists.json", "r", encoding="utf-8") as f:
            specs = json.load(f)
        expected_roles = {spec["name"] for spec in specs}
        self.assertEqual(len(expected_roles), 6)

        ag_roles = {p.stem for p in (ROOT / ".agents" / "agents").glob("*.md")}
        oc_roles = {p.stem for p in (ROOT / ".opencode" / "agents").glob("*.md")}
        claude_roles = {p.stem for p in (ROOT / ".claude" / "agents").glob("*.md")}
        kiro_roles = {p.stem for p in (ROOT / ".kiro" / "agents").glob("*.md")}

        self.assertEqual(ag_roles, expected_roles)
        self.assertEqual(oc_roles - {"faultline-orchestrator"}, expected_roles)
        self.assertEqual(claude_roles, expected_roles)
        self.assertEqual(kiro_roles, expected_roles)

        orch = (ROOT / ".opencode" / "agents" / "faultline-orchestrator.md").read_text(encoding="utf-8")
        for role in expected_roles:
            self.assertIn(f"resource: {role}", orch)

    def test_adapters_reference_canonical_and_host_protocol_paths(self):
        claude_agent = (ROOT / ".claude" / "agents" / "faultline-runtime-breaker.md").read_text(encoding="utf-8")
        self.assertIn("skills/faultline-preflight/references/subagent-protocol.md", claude_agent)
        self.assertIn(".claude/skills/faultline-preflight/references/subagent-protocol.md", claude_agent)

        kiro_agent = (ROOT / ".kiro" / "agents" / "faultline-runtime-breaker.md").read_text(encoding="utf-8")
        self.assertIn("skills/faultline-preflight/references/subagent-protocol.md", kiro_agent)
        self.assertIn(".kiro/skills/faultline-preflight/references/subagent-protocol.md", kiro_agent)

    def test_opencode_uses_v2_permissions_not_v1_permission(self):
        for p in (ROOT / ".opencode" / "agents").glob("*.md"):
            txt = p.read_text(encoding="utf-8")
            self.assertIn("permissions:", txt, p)
            self.assertNotRegex(txt, r"(?m)^permission:")

    def test_canonical_skills_and_symlink(self):
        skills_dir = ROOT / "skills"
        self.assertTrue(skills_dir.is_dir())
        expected_skills = {"faultline-preflight", "faultline-break-sweep", "faultline-spec-audit"}
        actual_skills = {d.name for d in skills_dir.iterdir() if d.is_dir()}
        self.assertTrue(expected_skills.issubset(actual_skills))

        agents_skills = ROOT / ".agents" / "skills"
        self.assertTrue(agents_skills.is_symlink())
        self.assertEqual(agents_skills.resolve(), skills_dir.resolve())


if __name__ == "__main__":
    unittest.main()
