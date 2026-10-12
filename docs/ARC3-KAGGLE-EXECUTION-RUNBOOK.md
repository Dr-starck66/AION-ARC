# Operational ARC-AGI-3 Kaggle handoff — 12 Oct 2026

Official Kaggle page: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview
Official starter documentation: https://github.com/arcprize/docs/blob/main/arc-prize-2026.mdx

## What is done in GitHub
- Canonical `v2.5` manifest is frozen.
- Challenger `v2.6` is a separate notebook with anti-false-stop recovery logic.
- An adversarial test gate runs on GitHub Actions with archived JSON status; partial status is **not hidden leaderboard proof**.
- `prepare_kaggle_kernel.py` generates an offline private notebook and metadata with three declared inputs, no Kaggle token and no API calls.
- Git ignores `.kaggle/`, `kaggle.json`, `dist/` and secrets to reduce accidental disclosures.

## Necessary actions that cannot be certified by GitHub alone
1. Account owner completes Kaggle competition rules acceptance and any required identity verification **before Oct 26**. No assistant can accept for the account.
2. Owner securely authorizes the Kaggle CLI on a trusted machine (do not paste token into ChatGPT or commit in repo).
3. Verify that all three pinned Kaggle datasets and model snapshot are actually accessible. Model/GPU compatibility has not been demonstrated for our AION notebook.
4. Run `python scripts/prepare_kaggle_kernel.py --username YOUR_KAGGLE_USERNAME --variant champion`. Check generated `dist/kaggle/champion/kernel-metadata.json` is private and has internet disabled.
5. With authorized Kaggle CLI, run `kaggle kernels push -p dist/kaggle/champion`.
6. Inspect Kaggle output logs, GPU memory, action traces, and `submission.parquet`; use Kaggle's official submission action only after it completed. Obtain score screenshot/url and numeric score from the Kaggle dashboard. Dataset provenance and official score still need verification.
7. Compare challenger on same visible games/seeds using `python scripts/compare_arc3_runs.py champion.json candidate.json` after generating authentic per-game records. Never claim the JSON comparator authenticates data by itself.
8. Before prize eligibility claims, verify code licenses and open-source scope as described in `docs/UPSTREAM-ATTRIBUTION-AND-LICENSE.md`.

## Promotion/rollback
A v2.6 CI PASS is not enough. No merge/promotion without actual game score, action efficiency, GPU runtime, reproducible logs, and licensing evidence. If v2.6 underperforms, retain the 2.5 champion.

All dates and hardware restrictions should be revalidated against Kaggle at actual submission time.
