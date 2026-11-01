"""Regression tests for graph navigation installed in the Kaggle harness.

No GPU, network, credentials or mock Kaggle score.
"""
from __future__ import annotations

import copy
import unittest
from types import SimpleNamespace

from kaggle.arc3_graph_nav import graph_route, try_graph_step


def small_lattice():
    grid = [[5] * 64 for _ in range(64)]
    grid[63] = [6] * 64
    # Three nodes at x=16,22,28 on row 16; edge midpoints x=19,25.
    for x in (16, 22, 28):
        grid[16][x] = 0
    for x in (19, 25):
        grid[16][x] = 2
    for y in range(15, 18):
        for x in range(15, 18):
            grid[y][x] = 9
        for x in range(27, 30):
            grid[y][x] = 14
    grid[16][19] = 2
    grid[16][25] = 2
    return grid


class FakeSession:
    def __init__(self, grid, *, success_on=2, action_ok=True):
        self.grid = copy.deepcopy(grid)
        self.action_count = 0
        self.game = SimpleNamespace(
            current_state=SimpleNamespace(available_actions=[1, 2, 3, 4])
        )
        self.success_on = success_on
        self.action_ok = action_ok

    def should_stop(self):
        return False

    def current_frame(self):
        return SimpleNamespace(grid=self.grid)

    def step_env(self, request):
        if not self.action_ok:
            return {"executed": False}
        assert request == {"action": "ACTION4"}, request
        self.action_count += 1
        # First action changes palette, making fresh image detection invalid.
        if self.action_count == 1:
            for y in range(15, 18):
                for x in range(15, 18):
                    self.grid[y][x] = 0
        return {
            "executed": True,
            "board_changed": True,
            "level_completed": self.action_count == self.success_on,
            "run_complete": False,
        }


class GraphNavigationTests(unittest.TestCase):
    def test_visual_bfs_computes_route_not_lookup(self):
        route = graph_route(small_lattice())
        self.assertIsNotNone(route)
        self.assertEqual(route["actions"], [4, 4])
        self.assertEqual(route["profile"], "visual-lattice-bfs")

    def test_mutated_frame_reuses_plan_until_level_completion(self):
        session = FakeSession(small_lattice())
        self.assertTrue(try_graph_step(session))
        self.assertIsNone(graph_route(session.current_frame().grid))
        self.assertTrue(try_graph_step(session))
        self.assertEqual(session.action_count, 2)
        self.assertIsNone(session._astra_graph_nav_route)
        self.assertFalse(try_graph_step(session))

    def test_negative_control_different_palette_abstains(self):
        s = FakeSession([[4] * 64 for _ in range(64)])
        self.assertFalse(try_graph_step(s))
        self.assertEqual(s.action_count, 0)

    def test_action_failure_disables_retries(self):
        s = FakeSession(small_lattice(), action_ok=False)
        self.assertFalse(try_graph_step(s))
        self.assertTrue(s._astra_graph_nav_disabled)
        self.assertEqual(s.action_count, 0)

    def test_exhausted_route_falls_back_to_model(self):
        s = FakeSession(small_lattice(), success_on=99)
        self.assertTrue(try_graph_step(s))
        self.assertTrue(try_graph_step(s))
        self.assertTrue(s._astra_graph_nav_disabled)
        self.assertFalse(try_graph_step(s))


if __name__ == "__main__":
    unittest.main()
