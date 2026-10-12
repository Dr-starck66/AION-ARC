import ast
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "kaggle" / "AION-ARC-v2.6-recovery.ipynb"

SEED = '''def handle(compact_payload, host_mismatches, repeated_state, store, action_key):
            if bool(compact_payload.get("game_over")) or bool(host_mismatches):
                store.add(action_key)
            if repeated_state:
                host_mismatches.append("unexpected repeated semantic state")
            if host_mismatches:
                compact_payload["aion_host_stop"] = True
'''

class RecoveryPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = json.loads(NOTEBOOK.read_text())
        assert cls.nb["metadata"]["aion_arc"]["version"] == "2.6.0-experimental"
        assert cls.nb["metadata"]["aion_arc"]["status"] == "UNVERIFIED"
        cls.cells = {c["id"]: c for c in cls.nb["cells"]}
        ids = list(cls.cells)
        assert ids.index("aion-v24-persistent-host-memory") < ids.index("aion-v26-recovery-policy") < ids.index("10")
        src = "".join(cls.cells["aion-v26-recovery-policy"]["source"])
        ast.parse(src)
        for c in cls.nb["cells"]:
            if c["cell_type"] == "code":
                ast.parse("".join(c["source"]))
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "tool.py"
            p.write_text(SEED)
            exec(compile(src, "<aion-v26-recovery>", "exec"), {"tool_path": p})
            cls.generated = p.read_text()
        ast.parse(cls.generated)
        ns = {}
        exec(compile(cls.generated, "<patched-tool>", "exec"), ns)
        cls.handle = staticmethod(ns["handle"])

    def test_wrong_prediction_stops_current_plan_but_does_not_blacklist(self):
        payload, store, mismatches = {}, set(), ["expect_gameplay_change mismatch"]
        self.handle(payload, mismatches, False, store, ("state-a", "ACTION1"))
        self.assertEqual(store, set())
        self.assertTrue(payload.get("aion_host_stop"))

    def test_legitimate_state_revisit_is_diagnostic(self):
        payload, store, mismatches = {}, set(), []
        self.handle(payload, mismatches, True, store, ("state-a", "ACTION2"))
        self.assertEqual(mismatches, [])
        self.assertTrue(payload["aion_host_revisit"])
        self.assertFalse(payload.get("aion_host_stop", False))

    def test_terminal_success_does_not_blacklist(self):
        payload, store = {"game_over": True, "level_completed": True}, set()
        self.handle(payload, [], False, store, ("state-a", "ACTION3"))
        self.assertEqual(store, set())

    def test_verified_failure_blacklisted(self):
        payload, store = {"game_over": True, "level_completed": False, "run_complete": False}, set()
        self.handle(payload, [], False, store, ("state-a", "ACTION4"))
        self.assertEqual(store, {("state-a", "ACTION4")})

    def test_patch_requires_exact_upstream_anchors(self):
        patch = "".join(self.cells["aion-v26-recovery-policy"]["source"])
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "tool.py"
            p.write_text("no matching anchors")
            with self.assertRaises(RuntimeError):
                exec(compile(patch, "<aion-v26-recovery>", "exec"), {"tool_path": p})
            self.assertEqual(p.read_text(), "no matching anchors")

if __name__ == "__main__":
    unittest.main()
