from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_adapters import (
    load_definitions,
    validate_definitions,
    build_host_adapters,
    render_claude,
    render_kiro,
    render_opencode,
    render_opencode_orchestrator,
    RENDERERS,
)


class SkillTests(unittest.TestCase):
    def test_skill_validator(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_skills.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_build_adapters_check(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_adapters.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_no_duplicate_host_folders_in_repo_root(self):
        """Strict DRY invariant: no static generated host adapter directories in git repository root."""
        self.assertFalse((ROOT / ".claude").exists(), ".claude should not exist in repo root")
        self.assertFalse((ROOT / ".kiro").exists(), ".kiro should not exist in repo root")
        self.assertFalse((ROOT / ".opencode").exists(), ".opencode should not exist in repo root")
        self.assertFalse((ROOT / ".cursor").exists(), ".cursor should not exist in repo root")

    def test_dynamic_adapter_generation_for_all_hosts(self):
        specs = load_definitions(ROOT / "definitions" / "specialists.json")
        expected_roles = {spec["name"] for spec in specs}
        self.assertEqual(len(expected_roles), 6)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            for host in ["antigravity", "opencode", "claude", "kiro"]:
                host_dir = tmppath / host
                files = build_host_adapters(host, host_dir, specs)
                file_stems = {f.stem for f in files}

                if host == "opencode":
                    self.assertEqual(file_stems - {"faultline-orchestrator"}, expected_roles)
                    orch = (host_dir / "faultline-orchestrator.md").read_text(encoding="utf-8")
                    for role in expected_roles:
                        self.assertIn(f"resource: {role}", orch)
                else:
                    self.assertEqual(file_stems, expected_roles)

    def test_adapters_reference_canonical_and_host_protocol_paths(self):
        specs = load_definitions(ROOT / "definitions" / "specialists.json")
        runtime_spec = next(s for s in specs if s["id"] == "runtime-breaker")

        claude_agent = render_claude(runtime_spec)
        self.assertIn("skills/faultline-preflight/references/subagent-protocol.md", claude_agent)
        self.assertIn(".claude/skills/faultline-preflight/references/subagent-protocol.md", claude_agent)

        kiro_agent = render_kiro(runtime_spec)
        self.assertIn("skills/faultline-preflight/references/subagent-protocol.md", kiro_agent)
        self.assertIn(".kiro/skills/faultline-preflight/references/subagent-protocol.md", kiro_agent)

    def test_opencode_uses_v2_permissions_not_v1_permission(self):
        specs = load_definitions(ROOT / "definitions" / "specialists.json")
        for s in specs:
            txt = render_opencode(s)
            self.assertIn("permissions:", txt)
            self.assertNotRegex(txt, r"(?m)^permission:")

        orch_txt = render_opencode_orchestrator()
        self.assertIn("permissions:", orch_txt)
        self.assertNotRegex(orch_txt, r"(?m)^permission:")

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
