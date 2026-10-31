# AION ARC-AGI-3 — third-party license audit

**Audit date:** 2026-10-12 UTC. **Overall: PARTIAL / UNVERIFIED for Kaggle prize eligibility**. The following is a provenance/technical compliance audit, not a legal opinion.

## Results by independently verifiable source

| Component | Primary provenance and what was actually verified | Status |
|---|---|---|
| Original AION contributions | Owner authorized MIT-0 on 2026-10-12. [LICENSE](../LICENSE) and [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) at the repo root scope this to code/methods owned by AION only | **PASS — original contributions only** |
| Tufa Labs Kaggle source notebook | [Public Tufa winning notebook](https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner) visibly declares **Apache-2.0**, and attributes the Tufa team | **PASS — public notebook license statement** |
| Tufa Labs Duck GitHub harness and bundled TAAF | [Tufalabs/duck-harness](https://github.com/Tufalabs/duck-harness). GitHub API on 2026-10-12 returned `license: null`; automated recursive tree of **3,587 ordinary files** found **no root or nested LICENSE/NOTICE/COPYING** matching standard filenames. `ARC3-Inference/pyproject.toml` contains a `MIT License` classifier but no license grant text | **UNVERIFIED — source redistribution rights** |
| Public Qwen FP8 model | [vrfai/Qwen3.6-27B-FP8](https://huggingface.co/vrfai/Qwen3.6-27B-FP8) Hugging Face metadata: **apache-2.0** at revision `70462b01826175b3f45fa80065184167ddc973fb` | **PASS — public model-card declaration** |
| Public base Qwen model | [Qwen/Qwen3.6-27B](https://huggingface.co/Qwen/Qwen3.6-27B) model metadata: **apache-2.0** at revision `6a9e13bd6fc8f0983b9b99948120bc37f49c13e9` | **PASS — public model-card declaration** |
| Kaggle TAAF source archive | [jeroencottaar/taaf-kaggle-source-share](https://www.kaggle.com/datasets/jeroencottaar/taaf-kaggle-source-share); not accessible from this GitHub-only runtime as a mounted snapshot | **UNVERIFIED — exact contents, license, accessibility** |
| Kaggle vLLM wheelhouse | [driessmit1/arc3-vllm-h100-wheelhouse-v3](https://www.kaggle.com/datasets/driessmit1/arc3-vllm-h100-wheelhouse-v3) contains wheels potentially under multiple licenses | **UNVERIFIED — actual wheel metadata, license notices** |
| Kaggle quantized weights snapshot | [driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot](https://www.kaggle.com/datasets/driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot). Upstream HF model-card license does **not** prove that this Kaggle archive has identical contents or notices | **UNVERIFIED — exact snapshot** |
| Competition SDK | Kaggle ARC-AGI-3 offline wheels | **UNVERIFIED — actual wheel license inventory** |

## Maintainer clarification already requested (do not open duplicate issues)

Two existing public requests about the absent Tufa repo license have **no response as of this audit**:

- [Tufalabs/duck-harness issue #6](https://github.com/Tufalabs/duck-harness/issues/6): documents missing LICENSE in source/harness and the MIT classifier.
- [Tufalabs/duck-harness issue #8](https://github.com/Tufalabs/duck-harness/issues/8): asks for explicit rights for downstream competition use.

Neither a bare MIT classifier nor an informal claim to be "open-source" substitutes for the operative license grant. The public **Kaggle notebook** is declared Apache-2.0, but the separately downloaded TAAF source is **not thereby proven to be covered**. No AION source file has been relabeled as Tufa-owned or vice versa.

## Actions already implemented

1. Owner-approved [MIT-0 root license](../LICENSE) on `main`, `arc3-kaggle-100`, and experimental branch.
2. [Third-party scope notice](../THIRD_PARTY_NOTICES.md) on all three branches; MIT-0 explicitly excludes third-party portions.
3. Standard **Apache License 2.0** text from the [SPDX canonical license list](https://github.com/spdx/license-list-data/blob/main/text/Apache-2.0.txt) copied to [THIRD_PARTY_LICENSES/Apache-2.0.txt](../THIRD_PARTY_LICENSES/Apache-2.0.txt) on all three branches, preserving license text without pretending the archive is licensed.
4. The Kaggle packager embeds MIT-0, Apache-2.0 and source/scope notices as a **markdown-only notebook cell**, for both champion and challenger; code cell order remains unaltered. This is packaging proof, **not Kaggle runtime proof**.
5. [Automated audit script](../scripts/arc3_upstream_license_audit.py) queries GitHub and Hugging Face public metadata, emits UTC JSON and archives it via GitHub Actions. Every Kaggle archive remains UNVERIFIED. Unit tests intentionally reject false PASS.
6. The strict prize-eligibility job remains **FAIL** until independently verifiable final-game, Kaggle, and license evidence is available.

## Before competition/licensing PASS

- Obtain explicit Tufa author/repository grant covering **actual** Duck/TAAF source used by the source archive; preserve author notices and check Apache-2.0 NOTICE requirements.
- Inspect each actual Kaggle-mounted archive and the offline wheel LICENSE/METADATA files in the Kaggle runtime; compare the model snapshot to an approved version.
- Confirm exact wheel/model terms permit the distribution/usage required by competition rules.
- Produce a real offline Kaggle notebook run (within hardware/time limits) and an authenticated submission/leaderboard score.
- Do not merge the v2.6 experimental algorithm unless paired-game evidence improves actual results.

**Rules:** https://arcprize.org/competitions/2026 and https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview

**GitHub proof run:** https://github.com/Dr-starck66/AION-ARC/actions/runs/38307346916 (live license metadata probe on public sources).
