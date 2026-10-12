"""AION ARC-AGI-3 release evidence gate.

Honest-by-default: structural proof != GPU execution != official Kaggle score.
No self-reported URL or local score is sufficient to mark the competition PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = "kaggle/AION-ARC-v2.5-generalization.ipynb"
CHALLENGER = "kaggle/AION-ARC-v2.6-recovery.ipynb"
REQUIRED_DATASETS = {
    "jeroencottaar/taaf-kaggle-source-share",
    "driessmit1/arc3-vllm-h100-wheelhouse-v3",
    "driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root: Path = ROOT) -> dict:
    checks = []
    def add(name: str, status: str, detail: str, **extra) -> None:
        checks.append({"check": name, "status": status, "detail": detail, **extra})

    manifest_path = root / "kaggle" / "SUBMISSION_MANIFEST.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        add("manifest", "FAIL", f"{type(exc).__name__}: missing/invalid canonical manifest")
        return {"status": "FAIL", "checks": checks}
    if (manifest.get("champion_notebook") != CANONICAL
        or manifest.get("official_hidden_score_status") != "UNVERIFIED"
        or set(manifest.get("required_kaggle_inputs", [])) != REQUIRED_DATASETS):
        add("manifest", "FAIL", "Canonical v2.5 / three offline inputs / UNVERIFIED claims must match")
    else:
        add("manifest", "PASS", "Canonical champion stays v2.5; no hidden score claimed")

    notebooks = {}
    for label, path, expected_version in (
        ("champion", CANONICAL, "2.5.0"),
        ("challenger", CHALLENGER, "2.6.0-experimental"),
    ):
        try:
            p = root / path
            notebook = json.loads(p.read_text(encoding="utf-8"))
            metadata = notebook["metadata"]["aion_arc"]
            code = [c for c in notebook["cells"] if c.get("cell_type") == "code"]
            good = (notebook.get("nbformat") == 4 and
                    metadata.get("version") == expected_version and
                    metadata.get("status") == "UNVERIFIED" and bool(code))
            import ast
            for cell in code:
                ast.parse("".join(cell.get("source", [])))
            if label == "challenger":
                ids = [c.get("id") for c in notebook["cells"]]
                good = good and "aion-v26-recovery-policy" in ids and ids.index("aion-v26-recovery-policy") < ids.index("10")
            add(label + "_notebook", "PASS" if good else "FAIL",
                "Version / guard order / syntax verified, but not executed on Kaggle" if good else "Invalid notebook metadata or guard order",
                sha256=_sha256(p))
            notebooks[label] = p
        except (OSError, ValueError, KeyError, SyntaxError, TypeError) as exc:
            add(label + "_notebook", "FAIL", f"{type(exc).__name__}: invalid notebook")

    # Preserve a meaningful diff; a renamed notebook must not be counted as a new solver.
    if len(notebooks) == 2:
        a, b = [json.loads(notebooks[k].read_text(encoding="utf-8")) for k in ("champion", "challenger")]
        ac = {c.get("id"): "".join(c.get("source", [])) for c in a["cells"] if c.get("cell_type") == "code"}
        bc = {c.get("id"): "".join(c.get("source", [])) for c in b["cells"] if c.get("cell_type") == "code"}
        changes = sorted(k for k in set(ac) | set(bc) if ac.get(k) != bc.get(k))
        good = "aion-v26-recovery-policy" in changes
        add("meaningful_challenger_delta", "PASS" if good else "FAIL",
            "Changed code cell IDs: " + ", ".join(changes[:20]))

    # Only the submitter-owned original code is licensed under MIT-0.
    # A valid root license does NOT prove that third-party bundled code is usable.
    license_path = root / "LICENSE"
    scope_path = root / "THIRD_PARTY_NOTICES.md"
    if not license_path.is_file():
        add("project_license", "FAIL",
            "Missing root MIT-0 license for submitter-authored code")
    elif not scope_path.is_file():
        add("project_license", "FAIL",
            "Missing third-party scope notice; root license may wrongly suggest ownership of upstream")
    else:
        license_text = license_path.read_text(encoding="utf-8")
        scope_text = scope_path.read_text(encoding="utf-8")
        valid = all(x in license_text for x in (
            "MIT No Attribution",
            "Copyright 2026 AION-ARC contributors",
            "Permission is hereby granted, free of charge",
            'THE SOFTWARE IS PROVIDED "AS IS"',
        )) and all(x in scope_text for x in (
            "original contributions: MIT-0",
            "only",
            "Tufa Labs",
            "Qwen3.6",
        ))
        add("project_license", "PASS" if valid else "FAIL",
            "MIT-0 and explicitly scoped original-code rights recorded; not a third-party rights grant"
            if valid else "MIT-0 text or third-party license exclusions missing/invalid")
    apache_path = root / "THIRD_PARTY_LICENSES" / "Apache-2.0.txt"
    if apache_path.is_file():
        apache_text = apache_path.read_text(encoding="utf-8")
        apache_valid = (
            apache_text.startswith("Apache License\\nVersion 2.0, January 2004")
            and "END OF TERMS AND CONDITIONS" in apache_text
            and len(apache_text) >= 10000
        )
        add("apache_license_notice", "PASS" if apache_valid else "FAIL",
            "Canonical Apache-2.0 text included for attribution (not a Tufa source-bundle grant)"
            if apache_valid else "Apache-2.0 license text invalid")
    else:
        add("apache_license_notice", "FAIL", "Apache-2.0 attribution license text missing")
    add("third_party_rights", "UNVERIFIED",
        "Bundled Tufa source, Qwen model weights, wheels and independent license/NOTICE terms not fully verified")

    notice = root / "docs" / "UPSTREAM-ATTRIBUTION-AND-LICENSE.md"
    add("upstream_attribution", "PASS" if notice.is_file() else "FAIL",
        "Separate upstream/license register exists (not proof of all permissions)" if notice.is_file()
        else "Third-party attribution register missing")

    # A local dataset report can never authenticate Kaggle leaderboard standings.
    add("official_kaggle_submission", "UNVERIFIED",
        "No authenticated Kaggle submission/leaderboard response available via GitHub")
    add("paired_real_gameplay", "UNVERIFIED",
        "No independently validated paired v2.5 vs v2.6 gameplay evidence")
    add("gpu_runtime", "UNVERIFIED",
        "No Kaggle GPU log demonstrating offline execution within 9 hours")

    status = "FAIL" if any(x["status"] == "FAIL" for x in checks) else (
        "PARTIAL" if any(x["status"] == "UNVERIFIED" for x in checks) else "PASS")
    return {
        "status": status,
        "version": 1,
        "policy": "STATIC_PASS_NEVER_COUNTS_AS_KAGGLE_SCORE_PASS",
        "checks": checks,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--strict", action="store_true",
                   help="Exit nonzero unless EVERY proof gate has independent evidence")
    p.add_argument("--output", type=Path, default=None,
                   help="Write audit JSON file; never use for competition score proof")
    args = p.parse_args()
    result = audit(args.root)
    rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    if result["status"] == "FAIL" or (args.strict and result["status"] != "PASS"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
