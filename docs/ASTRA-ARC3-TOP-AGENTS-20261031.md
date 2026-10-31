# ASTRA AION-ARC Ω — Top ARC-AGI-3 agents, 31 October 2026

Status: research-only; not an official Kaggle score.

Public Kaggle leaderboard (31 Oct): Yi-Chia Chen @ Fields Model 75.56; Tufa Labs 70.02; third 58.59. Source https://arc.markbarney.net/arc-leaderboards

Tufa Labs publishes Duck Harness, an offline tool-using LLM solver with TAAF. Source: https://github.com/Tufalabs/duck-harness

NVIDIA AVO reached 100.00 on 25 **public** ARC3 games using Claude Opus 5, not the Kaggle hidden competition. Architecture: persistent memory, supervision and long-horizon recovery. Source https://developer.nvidia.com/blog/nvidia-avo-reaches-100-on-arc-agi-3-demonstrating-a-frontier-level-general-purpose-architecture-for-long-horizon-autonomous-agents/

BDR-Pro reports programmatic heuristics overfit public games and transfer poorly to Kaggle hidden games. Source https://github.com/BDR-Pro/arc-prize-2026-arc-agi-3

ASTRA decision: preserve official submission #57848621 (version 6). Baseline agent is random; Kaggle hidden score unverified. Existing AION v2.5 has GPU Duck/TAAF backbone, but has a transport hazard: its nested Python compile(mode=exec) wraps a top-level await bm.run, which may fail without PyCF_ALLOW_TOP_LEVEL_AWAIT. A challenger must (1) make Save & Run All produce valid preflight Parquet; (2) reserve heavy GPU solve for official rerun; (3) compile top-level async correctly; (4) verify Kaggle output and score; (5) never claim superiority from static tests.

ARC3 conditional 700000 USD bonus requires 100% and is shared according to contest rules, not a guaranteed individual prize. Official: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview/prizes
