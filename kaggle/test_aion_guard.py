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

    def test_object_motion_changes_signature(self):
        a = node("R","same-shape",4,[[20,20],[20,21],[21,21],[21,20]])
        b = node("R","same-shape",4,[[20,21],[20,22],[21,22],[21,21]])
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

    def test_information_gain_prefers_discriminating_probe(self):
        h1 = types.SimpleNamespace(name="h1", predict=lambda s,a: s if a=="NOOP" else s+1)
        h2 = types.SimpleNamespace(name="h2", predict=lambda s,a: s if a=="NOOP" else s+2)
        ranked = g.aion_information_gain(["NOOP","PROBE"], [h1,h2], 0)
        self.assertEqual(ranked[0]["action"], "PROBE")
        self.assertGreater(ranked[0]["information_gain"], ranked[1]["information_gain"])
        self.assertEqual(g.aion_choose_probe(["NOOP","PROBE"], [h1,h2], 0), "PROBE")

    def test_probe_selector_penalizes_risk(self):
        h1 = types.SimpleNamespace(name="h1", predict=lambda s,a: a)
        h2 = types.SimpleNamespace(name="h2", predict=lambda s,a: a if a=="SAFE" else "OTHER")
        choice = g.aion_choose_probe(["SAFE","RISKY"], [h1,h2], 0, risk=lambda a: 2.0 if a=="RISKY" else 0.0)
        self.assertEqual(choice, "SAFE")

    def test_bfs_planner_finds_short_plan(self):
        result = g.aion_bfs_plan(
            0,
            [1,2],
            lambda state, action: state + action,
            lambda state: state == 5,
            max_nodes=30,
            max_depth=5,
        )
        self.assertEqual(result["status"], "FOUND")
        self.assertEqual(sum(result["plan"]), 5)

    def test_compact_memory_learns_success_and_failure(self):
        a=Frame([node("R","a",1,[[1,1],[1,1],[1,1],[1,1]])])
        b=Frame([node("R","b",1,[[2,2],[2,2],[2,2],[2,2]])])
        good=types.SimpleNamespace(action="ACTION1", before_frame=a, after_frame=b, result={"level_completed":True,"reward":1})
        inert=types.SimpleNamespace(action="ACTION2", before_frame=b, after_frame=b, result={})
        mem=g.aion_compact_memory([good,inert])
        self.assertEqual(mem["confirmed_effects"]["ACTION1"], 1)
        self.assertEqual(mem["inert_actions"]["ACTION2"], 1)
        self.assertTrue(mem["progress_actions"])

    def test_ablation_profiles_keep_baseline_and_balanced(self):
        base=g.aion_ablation_profile("duck_baseline")
        full=g.aion_ablation_profile("balanced")
        self.assertFalse(base["prediction_gate"])
        self.assertTrue(full["prediction_gate"])
        self.assertTrue(full["compact_memory"])
        self.assertTrue(full["world_model"])

    def test_efficiency_governor_detects_action_waste(self):
        f = Frame([])
        inert = types.SimpleNamespace(action="ACTION5", before_frame=f, after_frame=f, result={})
        rows = [inert for _ in range(8)]
        diag = g.aion_action_efficiency(rows)
        self.assertTrue(diag["needs_model_escalation"])
        self.assertEqual(diag["inert_rate"], 1.0)
        self.assertTrue(g.aion_probe_budget(rows, max_inert=3, window=8)["exhausted"])

    def test_shortest_plan_prefers_minimum_actions(self):
        graph = {0:[("A",1),("B",2)], 1:[("C",3)], 2:[("D",4)], 4:[("E",3)], 3:[]}
        out = g.aion_shortest_plan(0, lambda s:s==3, lambda s:graph[s])
        self.assertEqual(out["status"], "FOUND")
        self.assertEqual(out["plan"], ["A","C"])
        self.assertEqual(out["actions"], 2)

    def test_efficiency_gate_blocks_zero_value_probe_after_budget(self):
        f = Frame([])
        inert = types.SimpleNamespace(action="ACTION5", before_frame=f, after_frame=f, result={})
        rows = [inert for _ in range(4)]
        h1 = types.SimpleNamespace(predict=lambda s,a: 1)
        h2 = types.SimpleNamespace(predict=lambda s,a: 1)
        out = g.aion_efficiency_gate("ACTION5", rows, [h1,h2], 0)
        self.assertFalse(out["allowed"])

    def test_host_stop_on_terminal_transition(self):
        out = g.aion_host_should_stop("a", "b", "ACTION1", {"game_over": True})
        self.assertTrue(out["stop"])
        self.assertIn("terminal_transition", out["reasons"])

    def test_host_stop_on_known_negative_edge(self):
        edge = (repr("a"), "ACTION2", repr("b"))
        out = g.aion_host_should_stop("a", "b", "ACTION2", {}, negative_edges={edge})
        self.assertTrue(out["stop"])
        self.assertIn("known_negative_edge", out["reasons"])

    def test_host_stop_on_unexpected_cycle(self):
        out = g.aion_host_should_stop("a", "old", "ACTION3", {}, seen_signatures={"old"})
        self.assertTrue(out["stop"])
        self.assertIn("unexpected_state_cycle", out["reasons"])

    def test_host_allows_novel_nonterminal_transition(self):
        out = g.aion_host_should_stop("a", "b", "ACTION4", {}, seen_signatures={"a"})
        self.assertFalse(out["stop"])

    def test_host_stop_on_level_change_even_without_level_completed_flag(self):
        out = g.aion_host_should_stop(
            "a",
            "b",
            "ACTION1",
            {"aion_before_level": 2, "aion_after_level": 3, "level_completed": False},
        )
        self.assertTrue(out["stop"])
        self.assertIn("level_change", out["reasons"])

if __name__ == "__main__":
    unittest.main()
