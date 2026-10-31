# AION-ARC v2.6 Recovery Experiment — 2026-10-12

Branch: `arc3-v26-recovery-experiment`. Candidate notebook: `kaggle/AION-ARC-v2.6-recovery.ipynb`.

## Audit finding
In v2.5 a wrong *predicted* transition is stored in `_aion_negative_state_actions` as if the action itself had caused a confirmed fatal loss. Revisit of an already observed semantic signature is also treated as a mismatch. Either can prematurely stop legitimate exploration or permanently forbid a useful action. The previous notebook `v2.4` and `v2.5` were confirmed identical by Git blob SHA.

## Experimental intervention
- A prediction mismatch still aborts the current plan; it does **not** permanently blacklist an action.
- Only `game_over` without `level_completed` or `run_complete` qualifies for host fatal-edge memory (a conservative proxy; must be rechecked against actual API semantics).
- A semantic-state revisit becomes a diagnostic flag rather than a host-enforced stop; the pre-existing action-efficiency governor retains anti-stall protection.
- Keep v2.5 as canonical champion. This experiment MUST NOT auto-promote, nor assert any Kaggle score.

## Proof levels
1. **Static / deterministic**: unittest dynamically applies the actual v2.6 notebook patch to a minimal host fixture; verifies false-negative blacklisting is gone, fatal-memory retained, legitimate revisits continue, original plan mismatch still stops, and anchor drift fails closed. GitHub Actions must be green.
2. **Integration**: execute with actual bundled Tufa host in Kaggle offline run on visible games; record outcomes, actions, runtime and backward-compatible upstream anchors.
3. **A/B score**: paired games/seeds, v2.5 vs v2.6, public score / completion / actions / GPU runtime. Promote only with measured benefit and no material regressions.
4. **Competition**: a user-authorized official Kaggle submission and leaderboard result, which is currently **UNVERIFIED**.

No hosted API or extra paid service is needed. ARC-AGI-3 notebook must run without internet, within the GPU 9-hour limit, and under the competition license rules.

Official competition rules: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview/evaluation
