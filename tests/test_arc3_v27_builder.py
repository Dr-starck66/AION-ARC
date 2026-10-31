"""Static regression checks for ASTRA GPU v2.7 challenger.
No competition score is claimed by these tests.
"""
import ast
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_arc3_gpu_challenger.py"


class TestAionGPUChallenger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("aion_v27_builder", BUILDER)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        cls.notebook = mod.build()

    def test_cell_count_and_source_integrity(self):
        cells = [c for c in self.notebook["cells"] if c["cell_type"] == "code"]
        self.assertEqual(len(cells), 17)
        for i, c in enumerate(cells):
            source = "".join(c["source"])
            compile(source, "candidate_" + str(i), "exec",
                    flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)

    def test_async_top_level_corrected(self):
        sources = ["".join(c["source"]) for c in self.notebook["cells"]
                   if c["cell_type"] == "code"]
        self.assertEqual(sum("PyCF_ALLOW_TOP_LEVEL_AWAIT" in s for s in sources), 1)

    def test_offline_and_gpu_inputs(self):
        config = self.notebook["metadata"]["kaggle"]
        self.assertFalse(config["enable_internet"])
        self.assertTrue(config["enable_gpu"])
        self.assertEqual(config["competition_sources"], ["arc-prize-2026-arc-agi-3"])
        self.assertEqual(len(config["dataset_sources"]), 3)

    def test_preflight_and_rerun_gating(self):
        codes = ["".join(c["source"]) for c in self.notebook["cells"]
                 if c["cell_type"] == "code"]
        self.assertIn("submission.parquet", codes[0])
        self.assertIn("KAGGLE_IS_COMPETITION_RERUN", codes[0])
        self.assertTrue(all("if TRUE_RERUN else None" in s for s in codes[1:]))
        self.assertEqual(self.notebook["metadata"]["astra"]["status"], "UNVERIFIED_KAGGLE")


if __name__ == "__main__":
    unittest.main()
