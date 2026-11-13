#!/usr/bin/env python3
"""ASTRA NFL 2027 — official Kaggle input inspection, never fabricated scores.

Bounded reads: no full dataset loads, no upload, no user-identifying row exports.
Data source: Kaggle competition NFL Big Data Bowl 2027 (subject to rules).
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
from datetime import datetime, timezone

PROJECT = "nfl-big-data-bowl-2027"
SOURCE = "https://www.kaggle.com/competitions/nfl-big-data-bowl-2027"
ROOT = Path(os.environ.get("ASTRA_INPUT", "/kaggle/input"))
OUTPUT = Path(os.environ.get("ASTRA_OUTPUT", "/kaggle/working/astra_nfl_official_report.json"))
MAX_FILES = 100
MAX_PREVIEW_ROWS = 2000
MAX_FULL_HASH_BYTES = 80_000_000

def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def scan(root):
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Official competition folder is not mounted: " + str(root))
    # Official Kaggle mount may differ from the competition slug. Fail closed
    # unless a single official competition directory can be identified.
    dirs = [p for p in root.iterdir() if p.is_dir() and "nfl-big-data-bowl-2027" in p.name.lower()]
    if os.environ.get("ASTRA_INPUT"):
        selected = root  # test fixture or explicitly selected trusted input
    elif len(dirs) == 1:
        selected = dirs[0]
    else:
        raise ValueError("Competition data mount missing/ambiguous; mounts=" + repr(sorted(p.name for p in root.iterdir() if p.is_dir())[:30]))
    candidates = sorted(p for p in selected.rglob("*")
                        if p.is_file() and p.suffix.lower() in {".csv", ".parquet"})
    if not candidates:
        raise ValueError("Official competition files (.csv/.parquet) are missing")
    if len(candidates) > MAX_FILES:
        raise ValueError("Unexpectedly many input files; refusing unbounded scan")
    files = []
    for path in candidates:
        if path.is_symlink():
            raise ValueError("Symlink forbidden")
        name = str(path.relative_to(selected)).replace("\\", "/")
        low = name.lower()
        size = path.stat().st_size
        if size <= 0:
            raise ValueError("Empty input file: " + name)
        label = ("combine" if "combine" in low or "drill" in low
                 else "game" if "game" in low or "nfl" in low
                 else "unclassified")
        item = {"name": name, "bytes": size, "kind_candidate": label,
                "sha256": sha256_file(path) if size <= MAX_FULL_HASH_BYTES else None,
                "sha256_scope": "FULL" if size <= MAX_FULL_HASH_BYTES else "SKIPPED_LARGE"}
        if path.suffix.lower() == ".csv":
            with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                item["columns"] = headers
                item["sampled_rows"] = 0
                values = []
                speed_key = next((h for h in headers
                                  if h.lower() in ("s", "speed", "speed_mps")), None)
                for row in reader:
                    item["sampled_rows"] += 1
                    if speed_key:
                        try:
                            v = float(row[speed_key])
                            if math.isfinite(v) and v >= 0:
                                values.append(v)
                        except (TypeError, ValueError):
                            pass
                    if item["sampled_rows"] >= MAX_PREVIEW_ROWS:
                        break
                if values:
                    item["sample_speed_median"] = statistics.median(values)
                    item["sample_speed_max"] = max(values)
                    item["sample_speed_n"] = len(values)
        files.append(item)
    return files

def run():
    report = {"project": PROJECT, "source": SOURCE,
              "timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "official_input_origin": "KAGGLE_COMPETITION_MOUNT",
              "official_rule_acceptance": "NOT_INDEPENDENTLY_CHECKED",
              "sample_not_full_population": True,
              "statistical_prediction_or_nfl_linkage": "UNVERIFIED",
              "status": "UNVERIFIED"}
    try:
        files = scan(ROOT)
        types = sorted(set(f["kind_candidate"] for f in files))
        report.update({"status": "PARTIAL", "gate": "OFFICIAL_INPUT_SCANNED",
                       "input_files": files, "file_count": len(files),
                       "candidate_types": types,
                       "combined_nfl_outcome_mapping": "UNVERIFIED",
                       "data_science_claims": "UNVERIFIED"})
        if "combine" in types and "game" in types:
            report["gate"] = "COMBINE_AND_GAME_CANDIDATES_FOUND_NOT_YET_JOINED"
        print("ASTRA_NFL_REAL_DATA_PARTIAL", json.dumps({
            "file_count": len(files), "gate": report["gate"],
            "sampled_rows": sum(f.get("sampled_rows", 0) for f in files)
        }), flush=True)
    except Exception as exc:
        report.update({"status": "FAIL", "gate": "INPUT_UNAVAILABLE_OR_INVALID",
                       "error_type": type(exc).__name__, "error": str(exc)})
        print("ASTRA_NFL_DATA_GATE_FAIL", type(exc).__name__, str(exc), flush=True)
    report["script_sha256"] = sha256_file(Path(__file__))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report

if __name__ == "__main__":
    outcome = run()
    if outcome["status"] == "FAIL":
        raise SystemExit(2)
