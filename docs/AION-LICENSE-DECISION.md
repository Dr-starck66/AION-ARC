# AION-ARC MIT-0 original-code license decision — IMPLEMENTED 2026-10-12

**Status: PASS for publication of the contributor-controlled original AION-ARC code under MIT-0. Third-party redistribution and full ARC Prize eligibility remain UNVERIFIED.**

On 12 October 2026, the project owner explicitly authorized release of the original AION-ARC contributions under MIT-0, excluding all third-party materials. Following that authorization, these files were published on `main`, `arc3-kaggle-100`, and `arc3-v26-recovery-experiment`:

- [Root LICENSE](../LICENSE): verbatim MIT No Attribution terms, copyright 2026 AION-ARC contributors.
- [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md): scope restricts MIT-0 to original contributions; Tufa Labs, Kaggle/ARC SDK, vLLM wheels and Qwen weights are explicitly excluded from any unilateral relicensing.

## Remaining rights work

The source notebook contains Tufa Labs work and references datasets with independently controlled rights. The root MIT-0 file **does not prove** the complete source bundle, wheels and model weights may be redistributed or satisfy contest-specific publishing requirements.

- Confirm license files/headers and attribution requirements inside the Tufa Labs Kaggle source bundle.
- Check exact wheel and model snapshot licenses/NOTICE texts.
- Preserve upstream notices in any public release and verify compatibility with ARC Prize 2026 rules.
- Confirm the Kaggle notebook itself is licensable for public submission including its original and Tufa-derived portions.
- Do not claim official Kaggle score or prize eligibility before authenticated validation.

Sources: https://spdx.org/licenses/MIT-0 and https://arcprize.org/competitions/2026 ; see [upstream register](UPSTREAM-ATTRIBUTION-AND-LICENSE.md).

**Proof:** `LICENSE` on the three named branches and `THIRD_PARTY_NOTICES.md`; GitHub Action's `project_license` gate verifies the presence/scope. The overall competition/prize gate remains PARTIAL/UNVERIFIED until the independent dependencies and official submission are checked.
