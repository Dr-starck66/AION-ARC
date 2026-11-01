"""ASTRA ARC-AGI-3 visual graph navigator (offline, zero dependencies).

A narrow, *non-universal* image-pattern policy for lattice mazes.  It does
not memorize action sequences or identify games by their name.  When the
frame does not match the proven graph schema, return None and let the
original model control the game.  Positive public-demo evidence must not
be reported as a Kaggle leaderboard score.
"""
from __future__ import annotations

from collections import deque
from typing import Any

_DIRECTIONS = ((0, -6, 1), (0, 6, 2), (-6, 0, 3), (6, 0, 4))
_NODES = frozenset((0, 4, 9, 14))


def graph_route(raw_grid: Any, *, legal_actions=(1, 2, 3, 4)) -> dict | None:
    """Plan a path from image pixels; return None for unsupported games.

    On the known public graph schema, player and goal occupy 3x3 color
    clusters (9 and 14); 6-pixel graph edges are color 2.  The restrictive
    signature is intentional: never feed unrelated games guessed actions.
    """
    try:
        grid = raw_grid
        if len(grid) != 64 or any(len(row) != 64 for row in grid):
            return None
        if not all(int(value) == 6 for value in grid[63]):
            return None
        player, goal = [], []
        for y in range(54):
            for x in range(64):
                pixel = int(grid[y][x])
                if pixel == 9:
                    player.append((x, y))
                elif pixel == 14:
                    goal.append((x, y))
        if not (4 <= len(player) <= 16 and 4 <= len(goal) <= 16):
            return None

        def midpoint(points):
            return (
                (min(x for x, _ in points) + max(x for x, _ in points)) // 2,
                (min(y for _, y in points) + max(y for _, y in points)) // 2,
            )

        start, target = midpoint(player), midpoint(goal)
        if not all(0 <= v < 54 for v in (*start, *target)):
            return None
        if any((target[i] - start[i]) % 6 for i in (0, 1)):
            return None
        allowed = set(int(action) for action in legal_actions)
        search = deque([(start[0], start[1], ())])
        seen = {start}
        expanded = 0
        while search and expanded < 128:
            x, y, history = search.popleft()
            expanded += 1
            if (x, y) == target:
                if not (1 <= len(history) <= 45):
                    return None
                return {
                    "actions": list(history),
                    "start": list(start),
                    "goal": list(target),
                    "expanded": expanded,
                    "visited": len(seen),
                    "profile": "visual-lattice-bfs",
                }
            for dx, dy, action in _DIRECTIONS:
                nx, ny = x + dx, y + dy
                if (
                    action not in allowed or (nx, ny) in seen
                    or not (3 <= nx < 61 and 3 <= ny < 54)
                    or int(grid[ny][nx]) not in _NODES
                    or int(grid[y + dy // 2][x + dx // 2]) != 2
                ):
                    continue
                seen.add((nx, ny))
                search.append((nx, ny, history + (action,)))
    except (TypeError, ValueError, IndexError, KeyError):
        return None
    return None


def try_graph_step(session: Any) -> bool:
    """Execute a cached vision plan, one host-validated action at a time.

    After the first step, game boards may mutate visited edges, so *never*
    re-plan against an altered image on every turn. Re-plan only after a
    level transition. The existing AI agent remains the safe fallback.
    """
    if getattr(session, "_astra_graph_nav_disabled", False):
        return False
    try:
        if session.should_stop() or session.action_count >= 140:
            return False
        state = session.game.current_state
        route = getattr(session, "_astra_graph_nav_route", None)
        if route is None:
            route = graph_route(
                session.current_frame().grid,
                legal_actions=state.available_actions,
            )
            if route is None:
                return False
            route["next"] = 0
            session._astra_graph_nav_route = route
        step_index = route["next"]
        if step_index >= len(route["actions"]):
            session._astra_graph_nav_disabled = True
            return False
        action = route["actions"][step_index]
        if action not in state.available_actions:
            session._astra_graph_nav_disabled = True
            return False
        before = session.action_count
        result = session.step_env({"action": f"ACTION{action}"})
        if (
            not isinstance(result, dict)
            or not result.get("executed")
            or session.action_count != before + 1
        ):
            session._astra_graph_nav_disabled = True
            return False
        if not (
            result.get("board_changed")
            or result.get("level_completed")
            or result.get("run_complete")
        ):
            session._astra_graph_nav_disabled = True
        if result.get("level_completed"):
            session._astra_graph_nav_route = None
            print("ASTRA_GRAPH_NAV_LEVEL_COMPLETED", session.action_count, flush=True)
        else:
            route["next"] = step_index + 1
            if route["next"] >= len(route["actions"]):
                # All planned moves exhausted without winning: fail closed.
                session._astra_graph_nav_disabled = True
        return True
    except Exception as exc:
        session._astra_graph_nav_disabled = True
        print("ASTRA_GRAPH_NAV_FAIL_CLOSED", type(exc).__name__, flush=True)
        return False
