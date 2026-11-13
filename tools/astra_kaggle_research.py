#!/usr/bin/env python3
"""ASTRA Omega Kaggle research batch v1. Read-only public/official datasets.

Execute with existing Windows Kaggle OAuth: .venv/Scripts/python.exe this-file.py
No GitHub Actions, passwords, secrets, cron, paid services or competition submits.
Each remote task produces a real Kaggle output receipt, else explicit failure.
"""
from __future__ import annotations
import csv
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

ACCOUNT = "drstarck"
SOURCE_REV = "3bedfdb957e225684f13eadeb41e9547f250ccac"
BASE_URL = ("https://raw.githubusercontent.com/Dr-starck66/AION-ARC/" +
            SOURCE_REV + "/tools/kaggle_labs/")
HOME = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ASTRA-Kaggle"
KAGGLE = HOME / ".venv" / "Scripts" / "kaggle.exe"
MAX_POLLS = 48
POLL_SEC = 15
JOBS = (
    dict(name="nfl", project="nfl-big-data-bowl-2027",
         source="https://www.kaggle.com/competitions/nfl-big-data-bowl-2027",
         slug="drstarck/astra-nfl-2027-real-data-audit",
         filename="nfl_real_data_audit.py",
         receipt="astra_nfl_official_report.json",
         preflight=("competitions", "files", "nfl-big-data-bowl-2027"),
         competition_sources=["nfl-big-data-bowl-2027"],
         dataset_sources=[]),
    dict(name="bio", project="bio-mimic-x",
         source="https://www.kaggle.com/datasets/lachmann12/human-liver-rnaseq-gene-expression-903-samples",
         slug="drstarck/astra-bio-mimic-x-public-rnaseq-qc",
         filename="bio_public_expression_audit.py",
         receipt="astra_bio_expression_report.json",
         preflight=("datasets", "files", "lachmann12/human-liver-rnaseq-gene-expression-903-samples"),
         competition_sources=[],
         dataset_sources=["lachmann12/human-liver-rnaseq-gene-expression-903-samples"]),
)
OTHER_PROJECTS = {
    "aion-arc": "Competition 2026 submissions closed; existing ARC notebooks retained; no new official score.",
    "splatforge": "Prior GPU proof reused, real licensed COLMAP/image inputs not mounted, native 3D training UNVERIFIED.",
    "astra-dc-energy": "No measured timestamped electrical/latency joint trace attached; savings UNVERIFIED.",
    "astra-quantum-gate": "Structural checks exist; no verified physics or official competition result.",
    "nexus": "Need a vetted, licensed challenge corpus; no synthetic security success claimed.",
    "quantflow": "Need licensed market data and a leakage-controlled rolling backtest before claiming model performance.",
}

