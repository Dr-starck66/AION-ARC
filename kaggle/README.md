# AION-ARC v2.0 — Kaggle ARC-AGI-3

**Target:** 100% on the official hidden Kaggle evaluation.  
**Current status:** UNVERIFIED until Kaggle returns an official score.  

This branch intentionally does not touch the polluted main branch. The submission notebook uses the public Tufa Labs Duck Kaggle harness as the execution base and adds an original AION verification overlay before the benchmark is unpickled.

## Added control gates

- evidence-rated action/world hypotheses;
- retrodiction against recorded transitions before spending live actions;
- explicit expected gameplay effects for every live action;
- short verified plans with immediate abort on mismatch;
- bounded search / explicit transition-model escalation when stuck;
- ACTION7-first recovery and anti-RESET thrashing;
- fail-closed patch anchors so upstream changes cannot silently disable the overlay.

## Kaggle inputs required

Keep the three upstream datasets attached exactly as in the public Duck notebook: TAAF source bundle, ARC3 vLLM wheelhouse, and the vrfai Qwen3.6 27B FP8 snapshot. Internet must remain disabled. Use a GPU accelerator.

## Proof Gate

A local/offline successful notebook run proves packaging only. It is **not** proof of hidden score. PASS for the competition requires an official Kaggle score; 100% requires Kaggle itself to report 100.
