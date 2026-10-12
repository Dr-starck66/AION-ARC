# AION-ARC license decision — ACTION REQUIRED (2026-10-12)

**This document is a proposal, NOT a license grant.** Do not assume that a GitHub public repository is automatically open-source licensed.

## Current verified failures

- AION-ARC roots `main`, `arc3-kaggle-100`, and `arc3-v26-recovery-experiment` contain no `LICENSE`, `LICENSE.md`, `LICENSE.txt` or `COPYING` at repo root (checked via connected GitHub API 2026-10-12).
- ARC Prize 2026 official rules require **submitter-authored code and methods** to be permissively open-sourced (examples **CC0** and **MIT-0**). Prize-eligible third-party components must separately carry an appropriate open-source/public-sharing license. Source: https://arcprize.org/competitions/2026
- The Tufa Labs `duck-harness` public GitHub root also has no detectable root `LICENSE`: https://github.com/Tufalabs/duck-harness. A Kaggle notebook may declare a license, but that does not by itself establish rights to every attached dataset and bundled file. Validate the actual Kaggle Notebook and source bundle license/notice.

## Safe license plan — awaiting the contributor/rightsholder's approval

1. Establish copyright and ownership of each original AION file. Inventory `astra_arc/`, `tests/`, `scripts/`, the AION-specific notebook patch cells, and docs, excluding any code copied from Tufa or ARC SDK.
2. With explicit authorization from the owner(s), publish **MIT-0** for original AION portions only, using exact official OSI text: https://opensource.org/license/mit-0. Include a root `LICENSE` describing scope or a carefully drafted `LICENSE` plus `THIRD_PARTY_NOTICES.md` and per-file SPDX identifiers. Never assume rights to sublicense third-party code.
3. Retain all upstream copyright notices, Apache-2.0 license and any `NOTICE` files when actually present and verified. Check Kaggle wheelhouse and Qwen model weights separately.
4. Re-run license audit, archive exact file commit SHAs, verify competition-specific winner licensing conditions. Ensure Kaggle published notebook/methods reflect permitted license scope.
5. Official score stays **UNVERIFIED** until an authenticated Kaggle leaderboard entry is obtained.

## Publishing decision

Do not create a root `LICENSE` for the user on the assumption that committing one grants rights over the entire blended notebook. A **proposed** MIT-0 choice is not effective until confirmed by the copyright owner. The automated release gate deliberately FAILS while no root license is present; it continues to mark third-party rights UNVERIFIED even after a root license appears.

Recommended approval text to obtain before publishing: *"I authorize releasing the original AION-ARC code and methods for which I control the rights under MIT-0, while retaining and separately respecting all third-party licenses."*

See [licensing register](UPSTREAM-ATTRIBUTION-AND-LICENSE.md).
