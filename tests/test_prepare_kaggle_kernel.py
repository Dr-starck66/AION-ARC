import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_kaggle_kernel import ROOT, build


class KaggleKernelPackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.output = Path(self.tmp.name) / "out"
    def tearDown(self):
        self.tmp.cleanup()

    def test_champion_is_private_offline_and_digest_matches(self):
        report = build("aion_public", "champion", self.output)
        self.assertEqual(report["status"], "PACKAGE_ONLY_NOT_SUBMITTED")
        self.assertEqual(report["version"], "2.5.0")
        self.assertEqual(report["official_score"], "UNVERIFIED")
        self.assertTrue(report["legal_notices_embedded"])
        self.assertEqual(report["upstream_bundle_license"], "UNVERIFIED")
        notebook = json.loads((self.output / "submission.ipynb").read_text())
        notices = [c for c in notebook["cells"] if c.get("id") == "aion-license-notice"]
        self.assertEqual(len(notices), 1)
        words = "".join(notices[0]["source"])
        self.assertIn("MIT No Attribution", words)
        self.assertIn("END OF TERMS AND CONDITIONS", words)
        self.assertIn("UNVERIFIED", words)
        self.assertIn("Tufa Labs", words)
        meta = json.loads((self.output / "kernel-metadata.json").read_text())
        self.assertTrue(meta["is_private"])
        self.assertFalse(meta["enable_internet"])
        self.assertTrue(meta["enable_gpu"])
        self.assertEqual(meta["competition_sources"], ["arc-prize-2026-arc-agi-3"])
        self.assertEqual(meta["dataset_sources"], json.loads((ROOT / "kaggle/SUBMISSION_MANIFEST.json").read_text())["required_kaggle_inputs"])
        data = (self.output / "submission.ipynb").read_bytes()
        self.assertEqual(report["notebook_sha256"], hashlib.sha256(data).hexdigest())

    def test_challenger_is_distinct_and_never_auto_promoted(self):
        out = build("aion_public", "challenger", self.output)
        self.assertEqual(out["version"], "2.6.0-experimental")
        self.assertEqual(out["official_score"], "UNVERIFIED")
        notebook = json.loads((self.output / "submission.ipynb").read_text())
        self.assertIn("aion-v26-recovery-policy", [x.get("id") for x in notebook["cells"]])

    def test_secret_instead_of_username_is_rejected(self):
        for bad in ("", "token/secret", "kaggle_key:foo", "../escape", "x" * 100, "KAGGLE_USERNAME=abc", "KGAT_abcdefghijklmnopqrstuvwxyz012345"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                build(bad, "champion", self.output)
        self.assertFalse(self.output.exists())

    def test_first_real_code_cell_and_original_order_preserved(self):
        build("aion_public", "champion", self.output)
        baseline = json.loads((ROOT / "kaggle/AION-ARC-v2.5-generalization.ipynb").read_text())
        packaged = json.loads((self.output / "submission.ipynb").read_text())
        base_codes = [c.get("id") for c in baseline["cells"] if c.get("cell_type") == "code"]
        package_codes = [c.get("id") for c in packaged["cells"] if c.get("cell_type") == "code"]
        self.assertEqual(base_codes, package_codes)

    def test_missing_apache_license_does_not_fake_ready_package(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for path in ("LICENSE", "THIRD_PARTY_NOTICES.md",
                         "kaggle/SUBMISSION_MANIFEST.json", "kaggle/AION-ARC-v2.5-generalization.ipynb"):
                dst = root / path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / path, dst)
            with self.assertRaises(FileNotFoundError):
                build("aion_public", "champion", self.output, root=root)
            self.assertFalse((self.output / "submission.ipynb").exists())

    def test_refuses_overwriting_a_package(self):
        build("aion_public", "champion", self.output)
        with self.assertRaises(FileExistsError):
            build("aion_public", "challenger", self.output)

if __name__ == "__main__":
    unittest.main()
