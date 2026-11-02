"""Reuse bridge for ASTRA's preexisting original pixel navigation code.

There is deliberately no second copy of the ARC graph routing algorithm.
The generic controller can be imported without Kaggle, GPU or network access.
"""
from __future__ import annotations

from functools import lru_cache
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Callable

from .core import Observation, Plan


@lru_cache(maxsize=1)
def _existing_graph_route() -> Callable[..., dict[str, Any] | None]:
    """Load the exact user-owned implementation from the same repository."""
    source = Path(__file__).resolve().parents[1] / "kaggle" / "arc3_graph_nav.py"
    if not source.is_file():
        raise FileNotFoundError("Existing ARC visual graph module not present")
    spec = spec_from_file_location("astra_existing_arc3_graph_nav", source)
    if spec is None or spec.loader is None:
        raise ImportError("Original visual graph code cannot be loaded")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.graph_route


def arc3_lattice_plan(
    observation: Observation,
    *,
    route_fn: Callable[..., dict[str, Any] | None] | None = None,
) -> Plan | None:
    """Translate a proven ARC lattice route to the generic action protocol.

    All nonmatching images and routes are left to another planner. Optional
    route_fn is for deterministic unit testing, not a separate algorithm.
    """
    route = route_fn if route_fn is not None else _existing_graph_route()
    allowed = tuple(int(name[6:]) for name in observation.legal_actions
                    if isinstance(name, str) and name.startswith("ACTION")
                    and name[6:] in {"1", "2", "3", "4"})
    found = route(observation.payload, legal_actions=allowed)
    if not isinstance(found, dict) or not found.get("actions"):
        return None
    actions = tuple(f"ACTION{n}" for n in found["actions"])
    if any(action not in observation.legal_actions for action in actions):
        return None
    return Plan(actions=actions, method=found.get("profile", "visual-lattice-bfs"))
