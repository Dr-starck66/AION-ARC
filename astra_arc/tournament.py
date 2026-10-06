"""ASTRA HYPOTHESIS TOURNAMENT Ω — falsify competing world models before live actions."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable
from math import log2

@dataclass
class Model:
    name: str
    predict: Callable[[Any, Any], Any]
    support: int = 0
    contradictions: list[int] = field(default_factory=list)
    alive: bool = True

    def retrodict(self, history: Iterable[tuple[Any, Any, Any]],
                  equal: Callable[[Any, Any], bool] = lambda a,b: a == b) -> bool:
        self.support = 0
        self.contradictions.clear()
        self.alive = True
        for i, (before, action, after) in enumerate(history):
            try:
                predicted = self.predict(before, action)
            except Exception:
                self.contradictions.append(i)
                self.alive = False
                continue
            if equal(predicted, after):
                self.support += 1
            else:
                self.contradictions.append(i)
                self.alive = False
        return self.alive

def survivors(models: Iterable[Model], history: Iterable[tuple[Any,Any,Any]],
              equal: Callable[[Any,Any],bool] = lambda a,b:a==b) -> list[Model]:
    hist = list(history)
    return [m for m in models if m.retrodict(hist, equal=equal)]

def prediction_partition(models: Iterable[Model], state: Any, action: Any,
                         key: Callable[[Any],Any] = repr) -> dict[Any,list[str]]:
    buckets: dict[Any,list[str]] = {}
    for model in models:
        if not model.alive:
            continue
        try:
            outcome = key(model.predict(state, action))
        except Exception as exc:
            outcome = ("EXCEPTION", type(exc).__name__)
        buckets.setdefault(outcome, []).append(model.name)
    return buckets

def information_gain(models: Iterable[Model], state: Any, action: Any,
                     key: Callable[[Any],Any] = repr) -> float:
    buckets = prediction_partition(models, state, action, key=key)
    total = sum(len(names) for names in buckets.values())
    if not total:
        return 0.0
    entropy = 0.0
    for names in buckets.values():
        p = len(names) / total
        entropy -= p * log2(p)
    return entropy

def choose_discriminating_probe(actions: Iterable[Any], models: Iterable[Model], state: Any,
                                risk: Callable[[Any],float] = lambda _a:0.0) -> Any | None:
    live = [m for m in models if m.alive]
    scored = []
    for action in actions:
        gain = information_gain(live, state, action)
        penalty = float(risk(action) or 0.0)
        scored.append((gain - penalty, gain, -penalty, str(action), action))
    return max(scored)[-1] if scored else None

def robust_action(actions: Iterable[Any], models: Iterable[Model], state: Any,
                  score: Callable[[Any],float]) -> dict[str,Any]:
    """Maximin choice over surviving models; favors consensus as a tiebreak."""
    live = [m for m in models if m.alive]
    rows = []
    for action in actions:
        outcomes = []
        failed = False
        for model in live:
            try:
                outcomes.append(model.predict(state, action))
            except Exception:
                failed = True
                break
        if failed or not outcomes:
            continue
        scores = [float(score(outcome)) for outcome in outcomes]
        consensus = len({repr(o) for o in outcomes}) == 1
        rows.append({
            "action": action,
            "worst_case": min(scores),
            "mean": sum(scores)/len(scores),
            "consensus": consensus,
            "predictions": outcomes,
        })
    if not rows:
        return {"status":"NO_ACTION","action":None,"candidates":[]}
    rows.sort(key=lambda r:(r["worst_case"], r["mean"], r["consensus"], str(r["action"])), reverse=True)
    best = rows[0]
    return {"status":"OK","action":best["action"],"best":best,"candidates":rows}

def tournament(models: Iterable[Model], history: Iterable[tuple[Any,Any,Any]],
               actions: Iterable[Any], state: Any,
               score: Callable[[Any],float] | None = None,
               risk: Callable[[Any],float] = lambda _a:0.0,
               equal: Callable[[Any,Any],bool] = lambda a,b:a==b) -> dict[str,Any]:
    live = survivors(list(models), list(history), equal=equal)
    if not live:
        return {"status":"NO_SURVIVOR","survivors":[],"action":None}
    if score is not None:
        robust = robust_action(actions, live, state, score)
        if robust["status"] == "OK" and robust["best"]["consensus"]:
            return {"status":"CONSENSUS_PLAN","survivors":[m.name for m in live],"action":robust["action"],"robust":robust}
    probe = choose_discriminating_probe(actions, live, state, risk=risk)
    gains = {str(a):information_gain(live,state,a) for a in actions}
    if probe is not None and gains.get(str(probe),0.0) > 0:
        return {"status":"PROBE","survivors":[m.name for m in live],"action":probe,"information_gain":gains.get(str(probe),0.0)}
    if score is not None:
        robust = robust_action(actions, live, state, score)
        return {"status":"ROBUST_PLAN","survivors":[m.name for m in live],"action":robust.get("action"),"robust":robust}
    return {"status":"UNDERDETERMINED","survivors":[m.name for m in live],"action":None}
