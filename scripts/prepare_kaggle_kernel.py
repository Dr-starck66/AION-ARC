"""Build a private Kaggle ARC-AGI-3 notebook package without credentials or network.

This only prepares a Kaggle kernel; it neither executes the hidden evaluation
nor submits to the leaderboard. User must accept rules and run Kaggle CLI.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPETITION = "arc-prize-2026-arc-agi-3"
CANDIDATE = "kaggle/AION-ARC-v2.6-recovery.ipynb"

def build(username: str, variant: str, output: Path, root: Path = ROOT) -> dict:
    if not isinstance(username, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{1,64}", username):
        raise ValueError("Pass your public Kaggle USERNAME (not a token or password)")
    if variant not in {"champion", "challenger"}:
        raise ValueError("variant must be champion or challenger")
    manifest = json.loads((root / "kaggle/SUBMISSION_MANIFEST.json").read_text())
    source_rel = manifest["champion_notebook"] if variant == "champion" else CANDIDATE
    if variant == "champion" and manifest.get("official_hidden_score_status") != "UNVERIFIED":
        raise ValueError("manifest incorrectly claims an official score")
    notebook_path = root / source_rel
    nb = json.loads(notebook_path.read_text())
    assert nb["nbformat"] == 4
    version = nb["metadata"]["aion_arc"]["version"]
    if nb["metadata"]["aion_arc"].get("status") != "UNVERIFIED":
        raise ValueError("unexpected score status in notebook")
    if variant == "champion" and version != "2.5.0":
        raise ValueError("baseline version mismatch")
    if variant == "challenger" and version != "2.6.0-experimental":
        raise ValueError("challenger version mismatch")
    inputs = manifest["required_kaggle_inputs"]
    if len(inputs) != 3 or any("/" not in x for x in inputs):
        raise ValueError("expected three exact pinned dataset sources")
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if (output / "kernel-metadata.json").exists() or (output / "submission.ipynb").exists():
        raise FileExistsError("refusing to overwrite an existing Kaggle kernel package")
    submission_path = output / "submission.ipynb"
    shutil.copyfile(notebook_path, submission_path)
    metadata = {
        "id": f"{username}/aion-arc3-{variant}-2026",
        "title": f"AION ARC-AGI-3 {variant} {version}",
        "code_file": "submission.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": False,
        "keywords": [],
        "dataset_sources": inputs,
        "kernel_sources": [],
        "competition_sources": [COMPETITION],
        "model_sources": [],
    }
    (output / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    digest = hashlib.sha256(submission_path.read_bytes()).hexdigest()
    return {
        "status": "PACKAGE_ONLY_NOT_SUBMITTED",
        "variant": variant,
        "version": version,
        "notebook_sha256": digest,
        "source": source_rel,
        "directory": str(output),
        "kaggle_kernel_id": metadata["id"],
        "required_action": "After verification of competition eligibility and dataset availability, run kaggle kernels push -p DIR; wait for completed; submit to competition via Kaggle.",
        "official_score": "UNVERIFIED",
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True, help="PUBLIC Kaggle username, never API token")
    parser.add_argument("--variant", choices=["champion", "challenger"], default="champion")
    parser.add_argument("--out", type=Path, default=ROOT / "dist/kaggle/champion")
    args = parser.parse_args()
    print(json.dumps(build(args.username, args.variant, args.out), indent=2))

if __name__ == "__main__":
    main()
