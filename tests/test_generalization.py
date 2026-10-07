import types

import pytest

from astra_arc.generalization import chronological_split, score_model, temporal_holdout_gate


def test_chronological_split_keeps_future_suffix_separate():
    replay = [(i, 1, i + 1) for i in range(8)]
    train, holdout = chronological_split(replay, holdout_fraction=0.25, min_holdout=2)
    assert train == replay[:6]
    assert holdout == replay[6:]


def test_memorizer_passes_train_but_fails_future_holdout():
    replay = [(i, 1, i + 1) for i in range(8)]
    train, holdout = chronological_split(replay, holdout_fraction=0.25, min_holdout=2)
    table = {(s, a): after for s, a, after in train}

    memorizer = types.SimpleNamespace(
        name="memorizer",
        predict=lambda s, a: table.get((s, a), -999),
    )
    train_acc, _ = score_model(memorizer, train)
    holdout_acc, _ = score_model(memorizer, holdout)

    assert train_acc == 1.0
    assert holdout_acc == 0.0


def test_general_rule_survives_temporal_holdout():
    replay = [(i, 1, i + 1) for i in range(8)]
    rule = types.SimpleNamespace(name="plus", predict=lambda s, a: s + a)
    out = temporal_holdout_gate([rule], replay, holdout_fraction=0.25, min_holdout=2)

    assert out["status"] == "PASS"
    assert out["survivor_names"] == ["plus"]
    assert out["train_size"] == 6
    assert out["holdout_size"] == 2


def test_gate_rejects_memorizer_and_keeps_general_model():
    replay = [(i, 1, i + 1) for i in range(8)]
    train, _ = chronological_split(replay, holdout_fraction=0.25, min_holdout=2)
    table = {(s, a): after for s, a, after in train}

    memorizer = types.SimpleNamespace(
        name="memorizer",
        predict=lambda s, a: table.get((s, a), -999),
    )
    rule = types.SimpleNamespace(name="general", predict=lambda s, a: s + a)

    out = temporal_holdout_gate(
        [memorizer, rule],
        replay,
        holdout_fraction=0.25,
        min_holdout=2,
    )

    assert out["status"] == "PASS"
    assert out["survivor_names"] == ["general"]
    assert out["rejected_names"] == ["memorizer"]


def test_gate_fails_when_no_model_generalizes():
    replay = [(i, 1, i + 1) for i in range(8)]
    train, _ = chronological_split(replay, holdout_fraction=0.25, min_holdout=2)
    table = {(s, a): after for s, a, after in train}
    memorizer = types.SimpleNamespace(
        name="memorizer",
        predict=lambda s, a: table.get((s, a), -999),
    )

    out = temporal_holdout_gate([memorizer], replay, holdout_fraction=0.25, min_holdout=2)
    assert out["status"] == "FAIL"
    assert out["survivor_names"] == []


def test_holdout_requires_enough_transitions():
    with pytest.raises(ValueError):
        chronological_split([(0, 1, 1), (1, 1, 2)], min_holdout=2)
