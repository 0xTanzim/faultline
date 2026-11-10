from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_report.py"
FIXTURE = ROOT / "examples" / "sample-preflight-report.md"


class ValidatorTests(unittest.TestCase):
    def run_validator(self, report: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(report)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_valid_fixture_passes(self) -> None:
        result = self.run_validator(FIXTURE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS:", result.stdout)

    def test_missing_given_when_then_fails(self) -> None:
        text = FIXTURE.read_text(encoding="utf-8")
        text = "\n".join(
            line for line in text.splitlines()
            if not line.lstrip().startswith("- **Then**")
        )
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "bad.md"
            report.write_text(text, encoding="utf-8")
            result = self.run_validator(report)
        self.assertEqual(result.returncode, 1)
        self.assertIn("acceptance test must contain non-empty Then", result.stdout)

    def test_duplicate_risk_ids_fail(self) -> None:
        text = FIXTURE.read_text(encoding="utf-8")
        text += "\n### FL-001 — Duplicate example\n"
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "duplicate.md"
            report.write_text(text, encoding="utf-8")
            result = self.run_validator(report)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Duplicate risk IDs", result.stdout)


if __name__ == "__main__":
    unittest.main()
