#!/usr/bin/env python3
"""Read-only Kaggle private inventory + NFL/BIO receipts via existing local OAuth.

No pushes, submissions, deletes, GPU execution, external uploads or secrets.
All fetched records remain under %%LOCALAPPDATA%%/ASTRA-Kaggle.
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
from uuid import uuid4

ACCOUNT = "drstarck"
HOME = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ASTRA-Kaggle"
KAGGLE = HOME / ".venv" / "Scripts" / "kaggle.exe"
MAX_PAGES = 30
PAGE_SIZE = 50
JOBS = {
    "nfl": {
        "slug": "drstarck/astra-nfl-2027-real-data-audit",
        "prefix": "drstarck/astra-nfl-2027",
        "receipt": "astra_nfl_official_report.json",
        "project": "nfl-big-data-bowl-2027",
        "source": "https://www.kaggle.com/competitions/nfl-big-data-bowl-2027",
    },
    "bio": {
        "slug": "drstarck/astra-bio-mimic-x-public-rnaseq-qc",
        "prefix": "drstarck/astra-bio-mimic-x",
        "receipt": "astra_bio_expression_report.json",
        "project": "bio-mimic-x",
        "source": "https://www.kaggle.com/datasets/lachmann12/human-liver-rnaseq-gene-expression-903-samples",
    },
}
ALLOWED = {"list", "status", "files", "output"}

def safe_text(s: str) -> str:
    s = re.sub(r"(?i)(authorization|token|secret|password|api[_-]?key)\s*[:=]\s*[^\s&]+", r"\1=[REDACTED]", s)
    return re.sub(r"(?i)https?://[^\s?]+\?[^\s]+", "[URL_QUERY_REDACTED]", s)[-700:]

def call(args, timeout=100):
    assert len(args) >= 2 and args[0] == "kernels" and args[1] in ALLOWED
    p = subprocess.run([str(KAGGLE), *args], text=True, encoding="utf-8",
                       errors="replace", stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=timeout, check=False)
    return p.returncode, p.stdout, safe_text(p.stderr)

def extract_refs(text: str) -> list[str]:
    out = []
    for row in csv.reader(io.StringIO(text)):
        if row:
            ref = row[0].strip().lower()
            if re.fullmatch(r"[a-z0-9_-]+/[a-z0-9_-]+", ref):
                out.append(ref)
    return out

def inventory() -> list[str]:
    found: set[str] = set()
    for page in range(1, MAX_PAGES + 1):
        code, stdout, stderr = call(["kernels", "list", "--mine", "-v", "--page", str(page),
                                     "--page-size", str(PAGE_SIZE), "--sort-by", "dateRun"])
        if code:
            raise RuntimeError(f"Kaggle --mine page {page} FAIL: {stderr or safe_text(stdout)}")
        refs = extract_refs(stdout)
        if any(not ref.startswith(ACCOUNT + "/") for ref in refs):
            raise RuntimeError("Kaggle OAuth belongs to a different account, stop")
        if len(refs) > PAGE_SIZE:
            raise RuntimeError("Unexpected oversized Kaggle listing page")
        found.update(refs)
        if len(refs) < PAGE_SIZE:
            return sorted(found)
    raise RuntimeError("Kaggle listing exceeded safety cap; inventory incomplete")

def select(refs: list[str], job: dict) -> tuple[str | None, str]:
    expected = job["slug"]
    candidates = sorted(ref for ref in refs if ref.startswith(job["prefix"]))
    if expected in candidates:
        return expected, "EXACT"
    if len(candidates) == 1:
        return candidates[0], "UNIQUE_RENAMED"
    if not candidates:
        return None, "NOT_FOUND_IN_OWNED_LIST"
    return None, "AMBIGUOUS:" + ",".join(candidates[:10])

def load_receipt(path: Path, job: dict):
    if not path.is_file() or path.stat().st_size > 2_000_000:
        raise ValueError("Receipt absent or oversized")
    raw = path.read_bytes()
    record = json.loads(raw)
    if not isinstance(record, dict):
        raise ValueError("Receipt not an object")
    if record.get("project") != job["project"] or record.get("source") != job["source"]:
        raise ValueError("Receipt project/source mismatch")
    script_hash = record.get("script_sha256")
    if not isinstance(script_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", script_hash):
        raise ValueError("Receipt script SHA-256 missing")
    return {
        "status": "PARTIAL" if record.get("status") == "PARTIAL" else "UNVERIFIED",
        "receipt_reported_status": record.get("status"),
        "gate": record.get("gate"),
        "receipt_sha256": hashlib.sha256(raw).hexdigest(),
        "script_sha256": script_hash,
        "input_sha256": record.get("input_sha256"),
        "gene_rows": record.get("gene_rows"),
        "sample_columns": record.get("sample_columns"),
        "file_count": record.get("file_count"),
        "local_receipt": str(path),
        "provenance": "PROJECT_SOURCE_AND_SCRIPT_HASH_FIELDS_CONFIRMED",
        "science": "UNVERIFIED",
    }

def analyze_job(key: str, config: dict, refs: list[str], folder: Path) -> dict:
    slug, kind = select(refs, config)
    if slug is None:
        return {"status": "FAIL", "stage": "owned_kernel_discovery", "reason": kind}
    result = {"status": "UNVERIFIED", "slug": slug, "resolution": kind}
    code, stdout, stderr = call(["kernels", "status", slug])
    if code:
        return {**result, "status": "FAIL", "stage": "kernel_status", "error": stderr or safe_text(stdout)}
    result["kernel_status"] = safe_text(stdout)
    if not re.search(r"\b(COMPLETE|SUCCEEDED)\b", stdout, flags=re.I):
        return {**result, "stage": "not_completed_or_status_unknown"}
    dest = folder / key
    dest.mkdir(parents=True, exist_ok=True)
    code, stdout, stderr = call(["kernels", "output", slug, "-p", str(dest),
                                "--file-pattern", ".*" + re.escape(config["receipt"]) + "$"], timeout=150)
    if code:
        return {**result, "status": "FAIL", "stage": "output", "error": stderr or safe_text(stdout)}
    found = list(dest.rglob(config["receipt"]))
    if len(found) != 1:
        return {**result, "status": "FAIL", "stage": "missing_unique_receipt", "found": len(found)}
    try:
        return {**result, **load_receipt(found[0], config), "stage": "receipt_read_only"}
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        return {**result, "status": "FAIL", "stage": "receipt_invalid", "reason": safe_text(str(exc))}

def main() -> int:
    if not KAGGLE.is_file():
        print("ASTRA_KAGGLE_READ_ONLY_FAIL: Kaggle CLI not found", flush=True)
        return 2
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    dest = HOME / "research" / "authenticated-inventory" / stamp
    dest.mkdir(parents=True, exist_ok=False)
    report = {"kind": "astra_kaggle_private_receipts_v1", "timestamp_utc": stamp,
              "requested_account": ACCOUNT, "auth": "UNVERIFIED", "jobs": {},
              "read_only": True, "new_kernels": 0, "competition_submissions": 0,
              "gpu_jobs": 0, "science": "UNVERIFIED"}
    try:
        refs = inventory()
        report["auth"] = "PARTIAL" if not refs else "PASS_OWNED_INVENTORY"
        report["owned_kernel_count"] = len(refs)
        report["owned_kernel_refs"] = refs  # local only; never print the full list
        for key, cfg in JOBS.items():
            try:
                report["jobs"][key] = analyze_job(key, cfg, refs, dest)
            except (OSError, subprocess.TimeoutExpired) as exc:
                report["jobs"][key] = {"status": "FAIL", "stage": "transport",
                                        "error": type(exc).__name__}
            r = report["jobs"][key]
            print("ASTRA_KAGGLE_" + key.upper() + "_" + r["status"] + " "
                  + str(r.get("slug", r.get("reason", r.get("stage")))) + " gate="
                  + str(r.get("gate", "UNKNOWN")), flush=True)
        return 0 if all(x["status"] == "PARTIAL" for x in report["jobs"].values()) else 1
    except Exception as exc:
        report["failure"] = safe_text(str(exc))
        print("ASTRA_KAGGLE_INVENTORY_FAIL " + report["failure"], flush=True)
        return 2
    finally:
        path = dest / "private_report.json"
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("ASTRA_KAGGLE_PRIVATE_REPORT " + str(path), flush=True)
        print("READ_ONLY=TRUE NO_PUSH NO_SUBMISSION NO_GPU NO_EXTERNAL_UPLOAD", flush=True)

if __name__ == "__main__":
    sys.exit(main())
