import json
import unittest
from scripts.arc3_upstream_license_audit import inspect, MODEL_IDS, INPUTS, GITHUB_REPO

def fixture(license=None, paths=()):
    root = f"https://api.github.com/repos/{GITHUB_REPO}"
    data = {
        root: {"default_branch": "main", "license": license},
        root + "/git/trees/main?recursive=1": {
            "tree": [{"path": p, "type": "blob"} for p in paths], "truncated": False
        },
    }
    for item in MODEL_IDS:
        data["https://huggingface.co/api/models/" + item] = {
            "sha": "example-sha", "cardData": {"license": "apache-2.0"}
        }
    return data

class UpstreamLicenseAuditTests(unittest.TestCase):
    def test_missing_tufa_root_license_stays_unverified(self):
        src = fixture(paths=("README.md","ARC3-Inference/pyproject.toml"))
        report = inspect(fetch=lambda url: src[url],timestamp="2026-10-12T00:00:00Z")
        self.assertEqual(report["status"], "PARTIAL")
        checks = {x["component"]: x for x in report["checks"]}
        self.assertEqual(checks["tufa_github_source"]["status"], "UNVERIFIED")
        self.assertEqual(checks["hf_model:" + MODEL_IDS[0]]["status"], "PASS")
        self.assertEqual(checks["hf_model:" + MODEL_IDS[1]]["status"], "PASS")
        for ds in INPUTS:
            self.assertEqual(checks["kaggle_dataset:" + ds]["status"], "UNVERIFIED")
        self.assertEqual(report["checked_utc"], "2026-10-12T00:00:00Z")

    def test_public_repo_license_does_not_prove_dataset(self):
        src = fixture(license={"spdx_id":"MIT"},paths=("LICENSE", "README.md"))
        report = inspect(fetch=lambda url: src[url])
        c = {x["component"]: x for x in report["checks"]}
        self.assertEqual(c["tufa_github_source"]["status"], "PARTIAL")
        self.assertEqual(c["kaggle_dataset:" + INPUTS[0]]["status"], "UNVERIFIED")

    def test_missing_model_metadata_is_not_claimed_pass(self):
        src = fixture()
        src["https://huggingface.co/api/models/" + MODEL_IDS[0]]["cardData"]={"license":"unknown"}
        report=inspect(fetch=lambda url: src[url])
        c={x["component"]:x for x in report["checks"]}
        self.assertEqual(c["hf_model:" + MODEL_IDS[0]]["status"],"UNVERIFIED")

    def test_network_failure_fails_closed(self):
        report=inspect(fetch=lambda _url: (_ for _ in ()).throw(ValueError("unavailable")))
        self.assertEqual(report["status"], "PARTIAL")
        self.assertTrue(all(x["status"] != "PASS" for x in report["checks"]
                            if x["component"].startswith("hf_model:")))

    def test_truncated_tree_cannot_prove_license(self):
        src=fixture(license={"spdx_id":"Apache-2.0"},paths=("LICENSE",))
        key=f"https://api.github.com/repos/{GITHUB_REPO}/git/trees/main?recursive=1"
        src[key]["truncated"]=True
        report=inspect(fetch=lambda url: src[url])
        c={x["component"]:x for x in report["checks"]}
        self.assertEqual(c["tufa_github_source"]["status"],"UNVERIFIED")

    def test_metadata_is_explicitly_not_snapshot_proof(self):
        src=fixture()
        report=inspect(fetch=lambda url: src[url])
        self.assertEqual(report["policy"],"PUBLIC_LICENSE_METADATA_IS_NOT_KAGGLE_SNAPSHOT_PROOF")
        model=[x for x in report["checks"] if x["component"]=="hf_model:"+MODEL_IDS[0]][0]
        self.assertIn("NOT verified",model["detail"])

if __name__ == "__main__":
    unittest.main()
