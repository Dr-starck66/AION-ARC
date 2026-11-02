"""Minimal, offline decision-to-action controller for user-owned ASTRA components.

No model provider, browser stack, network client or third-party runtime is required.
A PASS means a real executor acknowledged a goal, not an external benchmark win.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Callable, Literal

Status = Literal["PASS", "PARTIAL", "FAIL"]


@dataclass(frozen=True)
class Observation:
    """Perceived state. Payload is deliberately excluded from event traces."""

    payload: Any
    legal_actions: frozenset[str]
    goal_reached: bool = False
    terminal: bool = False


@dataclass(frozen=True)
class Plan:
    """A bounded, explicit sequence proposed by a domain-specific planner."""

    actions: tuple[str, ...]
    method: str = "unspecified"


@dataclass(frozen=True)
class Feedback:
    """The executor's *actual* result, never a predicted outcome."""

    executed: bool
    changed: bool
    goal_reached: bool = False
    terminal: bool = False


@dataclass(frozen=True)
class Outcome:
    status: Status
    reason: str
    actions_executed: int
    events: tuple[dict[str, Any], ...]


class AionEngine:
    """Safely execute one plan, checking live legal actions before every step.

    - Unexpected observations, invalid plans, tool errors or blocked actions
      stop execution instead of guessing or retrying blindly.
    - False execution acknowledgements never count as successful actions.
    - An exhausted plan cannot be a PASS without a verified goal signal.
    - Events record action fingerprints and outcomes, never raw action text, pixels or secrets.
    """

    def __init__(
        self,
        observe: Callable[[], Observation],
        plan: Callable[[Observation], Plan | None],
        execute: Callable[[str], Feedback],
        *,
        max_actions: int = 64,
    ) -> None:
        if not isinstance(max_actions, int) or isinstance(max_actions, bool) or max_actions < 1:
            raise ValueError("max_actions must be a positive integer")
        self.observe = observe
        self.plan = plan
        self.execute = execute
        self.max_actions = max_actions

    def run(self) -> Outcome:
        events: list[dict[str, Any]] = []
        successful_actions = 0

        def stop(status: Status, reason: str) -> Outcome:
            return Outcome(status, reason, successful_actions, tuple(events))

        def safe_action_id(action: str) -> str:
            # Action arguments may contain user text, credentials, or URLs.
            return sha256(action.encode("utf-8")).hexdigest()[:16]

        try:
            initial = self.observe()
            if not isinstance(initial, Observation):
                return stop("FAIL", "invalid_observation")
            if initial.goal_reached:
                return stop("PASS", "goal_observed")
            if initial.terminal:
                return stop("PARTIAL", "environment_terminal_without_goal")
            candidate = self.plan(initial)
        except Exception as exc:  # Fail closed, do not leak observation or credentials.
            return stop("FAIL", f"perception_or_planning_error:{type(exc).__name__}")

        if candidate is None:
            return stop("PARTIAL", "unsupported_observation")
        if (not isinstance(candidate, Plan) or not candidate.actions
                or not all(isinstance(a, str) and a for a in candidate.actions)):
            return stop("FAIL", "invalid_plan")
        if len(candidate.actions) > self.max_actions:
            return stop("PARTIAL", "plan_exceeds_action_budget")

        for index, action in enumerate(candidate.actions, start=1):
            try:
                live = self.observe()
                if not isinstance(live, Observation):
                    return stop("FAIL", "invalid_observation")
                if live.goal_reached:
                    return stop("PASS", "goal_observed")
                if live.terminal:
                    return stop("PARTIAL", "environment_terminal_without_goal")
                if action not in live.legal_actions:
                    events.append({"index": index, "action_id_sha256": safe_action_id(action), "state": "blocked"})
                    return stop("FAIL", "action_not_legal")
                feedback = self.execute(action)
            except Exception as exc:
                events.append({"index": index, "action_id_sha256": safe_action_id(action), "state": "error"})
                return stop("FAIL", f"execution_error:{type(exc).__name__}")

            if not isinstance(feedback, Feedback) or not feedback.executed:
                events.append({"index": index, "action_id_sha256": safe_action_id(action), "state": "unconfirmed"})
                return stop("FAIL", "action_not_confirmed")

            successful_actions += 1
            events.append({"index": index, "action_id_sha256": safe_action_id(action),
                           "state": "changed" if feedback.changed else "unchanged",
                           "goal": bool(feedback.goal_reached)})
            if feedback.goal_reached:
                return stop("PASS", "goal_confirmed_by_executor")
            if feedback.terminal:
                return stop("PARTIAL", "environment_terminal_without_goal")
            if not feedback.changed:
                return stop("PARTIAL", "no_op_detected")

        return stop("PARTIAL", "plan_exhausted_without_goal")
