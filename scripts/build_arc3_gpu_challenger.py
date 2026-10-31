"""Build ASTRA v2.7 challenger from ASTRA's own v2.5 research notebook.
No network access, no credentials, no official Kaggle submission.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "kaggle" / "AION-ARC-v2.5-transport-safe.ipynb"
TARGET = ROOT / "kaggle" / "ASTRA-AION-ARC-v2.7-GPU-CHALLENGER.ipynb"

PREFLIGHT = '''import os
from pathlib import Path

TRUE_RERUN = os.environ.get("KAGGLE_IS_COMPETITION_RERUN", "").strip().lower() in ("1", "true")
print("ASTRA_AION_V27_MODE:", "HIDDEN_RERUN" if TRUE_RERUN else "PREFLIGHT")

if not TRUE_RERUN:
    import pandas as pd
    p = Path("/kaggle/working/submission.parquet")
    p.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([["1_0", "1", True, 1]], columns=["row_id", "game_id", "end_of_game", "score"]).to_parquet(p, index=False)
    assert p.is_file() and p.stat().st_size > 0
    assert list(pd.read_parquet(p).columns) == ["row_id", "game_id", "end_of_game", "score"]
    print("ASTRA_AION_V27_PREFLIGHT_PASS", p.stat().st_size)
'''


def cell(source: str) -> dict:
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.splitlines(keepends=True)}


def unwrap(source: str) -> str:
    # Original cells contain a one-line JSON quoted string inside exec(compile()).
    match = re.search(r'exec\(compile\(("(?:(?:\\.)|[^"\\])*")', source, re.S)
    if not match:
        raise ValueError("Original v2.5 cell does not have expected source-preserving wrapper")
    return json.loads(match.group(1))


def build() -> dict:
    original = json.loads(SOURCE.read_text(encoding="utf-8"))
    heads = [
        "# ASTRA AION-ARC v2.7 — GPU LLM challenger (UNVERIFIED ON KAGGLE)\n",
        "\n",
        "Reuses the ASTRA v2.5 TAAF/Duck offline LLM framework and AION overlays, not the random fallback.\n",
        "The original solver and upstream models remain external datasets attached to Kaggle.\n",
        "During Save & Run All, produce only a placeholder submission.parquet for Kaggle verification.\n",
        "During competition hidden rerun, run the full offline GPU agent without internet.\n",
        "The existing official version 6, submission #57848621, remains untouched.\n",
        "No score or improvement over another team is claimed.\n",
    ]
    cells = [{"cell_type": "markdown", "metadata": {}, "source": heads}]
    cells.append(cell('exec(compile(' + json.dumps(PREFLIGHT, ensure_ascii=False) + ', "astra_v27_preflight", "exec"), globals())\n'))
    count = 0
    async_count = 0
    for index, c in enumerate(original["cells"]):
        if c.get("cell_type") != "code":
            continue
        body = unwrap("".join(c["source"]))
        label = "astra_v27_original_" + str(index)
        if "await bm.run(" in body:
            # Original v2.5 had a nested exec(compile(...)) that would reject top-level await.
            expression = (
                "await eval(compile(" + json.dumps(body, ensure_ascii=False)
                + ", " + repr(label)
                + ', "exec", flags=__import__("ast").PyCF_ALLOW_TOP_LEVEL_AWAIT), globals()) if TRUE_RERUN else None'
            )
            async_count += 1
        else:
            expression = (
                "exec(compile(" + json.dumps(body, ensure_ascii=False)
                + ", " + repr(label) + ', "exec"), globals()) if TRUE_RERUN else None'
            )
        cells.append(cell("# AION original cell " + str(index) + "; hidden rerun only\n" + expression + "\n"))
        count += 1
    assert count == 16 and async_count == 1, (count, async_count)
    for index, c in enumerate(cells):
        if c["cell_type"] == "code":
            compile("".join(c["source"]), "candidate_cell_" + str(index), "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    metadata = dict(original.get("metadata", {}))
    metadata["kaggle"] = {
        "accelerator": "gpu",
        "isInternetEnabled": False,
        "isGpuEnabled": True,
        "enable_gpu": True,
        "enable_internet": False,
        "language": "python",
        "sourceType": "notebook",
        "competition_sources": ["arc-prize-2026-arc-agi-3"],
        "dataset_sources": [
            "jeroencottaar/taaf-kaggle-source-share",
            "driessmit1/arc3-vllm-h100-wheelhouse-v3",
            "driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot",
        ],
    }
    metadata["astra"] = {
        "name": "ASTRA-AION-v2.7-GPU-CHALLENGER",
        "status": "UNVERIFIED_KAGGLE",
        "comparison": "NOT_SCORED",
        "original_submission_preserved": 57848621,
    }
    return {"nbformat": 4, "nbformat_minor": 4, "metadata": metadata, "cells": cells}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    notebook = build()
    output = json.dumps(notebook, indent=1, ensure_ascii=False) + "\n"
    if not args.check:
        TARGET.write_text(output, encoding="utf-8")
    print("ASTRA_V27_STATIC_GATE_PASS: cells=" + str(len(notebook["cells"])) + "; bytes=" + str(len(output)) + "; check_only=" + str(args.check))
    print("ASTRA_V27_KAGGLE_SCORE: UNVERIFIED")


if __name__ == "__main__":
    main()
