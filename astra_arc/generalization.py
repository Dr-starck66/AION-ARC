"""ASTRA TEMPORAL HOLDOUT Ω — leakage-resistant world-model validation.

This module does not claim hidden Kaggle performance. It supplies a deterministic
gate that separates earlier replay transitions from a later holdout suffix, scores
candidate transition models on both, and rejects models that only fit history.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class HoldoutScore:
    name: str
    train_accuracy: float
    holdout_accuracy: float
    train_checked: int
    holdout_checked: int
    train_failures: tuple[int, ...]
    holdout_failures: tuple[int, ...]

    @property
    def generalizes(self) -> bool:
        return self.train_accuracy == 1.0 and self.holdout_accuracy == 1.0


def chronological_split(
    replay: Iterable[tuple[Any, Any, Any]],
    *,
    holdout_fraction: float = 0.25,
    min_holdout: int = 2,
) -> tuple[list[tuple[Any, Any, Any]], list[tuple[Any, Any, Any]]]:
    """Split a replay into an earlier train prefix and later holdout suffix."""
    rows = list(replay)
    if not 0 < float(holdout_fraction) < 1:
        raise ValueError("holdout_fraction must be between 0 and 1")
    min_holdout = max(1, int(min_holdout))
    if len(rows) < min_holdout + 1:
        raise ValueError("not enough transitions for a temporal holdout")
    holdout_n = max(min_holdout, int(ceil(len(rows) * float(holdout_fraction))))
    holdout_n = min(holdout_n, len(rows) - 1)
    return rows[:-holdout_n], rows[-holdout_n:]


def score_model(
    model: Any,
    replay: Iterable[tuple[Any, Any, Any]],
    *,
    equal: Callable[[Any, Any], bool] = lambda a, b: a == b,
) -> tuple[float, tuple[int, ...]]:
    """Score a callable or object with .predict(state, action) without mutating it."""
    predict = getattr(model, "predict", model)
    failures: list[int] = []
    checked = 0
    for index, (before, action, after) in enumerate(replay):
        checked += 1
        try:
            predicted = predict(before, action)
        except Exception:
            failures.append(index)
            continue
        if not equal(predicted, after):
            failures.append(index)
    accuracy = (checked - len(failures)) / checked if checked else 0.0
    return accuracy, tuple(failures)


def temporal_holdout_gate(
    models: Iterable[Any],
    replay: Iterable[tuple[Any, Any, Any]],
    *,
    holdout_fraction: float = 0.25,
    min_holdout: int = 2,
    min_train_accuracy: float = 1.0,
    min_holdout_accuracy: float = 1.0,
    equal: Callable[[Any, Any], bool] = lambda a, b: a == b,
) -> dict[str, Any]:
    """Reject replay-perfect memorizers that fail on the unseen chronological suffix."""
    train, holdout = chronological_split(
        replay,
        holdout_fraction=holdout_fraction,
        min_holdout=min_holdout,
    )
    rows: list[HoldoutScore] = []
    survivors: list[Any] = []
    rejected: list[Any] = []

    for model in list(models):
        name = str(getattr(model, "name", getattr(model, "__name__", type(model).__name__)))
        train_accuracy, train_failures = score_model(model, train, equal=equal)
        holdout_accuracy, holdout_failures = score_model(model, holdout, equal=equal)
        score = HoldoutScore(
            name=name,
            train_accuracy=train_accuracy,
            holdout_accuracy=holdout_accuracy,
            train_checked=len(train),
            holdout_checked=len(holdout),
            train_failures=train_failures,
            holdout_failures=holdout_failures,
        )
        rows.append(score)
        if (
            train_accuracy >= float(min_train_accuracy)
            and holdout_accuracy >= float(min_holdout_accuracy)
        ):
            survivors.append(model)
        else:
            rejected.append(model)

    rows.sort(key=lambda row: (-row.holdout_accuracy, -row.train_accuracy, row.name))
    return {
        "status": "PASS" if survivors else "FAIL",
        "train_size": len(train),
        "holdout_size": len(holdout),
        "survivors": survivors,
        "survivor_names": [str(getattr(m, "name", getattr(m, "__name__", type(m).__name__))) for m in survivors],
        "rejected_names": [str(getattr(m, "name", getattr(m, "__name__", type(m).__name__))) for m in rejected],
        "scores": rows,
    }
