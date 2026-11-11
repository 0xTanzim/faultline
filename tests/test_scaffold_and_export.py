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

from scripts.scaffold_report import scaffold_report
from scripts.validate_report import validate
from scripts.export_report import parse_report_to_dict, to_sarif


class ScaffoldAndExportTests(unittest.TestCase):
    def test_scaffolded_report_passes_validator(self):
        with tempfile.TemporaryDirectory() as td:
            out_file = Path(td) / "test-feature.md"
            scaffold_report(slug="test-feature", title="Test Feature Audit", output_path=out_file)
            self.assertTrue(out_file.is_file())

            # Validate that scaffolded skeleton passes validate_report with 0 errors
            res = validate(out_file)
            self.assertEqual(res, 0, "Scaffolded report must pass validation with exit code 0")

    def test_export_to_json_and_sarif(self):
        sample_path = ROOT / "examples" / "sample-preflight-report.md"
        data = parse_report_to_dict(sample_path)

        # JSON assertions
        self.assertEqual(data["slug"], "payment-retry")
        self.assertEqual(len(data["risks"]), 1)
        r0 = data["risks"][0]
        self.assertEqual(r0["id"], "FL-001")
        self.assertEqual(r0["severity"], "High")
        self.assertIn("acceptance_scenario", r0)
        self.assertIn("given", r0["acceptance_scenario"])

        # SARIF assertions
        sarif = to_sarif(data)
        self.assertEqual(sarif["version"], "2.1.0")
        self.assertIn("runs", sarif)
        run0 = sarif["runs"][0]
        self.assertEqual(run0["tool"]["driver"]["name"], "Faultline")
        self.assertEqual(len(run0["results"]), 1)
        res0 = run0["results"][0]
        self.assertEqual(res0["ruleId"], "FL-001")
        self.assertEqual(res0["level"], "error")


if __name__ == "__main__":
    unittest.main()
