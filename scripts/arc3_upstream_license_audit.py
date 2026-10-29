"""AION ARC3 public upstream-license evidence collector.

This is a GitHub Actions / local CI audit, never run inside offline Kaggle.
Only exact public source metadata is checked. Public metadata cannot prove that
copies inside a Kaggle dataset contain the same license or exact source files.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import urllib.error
import urllib.request

GITHUB_REPO = "Tufalabs/duck-harness"
MODEL_IDS = ("vrfai/Qwen3.6-27B-FP8", "Qwen/Qwen3.6-27B")
INPUTS = (
    "jeroencottaar/taaf-kaggle-source-share",
    "driessmit1/arc3-vllm-h100-wheelhouse-v3",
    "driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot",
)
PUBLIC_NOTEBOOK = "https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner"


def request_json(url: str):
    req = urllib.request.Request(
        url, headers={"User-Agent": "AION-ARC-license-audit/1.0", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=18) as response:
        return json.load(response)


def _reason(exc: Exception) -> str:
    return type(exc).__name__ + ": public metadata unavailable"


def inspect(fetch=request_json, timestamp: str | None = None) -> dict:
    rows = []
    def add(item, status, source, **extra):
        rows.append({"component": item, "status": status, "source": source, **extra})

    repo_url = f"https://api.github.com/repos/{GITHUB_REPO}"
    try:
        repo = fetch(repo_url)
        if not isinstance(repo, dict) or "default_branch" not in repo:
            raise ValueError("incomplete repository metadata")
        branch = repo["default_branch"]
        tree_url = f"{repo_url}/git/trees/{branch}?recursive=1"
        tree = fetch(tree_url)
        if not isinstance(tree, dict) or not isinstance(tree.get("tree"), list) or tree.get("truncated"):
            raise ValueError("missing/truncated upstream tree")
        names = [entry.get("path", "") for entry in tree["tree"] if entry.get("type") == "blob"]
        names = [x for x in names if isinstance(x, str)]
        legal = [p for p in names if p.rsplit("/", 1)[-1].lower() in (
            "license", "license.md", "license.txt", "licence", "licence.md", "copying",
            "copying.md", "notice", "notice.txt",
        )]
        upstream_license = repo.get("license")
        if legal and upstream_license and upstream_license.get("spdx_id") not in (None, "NOASSERTION"):
            status = "PARTIAL"
            detail = "License metadata/file visible; scope for Kaggle source bundle not verified"
        else:
            status = "UNVERIFIED"
            detail = "No verifiable license grant for full GitHub harness/source (public source != reusable)"
        add("tufa_github_source", status, repo_url,
            upstream_head=repo.get("default_branch"),
            tree_complete=True, file_count=len(names), license_files=legal,
            github_spdx=(upstream_license or {}).get("spdx_id"), detail=detail)
    except (ValueError, TypeError, KeyError, urllib.error.URLError, TimeoutError) as exc:
        add("tufa_github_source", "UNVERIFIED", repo_url, detail=_reason(exc))

    for model_id in MODEL_IDS:
        url = "https://huggingface.co/api/models/" + model_id
        try:
            model = fetch(url)
            if not isinstance(model, dict):
                raise ValueError("invalid model metadata")
            card = model.get("cardData") or {}
            tags = model.get("tags") or []
            license_name = card.get("license")
            if not license_name:
                matches = [str(tag)[8:] for tag in tags if str(tag).startswith("license:")]
                license_name = matches[0] if matches else None
            good = license_name == "apache-2.0"
            add("hf_model:" + model_id, "PASS" if good else "UNVERIFIED", url,
                declared_license=license_name, model_revision=model.get("sha"),
                detail=("Public model card declares Apache-2.0; Kaggle snapshot copy NOT verified"
                        if good else "Public model license not positively verified"))
        except (ValueError, TypeError, urllib.error.URLError, TimeoutError) as exc:
            add("hf_model:" + model_id, "UNVERIFIED", url, detail=_reason(exc))

    # The public Kaggle notebook license is separately web-verified as Apache-2.0.
    # Dataset metadata/public status does not establish exact archive contents.
    add("tufa_kaggle_notebook", "PARTIAL", PUBLIC_NOTEBOOK,
        declared_license="Apache-2.0",
        detail="Kaggle public notebook page displays Apache-2.0; bundled TAAF/Duck source not covered automatically")
    for dataset in INPUTS:
        url = "https://www.kaggle.com/datasets/" + dataset
        add("kaggle_dataset:" + dataset, "UNVERIFIED", url,
            detail="Exact snapshot rights, file-level LICENSE/NOTICE and live Kaggle mount accessibility not authenticated")
    status = "FAIL" if any(r["status"] == "FAIL" for r in rows) else (
        "PARTIAL" if any(r["status"] in ("PARTIAL", "UNVERIFIED") for r in rows) else "PASS"
    )
    return {
        "schema": 1,
        "checked_utc": timestamp or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "policy": "PUBLIC_LICENSE_METADATA_IS_NOT_KAGGLE_SNAPSHOT_PROOF",
        "checks": rows,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=Path("reports/aion-arc3-upstream-licenses.json"))
    p.add_argument("--strict", action="store_true", help="Fail unless all sources have complete license evidence")
    args = p.parse_args()
    report = inspect()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(report, indent=2, sort_keys=True) + "\n"
    args.output.write_text(data, encoding="utf-8")
    print(data)
    if report["status"] == "FAIL" or (args.strict and report["status"] != "PASS"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
