"""AION host-side plan-prefix verifier.

Deterministic enforcement layer. It never decides game semantics itself; it only
checks caller-supplied expectations and stops a plan when observations diverge.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

@dataclass
class StepExpectation:
    action: Any
    expected_state: Any | None = None
    expected_legal_actions: set[str] | None = None
    allow_level_change: bool = False
    allow_terminal: bool = False

@dataclass
class PrefixResult:
    status: str
    executed: int
    reason: str | None = None
    observations: list[Any] = field(default_factory=list)

def execute_plan_prefix(
    expectations: Iterable[StepExpectation],
    step: Callable[[Any], Any],
    observe_state: Callable[[Any], Any],
    observe_legal_actions: Callable[[Any], Iterable[Any]] = lambda _x: (),
    observe_level: Callable[[Any], Any] = lambda _x: None,
    observe_terminal: Callable[[Any], bool] = lambda _x: False,
    equal: Callable[[Any, Any], bool] = lambda a,b: a == b,
) -> PrefixResult:
    """Execute one action at a time and fail closed on the first violated invariant."""
    expectations = list(expectations)
    observations = []
    previous_level = None
    seen = set()

    for index, spec in enumerate(expectations):
        raw = step(spec.action)
        state = observe_state(raw)
        legal = {str(x).upper() for x in observe_legal_actions(raw)}
        level = observe_level(raw)
        terminal = bool(observe_terminal(raw))
        observations.append(state)

        if spec.expected_state is not None and not equal(state, spec.expected_state):
            return PrefixResult("QUARANTINED", index + 1, "predicted_state_mismatch", observations)

        if spec.expected_legal_actions is not None:
            wanted = {str(x).upper() for x in spec.expected_legal_actions}
            if legal != wanted:
                return PrefixResult("QUARANTINED", index + 1, "legal_actions_changed", observations)

        if previous_level is not None and level != previous_level and not spec.allow_level_change:
            return PrefixResult("QUARANTINED", index + 1, "unexpected_level_change", observations)

        if terminal and not spec.allow_terminal:
            return PrefixResult("QUARANTINED", index + 1, "unexpected_terminal", observations)

        signature = repr((level, state, tuple(sorted(legal))))
        if signature in seen and index + 1 < len(expectations):
            return PrefixResult("QUARANTINED", index + 1, "unexpected_cycle", observations)
        seen.add(signature)
        previous_level = level

    return PrefixResult("PASS", len(expectations), None, observations)
