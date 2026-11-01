# Kaggle execution evidence — 1 November 2026

This is a work log, not a score claim. The original successful submission
57848621 (notebook2700e63354 v6, public 0.07) is preserved. No new official
submission has been made at this checkpoint.

## Live executions

| Version | Kaggle scriptVersionId | Observed state | Evidence |
|---|---:|---|---|
| v2.8 recovery | 364606055 | FAIL | Actual 12.1-second RTX PRO 6000 run; Python 3.13.15 cannot install the cp312-only aiohttp 3.13.5 wheel |
| v2.8 pinned recovery | 364607203 | PARTIAL — running | Original environment pinned to 2026-05-26; actual Python 3.12.13 and 97887 MiB RTX PRO 6000; wheelhouse installation succeeded; local model loading |
| v2.9 Milestone 2 comparison | 364609200 | PARTIAL — running | Same pinned environment; 5 inputs inherited; harness patch applied and SGLang 0.5.19 / torch 2.13.0+cu130 installed offline; local model loading |

- [Failed v2.8 run](https://www.kaggle.com/code/drstarck/astra-aion-arc3-v2-8-recovery?scriptVersionId=364606055)
- [Corrected v2.8 run](https://www.kaggle.com/code/drstarck/astra-aion-arc3-v2-8-pinned-recovery?scriptVersionId=364607203)
- [v2.9 run](https://www.kaggle.com/code/drstarck/astra-aion-arc3-v2-9-milestone2?scriptVersionId=364609200)

Required v2.8 inputs were actually attached, then validated by notebook code.
Two deleted historical input versions inherited from the July source were
removed from the new draft and replaced with the current public versions.
Internet remains off. Kaggle displayed 29 free GPU hours remaining.

The v2.8 Python incompatibility was corrected through the inherited original
Docker environment, not by forcing incompatible binary wheels. Future builds
now reject Python versions other than 3.12 early. Accelerator metadata was
aligned with the `nvidiaRtxPro6000` value exported by Kaggle's public notebook.
These metadata/preflight edits postdate the two live uploads; upload hashes
are recorded separately in the machine-readable progress file.

## More competitive comparison

The [public Daniel Franzen Milestone 2 notebook](https://www.kaggle.com/code/dfranzen/arc-agi-3-milestone-2-solution)
was directly inspected and downloaded from Kaggle v3 / 354920985. Its page
showed public 33.68 and best 34.30 v1. These are the author's scores, not ours.
His [primary write-up](https://github.com/da-fr/arc-agi-3-solution/blob/main/WRITEUP.md)
describes newer-model inference, animation access, image differences, undo,
retained functions, larger context and scheduling. It also reports no clear
benefit from several stricter verification and remembered-action guards.
That supports testing the published configuration before adding more guards.

v2.9 reuses the Tufa/Duck lineage and ASTRA v2.8's model/environment telemetry
and gameplay gate. It retains all upstream attribution. It compares ls20 and
vc33, one pass and 1800 seconds after setup, with v2.8 on the same games.
Both model and harness change, so this is a system comparison, not a causal
ablation. Competition reruns retain the source competition configuration and
use the complete gateway game list; the public filter is absent there.

## Local validation

- PASS: 13 v2.8 regression and negative-control tests via unittest after the
  environment metadata correction. Earlier full-suite results are separate.
- PASS: v2.9 generated 26 cells, all executable bodies compiled.
- PASS: its exact public patch applied to Duck commit
  7652836056c59e044f093e3c13ed7438c814169e; 34 generated Python files and the
  embedded sandbox bootstrap compiled.
- A real negative control found a corrupt patch if IPython's writefile trailing
  newline is omitted. The transport-safe conversion now preserves that newline.

Kaggle gameplay, official submission ID, improved score and score 100 remain
UNVERIFIED until returned by the actual runs and competition service.
