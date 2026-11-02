"""Reproduce the submitted v29 engine with two opt-in recovery features.

This is an experiment, not a claim of improved hidden-game performance.
Keep v29 reproducible and preserve its official submission as a fallback.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

from build_arc3_milestone2_challenger import build as build_v29, wrap

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "kaggle/v30-recovery/submission.ipynb"
RECOVERY = '''
# Experimental recovery: retain the same model, scheduler and hidden budget.
# RESET restarts the current level because ONLY_RESET_LEVELS is enabled.
# The no-op guard is overridable by immediately insisting on the action;
# use the entire visible board so HUD changes are not discarded as no-ops.
os.environ.update({
    "EXPOSE_RESET": "on",
    "ARC3_NOOP_REPEAT_GUARD": "1",
    "ARC3_NOOP_GUARD_BORDER": "0",
})
print("ASTRA_RECOVERY_EXPERIMENT", {k: os.environ[k] for k in
      ("EXPOSE_RESET", "ARC3_NOOP_REPEAT_GUARD", "ARC3_NOOP_GUARD_BORDER")}, flush=True)
'''


def build() -> dict:
    notebook = build_v29()
    for index, original in enumerate(notebook["cells"]):
        if original.get("id") == "astra-v29-source-4":
            expression = ast.parse("".join(original["source"]))
            body = expression.body[0].value.args[0].args[0].value
            assert isinstance(body, str)
            notebook["cells"][index] = wrap(body + RECOVERY, original["id"])
            break
    else:
        raise RuntimeError("Base setup cell not found")
    notebook["cells"][0]["source"] = [
        "# ASTRA AION-ARC v3.0 — recovery experiment\n",
        "Reuses the v29 engine and its sources without changing weights, scheduler or hidden budget.\n",
        "Adds level RESET and the upstream overridable no-op repeat guard using the full visible board.\n",
        "Baseline: official public score 24.58, submission 57886365, notebook version 4. Preserved unchanged.\n",
        "Normal run: same two games and 300-second budget as v29. Random sampling means one run is not a causal ablation.\n",
        "Challenger official score UNVERIFIED. Third-party notices remain below.\n",
    ]
    notebook["metadata"]["astra"].update({
        "version": "3.0-recovery-experimental",
        "baseline_submission": 57886365,
        "baseline_official_public_score": 24.58,
        "recovery": ["level-reset", "overridable-full-frame-noop-guard"],
    })
    return notebook


if __name__ == "__main__":
    notebook = build()
    TARGET.parent.mkdir(exist_ok=True)
    TARGET.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n")
    metadata = json.loads((ROOT / "kaggle/v29-milestone2/kernel-metadata.json").read_text())
    (TARGET.parent / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "scope": "generation and compilation only",
                      "cells": len(notebook["cells"]), "official_score": "UNVERIFIED"}))
