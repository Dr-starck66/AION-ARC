#!/usr/bin/env python3
"""ASTRA BIO-MIMIC X — public ARCHS4 human-liver expression structural QC.

Real dataset on Kaggle: lachmann12/human-liver-rnaseq-gene-expression-903-samples
License according to dataset card: CC0. No clinical/methylation/aging inference.
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

PROJECT = "bio-mimic-x"
SLUG = "lachmann12/human-liver-rnaseq-gene-expression-903-samples"
SOURCE = "https://www.kaggle.com/datasets/" + SLUG
ROOT = Path(os.environ.get("ASTRA_INPUT", "/kaggle/input/human-liver-rnaseq-gene-expression-903-samples"))
OUTPUT = Path(os.environ.get("ASTRA_OUTPUT", "/kaggle/working/astra_bio_expression_report.json"))

def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as src:
        for block in iter(lambda: src.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def audit(root):
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Kaggle public expression dataset is not mounted")
    paths = [p for p in root.rglob("*.tsv") if p.is_file() and not p.is_symlink()]
    if len(paths) != 1:
        raise ValueError("Expected exactly one readable public ARCHS4 TSV file")
    path = paths[0]
    if path.stat().st_size == 0:
        raise ValueError("Empty gene expression matrix")
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader, None)
        if not header or len(header) < 3:
            raise ValueError("Expected genes as rows and sample IDs as columns")
        n_samples = len(header) - 1
        if len(set(header[1:])) != n_samples or not all(header[1:]):
            raise ValueError("Duplicate or missing sample identifiers")
        seen_genes = set()
        min_detected = [10**9] * n_samples
        detected = [0] * n_samples
        totals = [0.0] * n_samples
        n_genes = 0
        for row in reader:
            if len(row) != len(header):
                raise ValueError("Inconsistent number of sample columns")
            gene = row[0].strip()
            if not gene or gene in seen_genes:
                raise ValueError("Duplicate or empty gene identifier")
            seen_genes.add(gene)
            n_genes += 1
            for i, val in enumerate(row[1:]):
                try:
                    x = float(val)
                except ValueError:
                    raise ValueError("Non-numeric expression in TSV") from None
                if not math.isfinite(x) or x < 0:
                    raise ValueError("Negative or nonfinite expression value")
                totals[i] += x
                if x > 0:
                    detected[i] += 1
        if n_genes < 2 or n_samples < 2:
            raise ValueError("Insufficient genes/samples")
        if any(not math.isfinite(t) for t in totals):
            raise ValueError("Nonfinite sample library size")
    return {
        "status": "PARTIAL",
        "gate": "PUBLIC_ARCHS4_EXPRESSION_MATRIX_QC_PASS",
        "source": SOURCE,
        "license": "CC0_DECLARED_ON_KAGGLE_CARD",
        "input_sha256": sha256_file(path),
        "file_bytes": path.stat().st_size,
        "gene_rows": n_genes,
        "sample_columns": n_samples,
        "zero_library_samples": sum(t == 0 for t in totals),
        "min_detected_genes_per_sample": min(detected),
        "max_detected_genes_per_sample": max(detected),
        "sample_id_export": "NO",
        "paired_methylation": "UNVERIFIED",
        "age_metadata": "UNVERIFIED",
        "cell_type_composition": "UNVERIFIED",
        "batch_effects": "UNVERIFIED",
        "biological_replication": "UNVERIFIED",
        "aging_or_clinical_efficacy": "UNVERIFIED",
        "study_validity": "UNVERIFIED",
    }

def run():
    try:
        r = audit(ROOT)
        print("ASTRA_BIO_REAL_EXPRESSION_QC_PARTIAL",
              json.dumps({"samples":r["sample_columns"],"genes":r["gene_rows"],
                          "sha256":r["input_sha256"]}), flush=True)
    except Exception as exc:
        r = {"status": "FAIL", "gate": "PUBLIC_ARCHS4_EXPRESSION_QC_FAILED",
             "source": SOURCE, "error_type": type(exc).__name__, "error": str(exc)}
        print("ASTRA_BIO_DATA_GATE_FAIL", type(exc).__name__, str(exc), flush=True)
    r["project"] = PROJECT
    r["dataset_slug"] = SLUG
    r["script_sha256"] = sha256_file(Path(__file__))
    r["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return r

if __name__ == "__main__":
    result = run()
    if result["status"] == "FAIL":
        raise SystemExit(2)
