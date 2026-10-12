import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.arc3_submission_evidence_gate import ROOT, audit


class SubmissionEvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel in ("kaggle/SUBMISSION_MANIFEST.json",
                    "kaggle/AION-ARC-v2.5-generalization.ipynb",
                    "kaggle/AION-ARC-v2.6-recovery.ipynb",
                    "docs/UPSTREAM-ATTRIBUTION-AND-LICENSE.md",
                    "THIRD_PARTY_LICENSES/Apache-2.0.txt"):
            destination = self.root / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, destination)

    def tearDown(self):
        self.tmp.cleanup()

    def test_unlicensed_static_content_is_fail_not_competition_pass(self):
        result = audit(self.root)
        self.assertEqual(result["status"], "FAIL", result)
        statuses = {c["check"]: c["status"] for c in result["checks"]}
        self.assertEqual(statuses["manifest"], "PASS")
        self.assertEqual(statuses["challenger_notebook"], "PASS")
        self.assertEqual(statuses["meaningful_challenger_delta"], "PASS")
        self.assertEqual(statuses["official_kaggle_submission"], "UNVERIFIED")
        self.assertEqual(statuses["gpu_runtime"], "UNVERIFIED")
        self.assertEqual(statuses["paired_real_gameplay"], "UNVERIFIED")
        self.assertEqual(statuses["project_license"], "FAIL")

    def test_missing_manifest_is_fail(self):
        (self.root / "kaggle/SUBMISSION_MANIFEST.json").unlink()
        self.assertEqual(audit(self.root)["status"], "FAIL")

    def test_false_hidden_score_claim_is_fail(self):
        file = self.root / "kaggle/SUBMISSION_MANIFEST.json"
        m = json.loads(file.read_text())
        m["official_hidden_score_status"] = "PASS"
        file.write_text(json.dumps(m))
        self.assertEqual(audit(self.root)["status"], "FAIL")

    def test_removed_v26_recovery_patch_is_fail(self):
        file = self.root / "kaggle/AION-ARC-v2.6-recovery.ipynb"
        notebook = json.loads(file.read_text())
        notebook["cells"] = [c for c in notebook["cells"] if c.get("id") != "aion-v26-recovery-policy"]
        file.write_text(json.dumps(notebook))
        self.assertEqual(audit(self.root)["status"], "FAIL")

    def test_wrong_license_is_fail(self):
        (self.root / "LICENSE").write_text("Apache License, Version 2.0")
        checks = {x["check"]: x["status"] for x in audit(self.root)["checks"]}
        self.assertEqual(checks["project_license"], "FAIL")

    def test_authorized_mit_zero_scope_is_pass_but_external_rights_unverified(self):
        for rel in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
            shutil.copy2(ROOT / rel, self.root / rel)
        report = audit(self.root)
        checks = {x["check"]: x["status"] for x in report["checks"]}
        self.assertEqual(checks["project_license"], "PASS")
        self.assertEqual(checks["third_party_rights"], "UNVERIFIED")
        self.assertEqual(report["status"], "PARTIAL")

    def test_missing_scoping_notice_blocks_license(self):
        shutil.copy2(ROOT / "LICENSE", self.root / "LICENSE")
        checks = {x["check"]: x["status"] for x in audit(self.root)["checks"]}
        self.assertEqual(checks["project_license"], "FAIL")

    def test_missing_apache_license_text_is_fail(self):
        (self.root / "THIRD_PARTY_LICENSES/Apache-2.0.txt").unlink()
        checks = {x["check"]: x["status"] for x in audit(self.root)["checks"]}
        self.assertEqual(checks["apache_license_notice"], "FAIL")
        self.assertEqual(audit(self.root)["status"], "FAIL")

    def test_canonical_apache_notice_does_not_authorize_tufa_bundle(self):
        for rel in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
            shutil.copy2(ROOT / rel, self.root / rel)
        checks = {x["check"]: x["status"] for x in audit(self.root)["checks"]}
        self.assertEqual(checks["apache_license_notice"], "PASS")
        self.assertEqual(checks["third_party_rights"], "UNVERIFIED")

    def test_missing_upstream_notices_is_fail(self):
        (self.root / "docs/UPSTREAM-ATTRIBUTION-AND-LICENSE.md").unlink()
        self.assertEqual(audit(self.root)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
