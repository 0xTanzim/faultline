from __future__ import annotations
import subprocess, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INSTALL=ROOT/'install.sh'
class InstallerTests(unittest.TestCase):
    def run_install(self, target: Path, *args: str):
        return subprocess.run([str(INSTALL),*args,str(target)],text=True,capture_output=True)
    def test_preserves_existing_agents_and_installs_both_hosts(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'project'; target.mkdir()
            (target/'AGENTS.md').write_text('# User rules\nKeep this.\n')
            r=self.run_install(target)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertIn('Keep this.',(target/'AGENTS.md').read_text())
            self.assertTrue((target/'.agents/skills/faultline-break-sweep/SKILL.md').is_file())
            self.assertTrue((target/'.agents/agents/faultline-runtime-breaker.md').is_file())
            self.assertTrue((target/'.opencode/agents/faultline-orchestrator.md').is_file())
    def test_refuses_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'project'
            self.assertEqual(self.run_install(target).returncode,0)
            r=self.run_install(target)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('already exists',r.stderr)
    def test_force_refreshes_faultline_block_and_preserves_unrelated_rules(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'project'
            self.assertEqual(self.run_install(target).returncode,0)
            agents=target/'AGENTS.md'
            agents.write_text(agents.read_text()+'\n# Later user addition\nKeep too.\n')
            r=self.run_install(target,'--force')
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            txt=agents.read_text()
            self.assertEqual(txt.count('<!-- faultline:start -->'),1)
            self.assertIn('Keep too.',txt)
    def test_host_agent_options(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'project'
            r=self.run_install(target,'--no-antigravity-agents')
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertFalse((target/'.agents/agents').exists())
            self.assertTrue((target/'.opencode/agents/faultline-orchestrator.md').exists())
if __name__=='__main__': unittest.main()