def invoke(args, timeout=90):
    try:
        p = subprocess.run([str(KAGGLE), *args], text=True, capture_output=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, (p.stdout + "\n" + p.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return 125, type(e).__name__ + ": " + str(e)

def remote_file(name):
    url = BASE_URL + name
    with urlopen(url, timeout=45) as r:
        blob = r.read(3_000_000)
    if len(blob) > 500_000 or not blob.startswith(b"#!/usr/bin/env python3"):
        raise ValueError("Unexpected code artifact")
    return blob


def _owned_refs(search_term=None):
    """Read Kaggle CSV pages completely; fail closed on truncated discovery."""
    found = set()
    page_size = 100
    max_pages = 20
    for page in range(1, max_pages + 1):
        args = ("kernels", "list", "--mine", "-v", "--page", str(page),
                "--page-size", str(page_size), "--sort-by", "dateRun")
        if search_term:
            args += ("--search", search_term)
        code, output = invoke(args, timeout=100)
        if code:
            raise RuntimeError("Owned notebook listing failed (page " + str(page)
                               + "): " + output[-400:])
        count = 0
        for row in csv.reader(io.StringIO(output)):
            if not row:
                continue
            ref = row[0].strip().lower()
            if re.fullmatch(r"drstarck/[a-z0-9][a-z0-9_-]*", ref):
                found.add(ref)
                count += 1
        if count < page_size:
            return found
    raise RuntimeError("Owned Kaggle notebook listing exceeded 20 full pages; "
                       "cannot prove uniqueness or absence")


def find_owned_kernel(job):
    """Find a readable owned notebook, without creating another on uncertainty."""
    wanted = job["slug"].lower()
    code, direct = invoke(("kernels", "status", wanted), timeout=90)
    if code == 0:
        return wanted
    stem = "astra-nfl-2027" if job["name"] == "nfl" else "astra-bio-mimic-x"
    candidates = {ref for ref in _owned_refs(stem)
                  if ref == wanted or ref.startswith("drstarck/" + stem)}
    if not candidates:
        candidates = {ref for ref in _owned_refs()
                      if ref == wanted or ref.startswith("drstarck/" + stem)}
    if len(candidates) != 1:
        raise RuntimeError("Owned notebook discovery returned " + str(len(candidates))
                           + " candidates for " + job["name"] + ": "
                           + repr(sorted(candidates))[:300]
                           + "; exact status originally failed: " + direct[-250:]
                           + "; no duplicate push")
    actual = next(iter(candidates))
    code, output = invoke(("kernels", "status", actual), timeout=90)
    if code:
        raise RuntimeError("Owned notebook " + actual + " remains unreadable: "
                           + output[-400:] + "; no duplicate push")
    return actual

def slug_from_push_output(output):
    matches = re.findall(
        r"(?i)https?://(?:www[.])?kaggle[.]com/code/(drstarck/[a-z0-9_-]+)",
        output,
    )
    return matches[-1].lower() if matches else None


def kernel_status(slug):
    code, output = invoke(("kernels", "status", slug))
    if code != 0:
        if "permission" in output.lower() or "denied" in output.lower():
            return "DENIED", output
        return "MISSING", output
    found = re.search(r"KernelWorkerStatus[.]([A-Z_]+)", output)
    if found:
        state = found.group(1)
    elif re.search(r"\b(FAILED|ERROR|CANCELED|CANCELLED)\b", output, flags=re.I):
        state = "ERROR"
    elif re.search(r"\b(COMPLETE|SUCCEEDED)\b", output, flags=re.I):
        state = "COMPLETE"
    elif re.search(r"\b(RUNNING|QUEUED|PENDING)\b", output, flags=re.I):
        state = "RUNNING"
    else:
        state = "UNKNOWN"
    return state, output

def validated_receipt(job, script_hash):
    out_dir = HOME / "research" / job["name"] / (
        "output-" + hashlib.sha256(
            (job["slug"] + str(time.time_ns())).encode("utf-8")
        ).hexdigest()[:12]
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    code, msg = invoke(("kernels", "output", job["slug"], "-p", str(out_dir),
                        "-o", "--file-pattern", ".*" + re.escape(job["receipt"]) + "$"),
                       timeout=150)
    if code != 0:
        return None, "output failed: " + msg[-600:]
    matches = list(out_dir.rglob(job["receipt"]))
    if len(matches) != 1:
        return None, "missing exact receipt"
    try:
        obj = json.loads(matches[0].read_text(encoding="utf-8"))
        if (obj.get("project") != job["project"] or
            obj.get("source") != job["source"] or
            obj.get("script_sha256") != script_hash):
            return None, "receipt project/source/script checksum mismatch"
        return obj, str(matches[0])
    except (ValueError, OSError) as exc:
        return None, "invalid receipt: " + str(exc)


def remote_failure_details(job, digest, status_output):
    """Collect a verifiable negative receipt and bounded Kaggle logs immediately."""
    code, logs = invoke(("kernels", "logs", job["slug"]), timeout=120)
    receipt, receipt_path = validated_receipt(job, digest)
    details = {
        "status": "FAIL", "stage": "remote_execution_error",
        "kernel_slug": job["slug"],
        "kernel_status_message": status_output[-700:],
        "logs_exit_code": code,
        "logs_tail": logs[-1800:],
    }
    if receipt is not None:
        details["data_gate"] = receipt.get("gate")
        details["data_error"] = receipt.get("error")
        details["receipt"] = receipt_path
        details["receipt_status"] = receipt.get("status")
        print("ASTRA_REMOTE_FAIL_WITH_RECEIPT " + job["name"]
              + " " + str(receipt.get("error", ""))[-500:], flush=True)
    else:
        details["receipt_unavailable_reason"] = receipt_path
        print("ASTRA_REMOTE_FAIL_LOGS " + job["name"] + " " + logs[-500:], flush=True)
    return details


def local_selftest(job, blob, digest):
    """Two reproducible local fixtures before any remote Kaggle write."""
    compile(blob, job["filename"], "exec")
    with tempfile.TemporaryDirectory(prefix="astra-kaggle-qc-", dir=str(HOME)) as temp:
        base = Path(temp)
        source = base / job["filename"]
        source.write_bytes(blob)
        data = base / "input"
        data.mkdir()
        output = base / "receipt.json"
        if job["name"] == "nfl":
            (data / "combine.csv").write_text("player_id,s\np1,2.0\np2,3.0\n", encoding="utf-8")
            (data / "game_tracking.csv").write_text("player_id,s\np1,2.5\np3,3.5\n", encoding="utf-8")
        else:
            (data / "human_liver.tsv").write_text(
                "gene_id\tsample_1\tsample_2\nGENE1\t1\t0\nGENE2\t2\t3\n",
                encoding="utf-8")
        env = os.environ.copy()
        env["ASTRA_INPUT"] = str(data)
        env["ASTRA_OUTPUT"] = str(output)
        p = subprocess.run([sys.executable, str(source)], capture_output=True,
                           text=True, env=env, timeout=40)
        if p.returncode != 0 or not output.is_file():
            raise RuntimeError("Positive fixture did not execute: " + (p.stderr or p.stdout)[-500:])
        receipt = json.loads(output.read_text(encoding="utf-8"))
        if (receipt.get("status") != "PARTIAL" or
            receipt.get("project") != job["project"] or
            receipt.get("script_sha256") != digest):
            raise RuntimeError("Positive fixture receipt mismatch")
        bad = base / "empty"
        bad.mkdir()
        env["ASTRA_INPUT"] = str(bad)
        p = subprocess.run([sys.executable, str(source)], capture_output=True,
                           text=True, env=env, timeout=40)
        failed = json.loads(output.read_text(encoding="utf-8"))
        if p.returncode == 0 or failed.get("status") != "FAIL":
            raise RuntimeError("Negative fixture accepted a missing dataset")
    print("ASTRA_LOCAL_SELFTEST_PASS: " + job["name"] + " positive + negative", flush=True)

def prepare_job(job, blob):
    folder = HOME / "research" / job["name"] / "kernel"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "run.py").write_bytes(blob)
    meta = {
        "id": job["slug"],
        "title": job["slug"].split("/",1)[1],
        "code_file": "run.py", "language": "python", "kernel_type": "script",
        "is_private": True, "enable_gpu": False, "enable_internet": False,
        "dataset_sources": job["dataset_sources"],
        "competition_sources": job["competition_sources"],
        "kernel_sources": [], "model_sources": [],
    }
    (folder / "kernel-metadata.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8")
    return folder

def run_job(job):
    print("\n=== ASTRA " + job["name"].upper() + " : real Kaggle data ===", flush=True)
    try:
        blob = remote_file(job["filename"])
    except Exception as exc:
        return {"status": "FAIL", "stage":"source_download", "reason":str(exc)}
    digest = hashlib.sha256(blob).hexdigest()
    try:
        local_selftest(job, blob, digest)
    except Exception as exc:
        return {"status":"FAIL", "stage":"local_selftest", "reason":str(exc)}
    # Resolve actual slug BEFORE any new remote write. Kaggle may rename it.
    try:
        job = dict(job)
        job["slug"] = find_owned_kernel(job)
    except RuntimeError as exc:
        return {"status": "FAIL", "stage": "owned_kernel_discovery",
                "reason": str(exc)}
    state, msg = kernel_status(job["slug"])
    if state in ("DENIED", "MISSING", "UNKNOWN"):
        return {"status": "FAIL", "stage": "status_access",
                "reason": "Owned kernel unreadable: " + msg[-700:]}
    if state == "COMPLETE":
        receipt, location = validated_receipt(job, digest)
        if receipt and receipt.get("status") in ("PARTIAL", "PASS"):
            print("Existing verified data receipt reused: " + location, flush=True)
            return {"status": receipt["status"], "stage": "reused_receipt",
                    "receipt": location, "gate": receipt.get("gate"),
                    "sample_columns": receipt.get("sample_columns"),
                    "gene_rows": receipt.get("gene_rows"),
                    "input_sha256": receipt.get("input_sha256"),
                    "source": receipt.get("source")}
    if state not in ("RUNNING", "QUEUED", "PENDING"):
        code, out = invoke(job["preflight"], timeout=90)
        if code != 0:
            print("DATA_ACCESS_BLOCKED: " + out[-500:], flush=True)
            return {"status":"PARTIAL", "stage":"dataset_access",
                    "reason":"Kaggle refuses this source. Competition rules may require explicit acceptance.",
                    "details":out[-500:]}
        folder = prepare_job(job, blob)
        print("Submitting ONE private CPU run; no GPU quota consumed.", flush=True)
        code, out = invoke(("kernels", "push", "-p", str(folder), "--timeout", "1200"),
                           timeout=240)
        if code != 0:
            print("KAGGLE_PUSH_FAIL: " + out[-600:], flush=True)
            return {"status": "FAIL", "stage": "push", "reason": out[-900:]}
        actual = slug_from_push_output(out)
        if actual is not None and actual != job["slug"]:
            return {"status": "FAIL", "stage": "unexpected_slug",
                    "reason": "Kaggle push returned " + actual
                             + ", expected " + job["slug"]}
        print("KAGGLE_PUSH_ACCEPTED_NOT_SCIENTIFIC_PASS " + job["slug"], flush=True)
    else:
        print("Existing kernel running; no duplicate pushed.", flush=True)

    for i in range(MAX_POLLS):
        state, msg = kernel_status(job["slug"])
        if state == "COMPLETE":
            receipt, location = validated_receipt(job, digest)
            if receipt is None:
                return {"status": "FAIL", "stage":"receipt", "reason":location}
            status = receipt.get("status", "UNVERIFIED")
            print("ASTRA_KAGGLE_" + job["name"].upper() + "_DATA_" + status,
                  "gate=" + str(receipt.get("gate")), flush=True)
            return {"status": status, "stage": "real_kaggle_execution",
                    "gate":receipt.get("gate"), "receipt":location,
                    "source": job["source"],
                    "file_count":receipt.get("file_count"),
                    "sample_columns":receipt.get("sample_columns"),
                    "gene_rows":receipt.get("gene_rows"),
                    "input_sha256":receipt.get("input_sha256"),
                    "zero_library_samples":receipt.get("zero_library_samples"),
                    "min_detected_genes_per_sample":receipt.get("min_detected_genes_per_sample"),
                    "max_detected_genes_per_sample":receipt.get("max_detected_genes_per_sample")}
        if state in ("ERROR", "FAILED", "CANCELLED", "CANCELED"):
            return remote_failure_details(job, digest, msg)
        if state in ("MISSING", "DENIED"):
            return {"status": "FAIL", "stage": "kernel_inaccessible",
                    "reason": "Kaggle status failed: " + msg[-700:]}
        print("Checking " + job["name"] + " " + str(i+1) + "/" + str(MAX_POLLS) +
              " : " + state, flush=True)
        time.sleep(POLL_SEC)
    return {"status":"UNVERIFIED", "stage":"still_running_or_unknown",
            "reason":"Kaggle execution did not reach a confirmed terminal state in polling window."}

def main():
    HOME.mkdir(parents=True, exist_ok=True)
    print("ASTRA OMEGA — SCIENTIFIC KAGGLE WORK, REAL DATA, PRIVATE CPU, ZERO SPEND")
    if not KAGGLE.is_file():
        print("ASTRA_FAIL: Kaggle CLI missing: " + str(KAGGLE))
        return 2
    code, version = invoke(("--version",))
    if code != 0:
        print("ASTRA_FAIL: Kaggle CLI broken: " + version[-500:])
        return 2
    code, proof = invoke(("kernels", "status", "drstarck/notebook2700e63354"))
    if code != 0:
        print("ASTRA_FAIL: Windows Kaggle OAuth not authenticated. " + proof[-500:])
        return 2
    print("ASTRA_KAGGLE_AUTH_PASS: " + version)
    print("ASTRA_KAGGLE_RESEARCH_REVISION: 20261113-recovery-v3")
    summary = {"kind":"astra_kaggle_real_data_v1", "auth":"PASS",
               "timestamp_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
               "remote_script_commit":SOURCE_REV, "jobs":{}, "other_projects":OTHER_PROJECTS,
               "scientific_validation":"UNVERIFIED"}
    for job in JOBS:
        try:
            result = run_job(job)
        except Exception as exc:
            result = {"status":"FAIL", "stage":"exception", "reason":str(exc)}
        summary["jobs"][job["name"]] = result
        print("ASTRA_RESULT " + job["name"].upper() + " " + result["status"],
              result.get("gate", result.get("stage", "")), flush=True)
        if job["name"] == "bio" and result.get("status") == "PARTIAL":
            print("ASTRA_BIO_REAL_MATRIX_METRICS samples="
                  + str(result.get("sample_columns")) + " genes="
                  + str(result.get("gene_rows")) + " sha256="
                  + str(result.get("input_sha256")), flush=True)
        if result.get("status") == "FAIL" and result.get("reason"):
            print("ASTRA_FAILURE_REASON " + job["name"].upper() + " "
                  + str(result["reason"])[-800:], flush=True)
    report = HOME / "astra_kaggle_research_summary.json"
    report.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("\nASTRA_RESEARCH_SUMMARY " + str(report), flush=True)
    print("No competition submissions, no claimed NFL prediction, no clinical or anti-aging proof.")
    for name, result in summary["jobs"].items():
        print("RESULT:", name, result["status"], result.get("gate", result.get("stage")))
    return 0 if all(v["status"] == "PARTIAL" for v in summary["jobs"].values()) else 1

if __name__ == "__main__":
    sys.exit(main())
