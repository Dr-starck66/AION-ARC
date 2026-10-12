# AION ARC-AGI-3 — upstream attribution & licensing audit (2026-10-12)

**Status: UNVERIFIED for final prize eligibility.** This document records attribution and unresolved rights; it is not itself a license grant.

## Upstream materials and known public evidence

| Component | Provenance | Public license evidence | Status |
|---|---|---|---|
| Tufa Labs "Duck" notebook/harness template | Jeroen Cottaar, Harold Bessis, Isaiah Pressman, Andries Smit, Michal Tešnar, Stefano Viel; Tufa Labs, https://www.kaggle.com/code/jeroencottaar/taaf-duck-harness-kaggle-share | Kaggle notebook explicitly identifies Apache 2.0; https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner | Apache-2.0 stated for that notebook; retain attribution and license notice |
| Tufa Labs Duck source bundle attached from Kaggle | `jeroencottaar/taaf-kaggle-source-share`; project GitHub https://github.com/Tufalabs/duck-harness | Upstream GitHub root has no detected LICENSE (checked 2026-10-12); notebook license does not automatically prove each external bundle is covered | **UNVERIFIED**: check bundled file headers/LICENSE/NOTICE |
| Offline vLLM wheelhouse | `driessmit1/arc3-vllm-h100-wheelhouse-v3` | Multiple bundled packages have independent licenses | **UNVERIFIED**: inventory wheel metadata |
| Qwen3.6 27B FP8 weights | `driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot` | Exact dataset/weights terms not audited | **UNVERIFIED**: read license in pinned snapshot |
| AION `astra_arc/**`, `scripts/**`, `tests/**` and added notebook overlays | AION-ARC repo https://github.com/Dr-starck66/AION-ARC | Owner-approved original-code license not yet present | **UNVERIFIED**: obtain owner's express license and contribution ownership confirmation |

## Necessary before claiming license PASS

1. Identify and preserve all copyright, Apache-2.0 and NOTICE texts from notebook/bundled Tufa code.
2. Inventory all code copied into AION notebooks vs original AION patches and verify allowed adaptation/distribution.
3. Have code owner explicitly authorize the license choice for **only their own contributions**, and add exact license files and SPDX notices. Do not purport to relicense Tufa, wheelhouse, or model weights.
4. Verify license compatibility with ARC Prize's current open-source/reproducibility requirements and official Kaggle rules.
5. Store dated proof of Kaggle consent, actual submission and official score outside source code where appropriate. NEVER commit Kaggle tokens or password material.

Official rules: https://arcprize.org/competitions/2026/arc-agi-3 and https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview

This branch is an experiment and must never be merged based on CI alone. Prize status remains PARTIAL / UNVERIFIED.
