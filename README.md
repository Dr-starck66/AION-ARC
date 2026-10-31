# AION-ARC — ARC Prize 2026, ARC-AGI-3

> **Competition status: PARTIAL / UNVERIFIED.** AION has not yet produced an authenticated Kaggle score in this repository. Successful GitHub tests do NOT prove competition performance.

## Canonical competitor and safe challenger

- **Champion (frozen reference):** `arc3-kaggle-100/kaggle/AION-ARC-v2.5-generalization.ipynb`
- **v2.6 experiment (draft PR #3):** `kaggle/AION-ARC-v2.6-recovery.ipynb`
- [Competition tracker](https://github.com/Dr-starck66/AION-ARC/issues/4)
- [AION v2.6 adversarial test workflow](https://github.com/Dr-starck66/AION-ARC/actions/workflows/aion-v26-recovery.yml)

## Reproducible preparation (no credentials in source)

```bash
python scripts/arc3_submission_evidence_gate.py --output reports/aion-arc3-evidence.json
python -m unittest discover -s kaggle -p test_aion_v26_recovery.py -v
python -m unittest discover -s tests -p test_arc3_submission_evidence_gate.py -v
python -m unittest discover -s tests -p test_prepare_kaggle_kernel.py -v

# Supply only your PUBLIC Kaggle username. Do not put tokens on command lines.
python scripts/prepare_kaggle_kernel.py --username YOUR_KAGGLE_USERNAME --variant champion
# Creates dist/kaggle/champion/submission.ipynb and kernel-metadata.json

# Optional separate experimental package. Do not replace canonical.
python scripts/prepare_kaggle_kernel.py --username YOUR_KAGGLE_USERNAME --variant challenger
```

After verifying account eligibility, authenticating securely with Kaggle CLI, and checking the three attached datasets:

```bash
kaggle kernels push -p dist/kaggle/champion
```

Monitor the Kaggle kernel run. Only after it completes and produces `submission.parquet` can an authorized Kaggle account submit it to the competition and obtain an official score. Use the canonical champion first; the challenger is a measured experiment and must be compared on paired games before considering promotion. See [submission and proof protocol](docs/AION-ARC-v2.6-experiment.md) and [upstream licensing audit](docs/UPSTREAM-ATTRIBUTION-AND-LICENSE.md).

## Important restrictions and dates

- Entry/accept rules deadline: **October 26, 2026**, 23:59 UTC.
- Final submission: **November 2, 2026**, 23:59 UTC.
- Notebook needs internet **disabled**, freely public offline models/data, GPU run **<= 9 hours**.
- Prize eligibility requires open-sourcing the code and methods and meeting license obligations. Repository's scoped license review is **not yet complete**.

Official: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview

### Evidence levels

`PASS` for static checks never means `PASS` in Kaggle. A valid game run requires actual gameplay evidence; the competition requires the official account/leaderboard result. Never invent a score or call preparatory packaging a submission.
