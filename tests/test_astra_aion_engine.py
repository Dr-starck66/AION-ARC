"""Hermetic tests with positive and adversarial controls; no fake Kaggle score."""
import json
import unittest

from astra_aion_engine import AionEngine, Feedback, Observation, Plan
from astra_aion_engine.adapters import arc3_lattice_plan


class FormHarness:
    """Independent non-Kaggle task: interact with a synthetic web form."""
    def __init__(self):
        self.phase = 0
        self.calls = []

    def observe(self):
        actions = ({"OPEN"}, {"FILL"}, {"SUBMIT"}, set())[self.phase]
        return Observation({"phase": self.phase, "private_token": "NEVER_TRACE"},
                           frozenset(actions), goal_reached=self.phase == 3)

    def execute(self, action):
        self.calls.append(action)
        self.phase += 1
        return Feedback(True, True, goal_reached=self.phase == 3)


class EngineTests(unittest.TestCase):
    def test_real_actions_and_goal_acknowledgement(self):
        form = FormHarness()
        engine = AionEngine(form.observe, lambda obs: Plan(("OPEN", "FILL", "SUBMIT"), "synthetic-form"), form.execute)
        result = engine.run()
        self.assertEqual((result.status, result.actions_executed), ("PASS", 3))
        self.assertEqual(form.calls, ["OPEN", "FILL", "SUBMIT"])
        self.assertNotIn("NEVER_TRACE", json.dumps(result.events))
        self.assertEqual(result.reason, "goal_confirmed_by_executor")

    def test_unknown_observation_no_action(self):
        calls = []
        engine = AionEngine(lambda: Observation(None, frozenset()), lambda _: None, calls.append)
        result = engine.run()
        self.assertEqual((result.status, result.reason), ("PARTIAL", "unsupported_observation"))
        self.assertEqual(calls, [])

    def test_bad_action_fails_closed(self):
        calls = []
        engine = AionEngine(lambda: Observation(None, frozenset({"READ"})),
                            lambda _: Plan(("DELETE",)), calls.append)
        self.assertEqual(engine.run().reason, "action_not_legal")
        self.assertFalse(calls)

    def test_no_op_keeps_partial(self):
        engine = AionEngine(lambda: Observation(None, frozenset({"CLICK"})),
                            lambda _: Plan(("CLICK", "CLICK")),
                            lambda _: Feedback(True, False))
        result = engine.run()
        self.assertEqual((result.status, result.actions_executed), ("PARTIAL", 1))
        self.assertEqual(result.reason, "no_op_detected")

    def test_action_acknowledgement_required(self):
        engine = AionEngine(lambda: Observation(None, frozenset({"CLICK"})),
                            lambda _: Plan(("CLICK",)), lambda _: Feedback(False, True, goal_reached=True))
        self.assertEqual(engine.run().status, "FAIL")

    def test_stale_plan_never_reports_pass(self):
        engine = AionEngine(lambda: Observation(None, frozenset({"CLICK"})),
                            lambda _: Plan(("CLICK",)), lambda _: Feedback(True, True))
        self.assertEqual(engine.run().reason, "plan_exhausted_without_goal")

    def test_budget_prevents_any_execution(self):
        calls = []
        engine = AionEngine(lambda: Observation(None, frozenset({"CLICK"})),
                            lambda _: Plan(("CLICK", "CLICK")), calls.append, max_actions=1)
        result = engine.run()
        self.assertEqual(result.reason, "plan_exceeds_action_budget")
        self.assertEqual(calls, [])

    def test_executor_exception_hides_sensitive_text(self):
        def bad(_):
            raise RuntimeError("private-secret-value")
        engine = AionEngine(lambda: Observation(None, frozenset({"CLICK"})),
                            lambda _: Plan(("CLICK",)), bad)
        result = engine.run()
        self.assertEqual(result.status, "FAIL")
        self.assertNotIn("private-secret-value", result.reason)

    def test_initial_goal_no_calls(self):
        engine = AionEngine(lambda: Observation(None, frozenset(), goal_reached=True),
                            lambda _: self.fail("planner called"),
                            lambda _: self.fail("executor called"))
        self.assertEqual(engine.run().reason, "goal_observed")

    def test_invalid_budget_rejected(self):
        for value in (0, -1, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                AionEngine(lambda: None, lambda _: None, lambda _: None, max_actions=value)

    def test_action_text_is_never_logged(self):
        secret = "TYPE:api-token=confidential"
        result = AionEngine(lambda: Observation(None, frozenset({secret})),
                            lambda _: Plan((secret,)), lambda _: Feedback(True, True)).run()
        self.assertNotIn(secret, json.dumps(result.events))
        self.assertIn("action_id_sha256", result.events[0])

    def test_arc_adapter_reuses_existing_route_not_fork(self):
        calls = []
        def fake_route(grid, *, legal_actions):
            calls.append((grid, legal_actions))
            return {"actions": [4, 2], "profile": "visual-lattice-bfs"}
        obs = Observation("synthetic-frame", frozenset({"ACTION4", "ACTION2"}))
        plan = arc3_lattice_plan(obs, route_fn=fake_route)
        self.assertEqual(plan.actions, ("ACTION4", "ACTION2"))
        self.assertEqual(calls[0][0], "synthetic-frame")
        self.assertEqual(set(calls[0][1]), {2, 4})

    def test_arc_adapter_invalid_route_falls_back(self):
        route = lambda grid, *, legal_actions: {"actions": [3], "profile": "visual-lattice-bfs"}
        plan = arc3_lattice_plan(Observation("frame", frozenset({"ACTION4"})), route_fn=route)
        self.assertIsNone(plan)

    def test_existing_graph_integration_when_checkout_available(self):
        from pathlib import Path
        if not (Path(__file__).resolve().parents[1] / "kaggle" / "arc3_graph_nav.py").is_file():
            self.skipTest("Existing graph file is present only in the GitHub checkout")
        grid = [[0 for _ in range(64)] for _ in range(64)]
        grid[63] = [6] * 64
        for y in range(8, 11):
            for x in range(8, 11):
                grid[y][x] = 9
            for x in range(20, 23):
                grid[y][x] = 14
        grid[9][12] = 2
        grid[9][18] = 2
        obs = Observation(grid, frozenset({"ACTION1", "ACTION2", "ACTION3", "ACTION4"}))
        plan = arc3_lattice_plan(obs)
        self.assertIsNotNone(plan)
        self.assertEqual(plan.actions, ("ACTION4", "ACTION4"))


if __name__ == "__main__":
    unittest.main()
