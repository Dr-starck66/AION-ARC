#!/usr/bin/env python3
"""ASTRA independent NFL Combine/draft-grade exploratory audit.

Reads only public, SHA-pinned Combine data via analyze_combine.py. No Kaggle,
competition, submissions, GPU, or external uploading. Descriptive association
only; scouting grades are NOT independent real-match career outcomes.
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import math
from collections import defaultdict
from pathlib import Path

from analyze_combine import load_data, git_blob_sha1


def _pearson(rows):
    mx = sum(p[0] for p in rows) / len(rows)
    my = sum(p[1] for p in rows) / len(rows)
    xx = sum((x - mx) ** 2 for x, _ in rows)
    yy = sum((y - my) ** 2 for _, y in rows)
    xy = sum((x - mx) * (y - my) for x, y in rows)
    return xy / math.sqrt(xx * yy) if xx > 0 and yy > 0 else None


def _random_stream(seed):
    seed &= 0xFFFFFFFF
    while True:
        seed ^= (seed << 13) & 0xFFFFFFFF
        seed ^= seed >> 17
        seed ^= (seed << 5) & 0xFFFFFFFF
        seed &= 0xFFFFFFFF
        yield seed / 4294967296


def analyze(raw: bytes, *, permutations=300, seed=20261113):
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
    needed = {"year", "position_group", "forty_yard_dash", "draft_grade"}
    if not reader.fieldnames or not needed.issubset(reader.fieldnames):
        raise ValueError("Missing required columns")
    groups = defaultdict(list)
    skipped = {"unclassified": 0, "missing_dash": 0, "missing_grade": 0, "invalid": 0}
    rows = []
    posgroups = defaultdict(list)
    for row in reader:
        if None in row or any(x is None for x in row.values()):
            raise ValueError("Ragged CSV")
        pos = row["position_group"].strip()
        if not pos:
            skipped["unclassified"] += 1
            continue
        if not row["forty_yard_dash"].strip():
            skipped["missing_dash"] += 1
            continue
        if not row["draft_grade"].strip():
            skipped["missing_grade"] += 1
            continue
        try:
            dash, grade = float(row["forty_yard_dash"]), float(row["draft_grade"])
            year = int(row["year"])
        except ValueError:
            skipped["invalid"] += 1
            continue
        if not (3 < dash < 8 and 0 <= grade <= 100 and 2000 <= year <= 2030):
            skipped["invalid"] += 1
            continue
        idx = len(rows)
        rows.append((dash, grade, year, pos))
        groups[(year, pos)].append(idx)
        posgroups[pos].append((dash, grade))
    if len(rows) < 5 or permutations < 1 or permutations > 10000:
        raise ValueError("Insufficient data or invalid permutation count")
    rx = [0.0] * len(rows)
    ry = [0.0] * len(rows)
    ssx = ssy = ssxy = 0.0
    usable_n = 0
    for indices in groups.values():
        if len(indices) < 2:
            continue
        mx = sum(rows[i][0] for i in indices) / len(indices)
        my = sum(rows[i][1] for i in indices) / len(indices)
        for i in indices:
            dx, dy = rows[i][0] - mx, rows[i][1] - my
            rx[i], ry[i] = dx, dy
            ssx += dx * dx
            ssy += dy * dy
            ssxy += dx * dy
            usable_n += 1
    if ssx == 0 or ssy == 0:
        raise ValueError("One or both variables have no within-stratum variation")
    observed_r = ssxy / math.sqrt(ssx * ssy)
    stream = _random_stream(seed)
    extreme = 0
    null_min = float("inf")
    null_max = -float("inf")
    for _ in range(permutations):
        shuffled_y = [0.0] * len(rows)
        for indices in groups.values():
            values = [rows[i][1] for i in indices]
            for j in range(len(values) - 1, 0, -1):
                k = int(next(stream) * (j + 1))
                values[j], values[k] = values[k], values[j]
            for i, value in zip(indices, values):
                shuffled_y[i] = value
        sy = sxy = 0.0
        for i, (_, original_y, _, _) in enumerate(rows):
            dy = shuffled_y[i] - original_y + ry[i]
            sy += dy * dy
            sxy += rx[i] * dy
        null_r = sxy / math.sqrt(ssx * sy) if sy > 0 else 0.0
        null_min, null_max = min(null_min, null_r), max(null_max, null_r)
        extreme += abs(null_r) >= abs(observed_r)
    per_position = []
    for pos, values in sorted(posgroups.items(), key=lambda p: (-len(p[1]), p[0])):
        if len(values) < 30:
            continue
        per_position.append({"position_group": pos, "n": len(values),
                             "pearson_40_seconds_vs_draft_grade": _pearson(values)})
    return {
        "kind": "ASTRA_NFL_COMBINE_DRAFT_GRADE_EXPLORATORY",
        "source_git_blob_sha1": git_blob_sha1(raw),
        "competition": "NOT_USED",
        "rows_with_both_valid_and_classified": len(rows),
        "usable_within_strata_rows": usable_n,
        "strata_count": len(groups),
        "skipped": skipped,
        "within_year_position_pearson_r": observed_r,
        "permutations": permutations,
        "seed": seed,
        "extreme_null_permutations": extreme,
        "monte_carlo_two_sided_p_corrected": (extreme + 1) / (permutations + 1),
        "null_min": null_min,
        "null_max": null_max,
        "per_position": per_position,
        "limitations": [
            "Draft grade is a scouting rating and may incorporate Combine test results.",
            "Not an independent NFL match/career outcome, no causal inference.",
            "Exploratory association and Monte Carlo randomization test, not forecasting.",
            "Source CSV excludes year 2021, the in-person Combine was canceled.",
        ],
        "predictive_validity": "UNVERIFIED",
        "scientific_validation": "UNVERIFIED",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", help="Pinned public CSV; omit to fetch GitHub")
    p.add_argument("--output", help="Optional local JSON report")
    args = p.parse_args()
    result = analyze(load_data(args.input))
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print("ASTRA_NFL_OPEN_ASSOCIATION_PARTIAL n=" + str(result["rows_with_both_valid_and_classified"])
          + " r=" + str(result["within_year_position_pearson_r"]))
    print(text)


if __name__ == "__main__":
    main()
