# AION ARC-AGI-3 — upstream attribution & licensing audit (updated 2026-10-12)

**Original AION contributions: MIT-0 published, authorized. Full prize-eligibility rights: UNVERIFIED.** Publication of our own license does not grant rights over any third-party assets.

## Upstream materials and known public evidence

| Component | Provenance | Public license evidence | Status |
|---|---|---|---|
| AION original code/methods | Project's own `astra_arc/`, AION-created tests, utilities and notebook *additions* only to extent independently authored | Owner authorized MIT-0 on 2026-10-12; [LICENSE](../LICENSE) and [THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md) exist on three active branches | **PASS for licensed original contributions only** |
| Tufa Labs Duck notebook/harness template | Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit, Michal Tešnar, Stefano Viel; upstream https://github.com/Tufalabs/duck-harness | Kaggle notebook has Apache-2.0 indication; inspect exact Tufa notebook and bundle; do not infer all bundled files licensed | **PARTIAL / UNVERIFIED exact scope** |
| Tufa Labs source dataset | `jeroencottaar/taaf-kaggle-source-share` | Upstream GitHub root lacked a root LICENSE at the time checked; notebook license not automatic coverage of all attached code | **UNVERIFIED** |
| Offline vLLM wheels | `driessmit1/arc3-vllm-h100-wheelhouse-v3` | Separate upstream wheel licenses | **UNVERIFIED** |
| Qwen3.6 27B FP8 weights | `driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot` | Model weights and dataset snapshot terms must be checked individually | **UNVERIFIED** |
| ARC Prize offline SDK and runtime wheels | Official competition inputs | Independently licensed runtime; need package license inventory | **UNVERIFIED** |

## Required before claiming prize eligibility PASS

1. Inspect Tufa source dataset for LICENSE, NOTICE, per-file copyright headers and redistribution scope. Record exact origin/versions.
2. Verify requirements for bundling the notebook and distributing solver source; preserve every required third-party notice.
3. Inspect precise vLLM, Qwen model and ARC SDK license metadata, and ensure lawful publication of the final solution/methods.
4. Check compatibility with Kaggle's and ARC Prize's current rules, public reproducibility and no-Internet restrictions.
5. Obtain an official Kaggle submission result; **no source code or CI log alone proves eligibility or score**.

Reference: https://arcprize.org/competitions/2026 and https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview

Prize status: **PARTIAL / UNVERIFIED**, not PASS.
