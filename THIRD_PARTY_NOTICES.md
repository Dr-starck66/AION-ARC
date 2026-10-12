# License scope and third-party notices

**AION-ARC original contributions: MIT-0 (MIT No Attribution).**

This repository's root [LICENSE](LICENSE) applies **only** to code, methods and documentation originally authored by the AION-ARC submitter(s) and for which they control the necessary rights. The authorized original contributions include AION's original agent logic in `astra_arc/`, AION-created guard/reference and test code, original utilities/scripts, and original AION-specific notebook modifications, **only to the extent independently authored**. This license does **not** relicense material owned by others, even where embedded in a mixed file.

**Third-party components are NOT licensed here under MIT-0 by the AION-ARC submitter.** Each remains governed by its own rights and conditions.

| Source | Where used | Current rights status |
| --- | --- | --- |
| Tufa Labs Duck / TAAF baseline notebook and solver | `kaggle/AION-ARC-v2.*.ipynb` notebooks are adaptations; Tufa source is mounted via Kaggle dataset `jeroencottaar/taaf-kaggle-source-share` | The Tufa Labs Kaggle notebook carries an Apache-2.0 indication, but the full source bundle and its notices still require verification; no blanket MIT-0 claim |
| Tufa Labs GitHub `Tufalabs/duck-harness` | Source/harness reference | No root LICENSE detected at audit time. Verify upstream file-level terms and any accompanying grant |
| ARC Prize SDK / wheels, `arc-agi` | Kaggle offline competition wheels and runtime | Independently licensed; verify package terms |
| vLLM offline wheels | `driessmit1/arc3-vllm-h100-wheelhouse-v3` | Independently licensed dependencies; retain third-party LICENSE/NOTICE |
| Qwen3.6 model snapshot | `driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot` | Model weights and model terms independent; verify exact mounted snapshot |

AION contributions to mixed Kaggle notebooks are MIT-0 *only for the original additions*; preceding/embedded Tufa code retains upstream licensing. This file records scope, not an authorization to distribute unverified third-party source or model weights.

**Open issues before prize eligibility PASS:** audit the bundled third-party license and NOTICE files, legal ability to redistribute and publish all methods, and the official Kaggle reproducibility/score gate.

References: https://spdx.org/licenses/MIT-0 ; https://arcprize.org/competitions/2026 ; https://github.com/Tufalabs/duck-harness ; see `docs/UPSTREAM-ATTRIBUTION-AND-LICENSE.md` on the experiment branch for finer-grained audit.
