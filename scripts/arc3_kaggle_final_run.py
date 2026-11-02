#!/usr/bin/env python3
"""ASTRA ARC-AGI-3: one authenticated Kaggle push + submission, no paid services.

Run inside the existing AION-ARC checkout with a Kaggle CLI session already
authorized by the account owner. No credentials are written to this repository.
Without --execute this does local validation only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "kaggle/v29-milestone2"
KERNEL = "drstarck/astra-aion-arc3-v2-9-milestone2"
AUTH_PROBE_KERNEL = "drstarck/notebook2700e63354"  # Historic private v6; never overwrite
COMP = "arc-prize-2026-arc-agi-3"
DEADLINE = dt.datetime(2026, 11, 2, 23, 59, tzinfo=dt.timezone.utc)
RECEIPT = ROOT / "reports/arc3-final-20261101/receipt.json"


def command(args: list[str], *, timeout: int = 90, check: bool = True):
    run = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    # Do not log full Kaggle auth errors; may include sensitive local context.
    if run.returncode != 0 and check:
        raise RuntimeError(f"{args[0]} {args[1] if len(args)>1 else ''} exited {run.returncode}; "
                           "inspect connected Kaggle CLI logs privately")
    return run


def evidence(**kwargs):
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    previous = {}
    if RECEIPT.exists():
        previous = json.loads(RECEIPT.read_text())
    previous.update(kwargs)
    previous["at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    RECEIPT.write_text(json.dumps(previous, indent=2, ensure_ascii=False)+"\n")
    print("ASTRA_RECEIPT", json.dumps({k: v for k, v in kwargs.items()
                                      if "secret" not in k.lower()}), flush=True)


def validate():
    nb = FOLDER / "submission.ipynb"
    meta = json.loads((FOLDER / "kernel-metadata.json").read_text())
    before = nb.read_bytes()
    builder = command([sys.executable, "scripts/build_arc3_milestone2_challenger.py"], timeout=30)
    after = nb.read_bytes()
    assert before == after, "Notebook in GitHub differs from reproducible builder"
    j = json.loads(after)
    assert len(j["cells"]) == 27 and j["metadata"]["astra"]["graph_nav"] == "visual-lattice-bfs"
    assert any(c.get("id") == "astra-v29-graph-nav-install" for c in j["cells"])
    assert len(j["metadata"]["kaggle"]["dataSources"]) == 5
    assert meta["id"] == KERNEL and meta["code_file"] == nb.name
    assert meta["enable_internet"] is False and meta["enable_gpu"] is True
    assert meta["machine_shape"] == "NvidiaRtxPro6000"
    assert meta["competition_sources"] == [COMP]
    assert len(meta["dataset_sources"]) == 2 and len(meta["model_sources"]) == 2
    digest = hashlib.sha256(after).hexdigest()
    evidence(package="PASS", notebook_sha256=digest, cells=len(j["cells"]),
             official_score="UNVERIFIED")
    print("ASTRA_NOTEBOOK_VALIDATED", digest, builder.stdout.strip())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true",
                        help="Upload the notebook, execute it and submit the finished Kaggle version")
    parser.add_argument("--wait-minutes", type=int, default=530)
    parser.add_argument("--check-auth", action="store_true",
                        help="Read-only Kaggle authorization probe; no notebook push")
    args = parser.parse_args()
    if args.check_auth:
        if not shutil.which("kaggle"):
            evidence(kaggle_cli="FAIL", private_kernel_auth="UNVERIFIED")
            raise RuntimeError("Kaggle CLI missing; authorization cannot be checked")
        check = command(["kaggle", "kernels", "status", AUTH_PROBE_KERNEL], timeout=45, check=False)
        if check.returncode:
            evidence(private_kernel_auth="FAIL", auth_probe=AUTH_PROBE_KERNEL)
            raise RuntimeError("Authenticated access to the historic Kaggle kernel failed")
        evidence(private_kernel_auth="PASS", auth_probe=AUTH_PROBE_KERNEL)
        # The official history is authoritative: it prevents relying on
        # obsolete 0.07-score reports or repeating a daily submission.
        history = command(["kaggle", "competitions", "submissions", COMP, "-v", "-q"],
                          timeout=60, check=False)
        if history.returncode == 0:
            import csv
            import io
            submissions = list(csv.DictReader(io.StringIO(history.stdout)))
            recent = submissions[:12]
            evidence(submissions_read="PASS", submissions_returned=len(submissions),
                     recent_submissions=recent)
            print("ASTRA_KAGGLE_HISTORY", json.dumps(recent, ensure_ascii=False), flush=True)
        else:
            evidence(submissions_read="PARTIAL", official_score="UNVERIFIED",
                     reason="SUBMISSIONS_CLI_READ_FAILED")
        print("ASTRA_KAGGLE_READONLY_AUTH_PASS", flush=True)
        return
    validate()
    if not args.execute:
        print("ASTRA_DRY_RUN_ONLY: no Kaggle upload or submission requested")
        return
    if dt.datetime.now(dt.timezone.utc) >= DEADLINE:
        raise RuntimeError("Submission deadline has passed; no request sent")
    if not shutil.which("kaggle"):
        raise RuntimeError("Kaggle CLI not available in the authenticated execution environment")
    # Status is also a proof that the CLI can access this private notebook.
    probe = command(["kaggle", "kernels", "status", AUTH_PROBE_KERNEL], timeout=40, check=False)
    if probe.returncode:
        raise RuntimeError("Kaggle CLI has no authorized access to drstarck\u0027s historic private notebook; do not push")
    evidence(private_kernel_auth="PASS", verified_baseline=AUTH_PROBE_KERNEL, previous_kernel_status=probe.stdout.strip()[-300:])
    # Exactly one new version. Do not auto-repeat GPU work or consume daily slots.
    pushed = command(["kaggle", "kernels", "push", "-p", str(FOLDER),
                      "--accelerator", "NvidiaRtxPro6000"], timeout=150)
    evidence(kaggle_push="REQUEST_SENT", push_result=pushed.stdout.strip()[-1200:])
    deadline = time.monotonic() + args.wait_minutes * 60
    status = ""
    while time.monotonic() < deadline:
        if dt.datetime.now(dt.timezone.utc) >= DEADLINE:
            raise RuntimeError("Competition deadline reached while waiting")
        reply = command(["kaggle", "kernels", "status", KERNEL], timeout=45, check=False)
        status = (reply.stdout + "\n" + reply.stderr).strip()
        low = status.lower()
        if reply.returncode == 0 and re.search(r"\b(complete|succeeded)\b", low):
            break
        if re.search(r"\b(error|failed|cancelled)\b", low):
            evidence(kernel_status="FAILED", kernel_status_text=status[-350:])
            raise RuntimeError("New notebook did not complete; inspect Kaggle notebook logs")
        time.sleep(90)
    else:
        evidence(kernel_status="TIMEOUT", kernel_status_text=status[-300:])
        raise RuntimeError("Kaggle run was not confirmed complete within chosen wait time")
    # Phase A is the public Save & Run All validator. It emits a placeholder
    # submission.parquet; ONLY Phase B, launched via 'submit -k', scores hidden
    # games. Do not use a plain upload or mistake Phase A for an official score.
    game_gate = "UNVERIFIED"
    evidence(phase_a="COMPLETE", phase_b="NOT_STARTED", 
             gameplay="UNVERIFIED", official_score="UNVERIFIED")
    
    # Kaggle's output listing is eventually consistent after a successful kernel.
    artifact_found = False
    for attempt in range(3):
        files = command(["kaggle", "kernels", "files", KERNEL], timeout=60, check=False)
        artifact_found = files.returncode == 0 and "submission.parquet" in files.stdout
        if artifact_found:
            break
        if attempt < 2:
            time.sleep(20)
    if not artifact_found:
        evidence(kernel_status="PARTIAL", error="submission.parquet not listed after complete kernel")
        raise RuntimeError("Refusing submission: Kaggle output file missing")
    evidence(kernel_status="COMPLETE", game_gate=game_gate,
             output="submission.parquet", output_scope="PHASE_A_VALIDATION_ONLY")
    # Submit the notebook kernel reference (-k) to TRIGGER Kaggle's hidden
    # competition rerun. Never submit the placeholder parquet file directly.
    submitted = command(["kaggle", "competitions", "submit", COMP,
                         "-k", KERNEL, "-f", "submission.parquet",
                         "-m", "ASTRA AION-ARC v2.9 hidden competition rerun"],
                        timeout=120)
    match = re.search(r"Submission ref:\s*(\d+)", submitted.stdout)
    evidence(official_submission_request="SENT", phase_b="REQUEST_SENT",
             submission_ref=int(match.group(1)) if match else None,
             official_score="UNVERIFIED")
    if match:
        for _ in range(6):
            result = command(["kaggle", "competitions", "submission",
                              match.group(1)], timeout=45, check=False)
            if result.returncode == 0:
                m = re.search(r"Public Score:\s*(\S+)", result.stdout)
                if m and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", m.group(1)):
                    evidence(official_score=float(m.group(1)), official_submission="PASS")
                    break
            time.sleep(30)


if __name__ == "__main__":
    main()
