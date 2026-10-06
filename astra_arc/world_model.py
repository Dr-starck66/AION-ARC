"""AION ARC-AGI-3 executable world-model contracts.

Zero-cost, game-agnostic scaffolding for Kaggle.  The model is deliberately small:
the LLM/builder supplies candidate transition functions; this module supplies
falsification, confidence, planning and fail-closed execution gates.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from typing import Any, Callable, Iterable
from collections import deque
import json

class Confidence(str, Enum):
    UNKNOWN="UNKNOWN"; CANDIDATE="CANDIDATE"; CONFIRMED="CONFIRMED"; QUARANTINED="QUARANTINED"

@dataclass(frozen=True)
class Transition:
    before: Any
    action: Any
    after: Any

@dataclass
class Hypothesis:
    name: str
    predict: Callable[[Any, Any], Any]
    confidence: Confidence = Confidence.UNKNOWN
    checked: int = 0
    failures: list[str] = field(default_factory=list)

    def retrodict(self, history: Iterable[Transition], equal: Callable[[Any,Any],bool]=lambda a,b:a==b) -> bool:
        self.checked = 0
        self.failures.clear()
        for i, tr in enumerate(history):
            try:
                got = self.predict(tr.before, tr.action)
            except Exception as exc:
                self.failures.append(f"{i}:exception:{type(exc).__name__}")
                self.confidence = Confidence.QUARANTINED
                return False
            self.checked += 1
            if not equal(got, tr.after):
                self.failures.append(f"{i}:mismatch")
        self.confidence = Confidence.CONFIRMED if self.checked and not self.failures else (
            Confidence.QUARANTINED if self.failures else Confidence.UNKNOWN
        )
        return self.confidence == Confidence.CONFIRMED

    def may_plan(self) -> bool:
        return self.confidence == Confidence.CONFIRMED and not self.failures

@dataclass
class Checkpoint:
    digest: str
    payload: Any

def checkpoint(state: Any) -> Checkpoint:
    raw = json.dumps(state, sort_keys=True, separators=(",",":"), default=str).encode()
    return Checkpoint(sha256(raw).hexdigest(), state)

def verify_checkpoint(cp: Checkpoint) -> bool:
    return checkpoint(cp.payload).digest == cp.digest

def bfs_plan(start: Any, actions: Iterable[Any], predict: Callable[[Any,Any],Any],
             goal: Callable[[Any],bool], key: Callable[[Any],Any]=repr,
             max_nodes: int=5000, max_depth: int=64) -> list[Any] | None:
    if goal(start): return []
    q=deque([(start,[])])
    seen={key(start)}
    nodes=0
    while q and nodes < max_nodes:
        state,path=q.popleft(); nodes+=1
        if len(path) >= max_depth: continue
        for action in actions:
            nxt=predict(state,action)
            k=key(nxt)
            if k in seen: continue
            np=path+[action]
            if goal(nxt): return np
            seen.add(k); q.append((nxt,np))
    return None

def execute_verified(plan: Iterable[Any], expected_states: Iterable[Any], step: Callable[[Any],Any],
                     observe: Callable[[Any],Any]=lambda x:x,
                     equal: Callable[[Any,Any],bool]=lambda a,b:a==b) -> dict[str,Any]:
    """Execute one action at a time; stop at the first prediction mismatch."""
    expected=list(expected_states)
    plan=list(plan)
    if len(plan) != len(expected):
        return {"status":"FAIL","reason":"plan_expectation_length_mismatch","executed":0}
    for i,(action,want) in enumerate(zip(plan,expected)):
        result=step(action)
        got=observe(result)
        if not equal(got,want):
            return {"status":"QUARANTINED","reason":"prediction_mismatch","executed":i+1,
                    "failed_action":action,"expected":want,"observed":got}
    return {"status":"PASS","executed":len(plan)}
