#!/usr/bin/env python3
"""ASTRA Kaggle: read-only postmortem of 2026-11-13 NFL/BIO attempts.

Uses existing local Kaggle OAuth. Does not push, submit, delete or expose secrets.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HOME = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ASTRA-Kaggle"
KAGGLE = HOME / ".venv" / "Scripts" / "kaggle.exe"
DEST = HOME / "astra_kaggle_failure_diagnostics.json"
KERNELS = (
    ("nfl", "drstarck/astra-nfl-2027-real-data-audit", "astra_nfl_official_report.json"),
    ("bio", "drstarck/astra-bio-mimic-x-public-rnaseq-qc", "astra_bio_expression_report.json"),
)
MAX_OUTPUT = 10000
MAX_LOG = 4000

def cleaned(value):
    text = str(value)
    text = re.sub(r"(?i)(code|token|password|authorization|secret)\s*[:=]\s*[^\s,&]+",
                  r"\1=[REDACTED]", text)
    text = re.sub(r"(?:https?://)\S+[?][^\s]*", "[URL_WITH_QUERY_REDACTED]", text)
    return text

def invoke(*args, timeout=80):
    try:
        proc = subprocess.run([str(KAGGLE), *args], capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=timeout)
        result = cleaned((proc.stdout or "") + "\n" + (proc.stderr or ""))
        return {"exit_code": proc.returncode, "text": result[-MAX_OUTPUT:]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"exit_code": 125, "text": cleaned(str(exc))[:500]}

def emit_lines(content, cap=MAX_LOG):
    selected = []
    clues = ("error", "traceback", "exception", "fail", "permission",
             "dataset", "input", "missing", "kernel", "not found",
             "unavailable", "invalid", "limit", "denied", "expired")
    for line in content.splitlines():
        if any(k in line.lower() for k in clues):
            selected.append(line[:400])
    return "\n".join(selected[-20:])[-cap:]

def inspect_kernel(key, slug, filename):
    print("ASTRA_DIAG_START " + key, flush=True)
    state = invoke("kernels", "status", slug)
    logs = invoke("kernels", "logs", slug, timeout=110)
    files = invoke("kernels", "files", slug)
    location = HOME / "research" / key / "diagnostics"
    location.mkdir(parents=True, exist_ok=True)
    output = invoke("kernels", "output", slug, "-p", str(location),
                    "-o", "--file-pattern", ".*" + re.escape(filename) + "$",
                    timeout=130)
    matches = list(location.rglob(filename))
    data = None
    if len(matches) == 1:
        try:
            data = json.loads(matches[0].read_text(encoding="utf-8"))
        except (UnicodeError, ValueError, OSError):
            pass
    result = {
        "kernel": slug,
        "status_command": state,
        "logs_exit_code": logs["exit_code"],
        "logs_error_clues": emit_lines(logs["text"]),
        "files_exit_code": files["exit_code"],
        "files_excerpt": emit_lines(files["text"], 1500),
        "output_exit_code": output["exit_code"],
        "output_message": emit_lines(output["text"], 1500),
        "receipt_sha256": hashlib.sha256(matches[0].read_bytes()).hexdigest() if data is not None else None,
        "receipt": data,
        "receipt_path": str(matches[0]) if data is not None else None,
    }
    actual = "UNKNOWN"
    if data is not None:
        actual = str(data.get("status", "UNKNOWN"))
    elif state["exit_code"] != 0:
        actual = "STATUS_API_FAILURE"
    elif re.search(r"KernelWorkerStatus[.]ERROR", state["text"]):
        actual = "REMOTE_ERROR_NO_RECEIPT"
    print("ASTRA_DIAG_" + key.upper() + "=" + actual, flush=True)
    if data is not None:
        print("DATA_GATE=" + str(data.get("gate", "UNKNOWN")), flush=True)
        if data.get("error"):
            print("DATA_ERROR=" + cleaned(str(data["error"]))[:1200], flush=True)
    elif result["logs_error_clues"]:
        print("REMOTE_LOG_CLUES=" + result["logs_error_clues"][-2000:], flush=True)
    else:
        print("STATUS_DETAILS=" + state["text"][-1500:], flush=True)
    return result

def main():
    HOME.mkdir(parents=True, exist_ok=True)
    if not KAGGLE.is_file():
        print("ASTRA_DIAG_FAIL: Kaggle CLI not installed in ASTRA folder", flush=True)
        return 2
    probe = invoke("kernels", "status", "drstarck/notebook2700e63354")
    if probe["exit_code"]:
        print("ASTRA_DIAG_FAIL: Kaggle OAuth not accessible: " + probe["text"][-800:], flush=True)
        return 2
    listing = invoke("kernels", "list", "--mine", "-p", "1", timeout=120)
    results = {
        "kind": "astra_scientific_kaggle_read_only_diagnostic_v1",
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "auth": "PASS",
        "no_new_kernels_pushed": True,
        "no_competition_submissions": True,
        "existing_gpu_receipt": "ALREADY_REPORTED_2xT4_NOT_A_SCIENTIFIC_SCORE",
        "mine_listing_exit_code": listing["exit_code"],
        "mine_listing_excerpt": listing["text"][-5000:],
        "jobs": {},
    }
    print("ASTRA_AUTH_PASS - READ_ONLY_DIAGNOSTICS", flush=True)
    for key, slug, filename in KERNELS:
        results["jobs"][key] = inspect_kernel(key, slug, filename)
    DEST.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print("ASTRA_DIAGNOSTICS_SAVED=" + str(DEST), flush=True)
    print("NO_REPUSH_NO_QUOTA_NO_SUBMISSION", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
