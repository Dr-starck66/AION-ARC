"""Paired ARC-AGI-3 candidate comparison. Input provenance is not independently verified.

Run JSON: {"engine":"arc3_official_local", "games":[{"game_id":"ls20","seed":0,
"score_percent":4.0,"levels_completed":2,"actions":13,"runtime_seconds":5.7}]}
"""
from __future__ import annotations
import argparse
import json
from math import isfinite
from pathlib import Path

def load_run(raw: dict) -> dict:
    if not isinstance(raw, dict) or raw.get("engine") != "arc3_official_local":
        raise ValueError("actual arc3_official_local engine provenance is required")
    games = raw.get("games")
    if not isinstance(games, list) or not games:
        raise ValueError("nonempty actual game records required")
    result = {}
    for game in games:
        if not isinstance(game, dict) or not isinstance(game.get("game_id"), str) or not game["game_id"]:
            raise ValueError("game_id required")
        seed = game.get("seed")
        if type(seed) is not int or seed < 0:
            raise ValueError("nonnegative integer seed required")
        key = (game["game_id"], seed)
        if key in result:
            raise ValueError("duplicate game and seed: %r" % (key,))
        for field in ("score_percent", "runtime_seconds"):
            if type(game.get(field)) not in (float, int) or not isfinite(float(game[field])):
                raise ValueError("invalid %s" % field)
        for field in ("actions", "levels_completed"):
            if type(game.get(field)) is not int or game[field] < 0:
                raise ValueError("invalid %s" % field)
        if not 0 <= game["score_percent"] <= 100 or game["runtime_seconds"] < 0:
            raise ValueError("score_percent out of range or runtime_seconds negative")
        result[key] = game
    return result

def compare(champion: dict, candidate: dict, min_games: int = 5) -> dict:
    ref = load_run(champion)
    challenger = load_run(candidate)
    if ref.keys() != challenger.keys():
        raise ValueError("not paired: identical games and seeds required")
    keys = sorted(ref)
    n = len(keys)
    deltas = [challenger[k]["score_percent"] - ref[k]["score_percent"] for k in keys]
    mean_delta = sum(deltas) / n
    base_mean = sum(ref[k]["score_percent"] for k in keys) / n
    challenger_mean = sum(challenger[k]["score_percent"] for k in keys) / n
    base_actions = sum(ref[k]["actions"] for k in keys)
    challenger_actions = sum(challenger[k]["actions"] for k in keys)
    base_time = sum(ref[k]["runtime_seconds"] for k in keys)
    challenger_time = sum(challenger[k]["runtime_seconds"] for k in keys)
    if n < min_games:
        status = "INSUFFICIENT_GAMES"
    elif mean_delta < 0 or min(deltas) < -2.0:
        status = "REGRESSION"
    elif mean_delta > 0:
        status = "PROMISING_REQUIRES_OFFICIAL_VALIDATION"
    else:
        status = "NO_SCORE_GAIN"
    return {
        "status": status,
        "proof_level": "SELF_REPORTED_LOCAL_GAME_DATA_NOT_OFFICIAL_KAGGLE",
        "paired_games": n,
        "champion_mean_percent": round(base_mean, 5),
        "candidate_mean_percent": round(challenger_mean, 5),
        "score_delta_percentage_points": round(mean_delta, 5),
        "game_regressions": sum(d < 0 for d in deltas),
        "worst_game_delta": round(min(deltas), 5),
        "champion_actions_total": base_actions,
        "candidate_actions_total": challenger_actions,
        "champion_runtime_seconds": round(base_time, 5),
        "candidate_runtime_seconds": round(challenger_time, 5),
    }

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("champion", type=Path)
    p.add_argument("candidate", type=Path)
    args = p.parse_args()
    print(json.dumps(compare(json.loads(args.champion.read_text()), json.loads(args.candidate.read_text())), indent=2))

if __name__ == "__main__":
    main()
