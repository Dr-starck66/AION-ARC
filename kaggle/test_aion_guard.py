import importlib.util
import pathlib
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("aion_guard", ROOT / "aion_guard_reference.py")
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

def node(color, h, pixels, boundary, children=None):
    return {"color": color, "hash": h, "pixels": pixels, "boundary": boundary, "children": children or []}

class Frame:
    def __init__(self, nodes, shape=(64,64), level=1):
        self.segmentation = {"nodes": nodes, "adjacency_list": []}
        self.shape = shape
        self.level = level

class AionGuardTests(unittest.TestCase):
    def test_hud_strip_excluded_from_signature(self):
        hud1 = node("A","hud1",64,[[0,0],[0,63],[1,63],[1,0]])
        hud2 = node("B","hud2",63,[[0,0],[0,62],[1,62],[1,0]])
        obj = node("R","obj",4,[[20,20],[20,21],[21,21],[21,20]])
        self.assertEqual(g.aion_frame_signature(Frame([hud1,obj])), g.aion_frame_signature(Frame([hud2,obj])))

    def test_real_object_change_changes_signature(self):
        a = node("R","obj",4,[[20,20],[20,21],[21,21],[21,20]])
        b = node("R","obj2",5,[[20,20],[20,22],[21,22],[21,20]])
        self.assertNotEqual(g.aion_frame_signature(Frame([a])), g.aion_frame_signature(Frame([b])))

    def test_prediction_mismatch_detected(self):
        mm = g.aion_expectation_mismatches({"expect_change": True}, {"board_changed": False}, Frame([]))
        self.assertTrue(mm)

    def test_reset_warning_when_undo_available(self):
        warnings = g.aion_plan_audit([{"action":"RESET"}], ["RESET","ACTION7"])
        self.assertTrue(any("ACTION7" in w for w in warnings))

    def test_repeated_inert_probe_warns(self):
        f = Frame([])
        tr = types.SimpleNamespace(action="ACTION5", before_frame=f, after_frame=f, result={"board_changed":False})
        warnings = g.aion_plan_audit([{"action":"ACTION5"}], ["ACTION5"], [tr], {})
        self.assertTrue(any("inert" in w for w in warnings))

if __name__ == "__main__":
    unittest.main()
