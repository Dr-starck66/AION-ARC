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

    def test_information_gain_prefers_disagreement(self):
        ranked = g.aion_information_gain({"boring":[1,1], "probe":[1,2]})
        self.assertEqual(ranked[0][0], "probe")
        self.assertGreater(ranked[0][1], ranked[1][1])

    def test_prediction_match_partial_dict(self):
        self.assertTrue(g.aion_prediction_match({"x":1}, {"x":1,"y":2}))
        self.assertFalse(g.aion_prediction_match({"x":2}, {"x":1,"y":2}))

    def test_state_graph_detects_conflict(self):
        a=Frame([node("R","a",1,[[1,1],[1,1],[1,1],[1,1]])])
        b=Frame([node("R","b",1,[[2,2],[2,2],[2,2],[2,2]])])
        c=Frame([node("R","c",1,[[3,3],[3,3],[3,3],[3,3]])])
        t1=types.SimpleNamespace(action="ACTION1", before_frame=a, after_frame=b, result={})
        t2=types.SimpleNamespace(action="ACTION1", before_frame=a, after_frame=c, result={})
        graph=g.aion_state_graph([t1,t2])
        self.assertTrue(graph["conflicts"])

    def test_repeated_inert_probe_warns(self):
        f = Frame([])
        tr = types.SimpleNamespace(action="ACTION5", before_frame=f, after_frame=f, result={"board_changed":False})
        warnings = g.aion_plan_audit([{"action":"ACTION5"}], ["ACTION5"], [tr], {})
        self.assertTrue(any("inert" in w for w in warnings))

if __name__ == "__main__":
    unittest.main()
