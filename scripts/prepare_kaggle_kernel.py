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
    if (not isinstance(username, str)
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{1,64}", username)
        or username.upper().startswith("KGAT_")):
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
    # Ship license texts WITH the offline notebook, keeping ownership boundaries explicit.
    # This does not resolve rights over the separately mounted Tufa source dataset.
    mit_zero = (root / "LICENSE").read_text(encoding="utf-8")
    apache_two = (root / "THIRD_PARTY_LICENSES" / "Apache-2.0.txt").read_text(encoding="utf-8")
    scope = (root / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    if ("MIT No Attribution" not in mit_zero or
        "END OF TERMS AND CONDITIONS" not in apache_two or
        "Tufa Labs" not in scope):
        raise ValueError("missing accurate MIT-0/Apache-2.0 or third-party scope notices")
    notice = (
        "# AION-ARC LICENSES — embedded offline, not a blanket license grant\n\n"
        "AION originally authored additions: **MIT-0**, authorized by the rights holder.\n\n"
        "Tufa Labs base notebook: **Apache-2.0** as displayed on the public Kaggle notebook; "
        "the separately attached Tufa source bundle has **UNVERIFIED** license scope.\n\n"
        "Model card \u2018vrfai/Qwen3.6-27B-FP8\u2019: Apache-2.0 declared; Kaggle archive rights "
        "and wheelhouse dependency licenses require verification.\n\n"
        "Original Tufa notebook: https://www.kaggle.com/code/jeroencottaar/"
        "tufa-labs-duck-harness-june-30-milestone-winner\n\n"
        "AION scope: https://github.com/Dr-starck66/AION-ARC/blob/main/THIRD_PARTY_NOTICES.md\n\n"
        "## MIT No Attribution (original AION additions only)\n\n"
        + mit_zero + "\n\n"
        "## Apache License 2.0 (upstream public notebook; not automatically attached source)\n\n"
        + apache_two
    )
    if any(c.get("id") == "aion-license-notice" for c in nb.get("cells", [])):
        raise ValueError("AION legal notice already embedded; refuse duplicate")
    nb["cells"].insert(1, {
        "cell_type": "markdown", "id": "aion-license-notice", "metadata": {},
        "source": notice.splitlines(keepends=True),
    })
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if (output / "kernel-metadata.json").exists() or (output / "submission.ipynb").exists():
        raise FileExistsError("refusing to overwrite an existing Kaggle kernel package")
    submission_path = output / "submission.ipynb"
    submission_path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
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
        "legal_notices_embedded": True,
        "upstream_bundle_license": "UNVERIFIED",
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
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    output = args.out if args.out else ROOT / "dist" / "kaggle" / args.variant
    print(json.dumps(build(args.username, args.variant, output), indent=2))

if __name__ == "__main__":
    main()
