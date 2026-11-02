"""Reuse v29; expose actual transient animation frames, not composites."""
from __future__ import annotations

import ast
import json
from pathlib import Path

from build_arc3_milestone2_challenger import build as build_v29, wrap

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "kaggle/v31-animation/submission.ipynb"
ANIMATION = '''
# Perception experiment: append a real intermediate frame when an animation
# otherwise disappears, including at game over. No synthetic composite image.
# Retain v29 controls, guards, model, scheduler and hidden evaluation budget.
os.environ.update({
    "ARC3_ANIMATION_IMAGE": "peak",
    "ARC3_ANIMATION_DEATH_IMAGE": "peak",
})
print("ASTRA_ANIMATION_EXPERIMENT", {k: os.environ[k] for k in
      ("ARC3_ANIMATION_IMAGE", "ARC3_ANIMATION_DEATH_IMAGE")}, flush=True)
'''


def build() -> dict:
    notebook = build_v29()
    for index, original in enumerate(notebook["cells"]):
        if original.get("id") == "astra-v29-source-4":
            expression = ast.parse("".join(original["source"]))
            body = expression.body[0].value.args[0].args[0].value
            assert isinstance(body, str)
            notebook["cells"][index] = wrap(body + ANIMATION, original["id"])
            break
    else:
        raise RuntimeError("Base setup cell not found")
    notebook["cells"][0]["source"] = [
        "# ASTRA AION-ARC v3.1 — actual animation frame experiment\n",
        "Reuses v29 with automatic peak-frame images for transient animations and game-over animations.\n",
        "Preserves the original controls and guards, model weights, scheduler and hidden budget.\n",
        "Baseline official public score: 24.58, submission 57886365. Challenger official score UNVERIFIED.\n",
        "Public comparison: same two games and 300-second budget. One stochastic run does not establish causality.\n",
        "Third-party notices remain below.\n",
    ]
    notebook["metadata"]["astra"].update({
        "version": "3.1-animation-experimental",
        "baseline_submission": 57886365,
        "baseline_official_public_score": 24.58,
        "animation_image": "peak",
        "animation_death_image": "peak",
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
