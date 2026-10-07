# AION-ARC v2.4 — Kaggle ARC-AGI-3

**Target:** 100% on the official hidden Kaggle evaluation.  
**Current status:** UNVERIFIED until Kaggle returns an official score.  
**Champion notebook:** `kaggle/AION-ARC-v2.4-persistent-host.ipynb`

Do not submit v2.0, v2.1, v2.2, or v2.3 by mistake. They are retained only as development history. The canonical package is declared in `kaggle/SUBMISSION_MANIFEST.json`.

## What v2.4 adds

- local/offline Duck 27B reasoning base;
- evidence-rated hypotheses and retrodiction before live probes;
- ASTRA HYPOTHESIS TOURNAMENT Ω for competing world models;
- information-gain probe selection;
- ASTRA ACTION-EFFICIENCY Ω with probe budget and shortest-plan BFS;
- host-side rejection of multi-action batches so every prefix is verified;
- host-side prediction checking and semantic repeated-state detection;
- persistent semantic-state memory across Python tool calls;
- persistent known-fatal state/action memory;
- stop on silent level changes even when `level_completed` is missing;
- verified ACTION7 rollback when explicitly requested;
- TARDIGRADE / NO-REPEAT / VERIFY² / ZERO-COST guards.

## Kaggle inputs required

Attach these three upstream datasets exactly as expected by the notebook:

1. `jeroencottaar/taaf-kaggle-source-share`
2. `driessmit1/arc3-vllm-h100-wheelhouse-v3`
3. `driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot`

Internet must remain disabled. No paid external API is required.

## Proof Gate

Static CI, syntax tests and offline packaging checks can only prove that the submission package is internally coherent. They cannot prove a hidden competition score.

- GitHub gates passing: packaging evidence.
- Kaggle official score returned: competition evidence.
- Kaggle official 100%: target PASS.

Until that last condition occurs, the hidden-score status remains **UNVERIFIED**.
