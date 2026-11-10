from __future__ import annotations
import subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SkillTests(unittest.TestCase):
    def test_skill_validator(self):
        r=subprocess.run([sys.executable,str(ROOT/'scripts/validate_skills.py')],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
    def test_all_host_adapters_reference_only_current_roles(self):
        roles={p.stem for p in (ROOT/'.agents/agents').glob('*.md')}
        oc={p.stem for p in (ROOT/'.opencode/agents').glob('*.md')}
        self.assertEqual(roles,oc-{'faultline-orchestrator'})
        orch=(ROOT/'.opencode/agents/faultline-orchestrator.md').read_text()
        for role in roles: self.assertIn(f'resource: {role}',orch)
    def test_opencode_uses_v2_permissions_not_v1_permission(self):
        for p in (ROOT/'.opencode/agents').glob('*.md'):
            txt=p.read_text()
            self.assertIn('permissions:',txt,p)
            self.assertNotRegex(txt,r'(?m)^permission:')
if __name__=='__main__': unittest.main()
