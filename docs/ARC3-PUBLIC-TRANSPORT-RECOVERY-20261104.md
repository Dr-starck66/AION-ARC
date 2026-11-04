# ASTRA ARC-AGI-3 — Public API transport recovery (2026-11-04)

## Verified independently
An existing ASTRA/Floot VM executed the original ARC public API with Python stdlib and persisted the same HTTP cookie jar across all requests. This restored the ability to initialize a real game, send one valid action, and close the scorecard without external payment or API credentials.

The old implementation lost cookies between API calls. `POST /api/cmd/RESET` incorrectly returned `400 SERVER_ERROR / game <id> not found`. Reusing one cookie-aware opener fixed the transport failure.

- Runtime: Python 3.11.2; no third-party Python dependency.
- Live test: `ls20-9607627b`; catalog 25 games; RESET HTTP 200; ACTION1 HTTP 200; close HTTP 200.
- Remote scorecard score = 0.0, expected for one smoke-test action, **NOT** an AION solver score.
- Evidence: [real-api-probe.json](../reports/arc3-transport-20261104/real-api-probe.json).
- Local suite: `python3 -m unittest -q tests/test_arc3_public_transport_probe.py kaggle/test_aion_v26_recovery.py tests/test_compare_arc3_runs.py` — **19/19 PASS** on the experimental source checkout.

## Reproduce without a Kaggle account
```bash
python3 scripts/arc3_public_transport_probe.py --game-id ls20-9607627b --output reports/arc3-public-test.json
```
This invokes a real game API. By design it executes **one action only** and closes the scorecard. No generated API key, cookies, guid, or scorecard ID is printed or saved.

## Proof boundary
- `PASS`: live public ARC-AGI-3 transport, scorecard open/close and one real action.
- `UNVERIFIED`: SDK 27B solver runs, **v2.5/v2.6 paired seeds**, Kaggle GPU/mounted inputs, official Kaggle score and prize eligibility.
- An anonymous ARC API key is **not** Kaggle account authorization. The VM did not have Kaggle CLI credentials.
- Public API does not expose a verified seed through this probe; this is not an eligible input for the paired score comparator.
- No GitHub Actions, Kaggle submissions, new paid resources or background jobs were created.
