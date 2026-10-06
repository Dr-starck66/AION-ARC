# AION-ARC v2.2 — Winning Architecture Gate

Status vocabulary: PASS / PARTIAL / FAIL / UNVERIFIED. No hidden-score claim without Kaggle evidence.

## Layered agent

1. **Fast floor — deterministic scientist**
   - stable/volatile frame separation
   - connected components + relations
   - legal-action signature
   - state graph and repeated-edge detection
   - ACTION7 recovery
   - bounded BFS/beam search once dynamics are confirmed

2. **Human-efficiency prior**
   - exploit public human replays only as a general prior: action-profile families, frame-change prediction, object/interaction priors
   - never ship game IDs, solutions, coordinates or private-game assumptions
   - winning and losing replay transitions both matter; learn causal differences, not memorized routes

3. **Slow rescue — local 27B Duck reasoner**
   - invoked for ambiguity/stall/novel mechanics
   - must produce falsifiable hypothesis + prediction before acting
   - Python/search tool preferred over speculative probes

4. **ASTRA ARC MEMORY**
   - transition ledger: semantic state, action, predicted effect, observed effect, outcome class, confidence
   - successful trajectories compressed to minimal plan skeletons
   - failed trajectories preserve counterexamples and dead ends

5. **TARDIGRADE recovery**
   - checkpoint before risky plans
   - abort on prediction mismatch, legal-action change, level change, cycle or terminal state
   - re-ground from checkpoint; verified ACTION7 before RESET when applicable

6. **VERIFY² / adversarial gate**
   - confirmed mechanics must explain observed transitions and survive counterexample search
   - alternative explanations remain explicit until discriminated
   - no batch execution on candidate mechanics

## Evaluation ladder

A candidate may reach Kaggle only after:
- packaging/AST parse gate PASS
- offline smoke PASS
- 25-public-game sweep completed
- independent RHAE recomputation agrees with official scorecard
- no regression in levels completed versus champion
- action count improvement reported separately from completion improvement
- at least two deterministic seeds/config repetitions for changed stochastic components
- candidate manifest records model, datasets, budgets and commit SHA

A public-game improvement is evidence, not proof of private generalization. Hidden Kaggle score remains UNVERIFIED until returned by Kaggle.

## Next implementation target

Build a host-side semantic transition ledger and plan-prefix verifier rather than relying only on prompt instructions. The host must be able to stop a multi-action sequence independently of the LLM when:
- predicted semantic delta fails,
- stable-state hash repeats unexpectedly,
- legal actions change,
- level changes,
- terminal state appears,
- a known negative edge is revisited.

This is the highest-priority structural upgrade because it converts AION's verification rules from advice into enforcement.
