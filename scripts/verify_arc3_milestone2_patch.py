"""Apply the exact notebook patch to upstream, with a corrupt-EOF control."""
from __future__ import annotations

import argparse
import ast
import json
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

from build_arc3_milestone2_challenger import SOURCE, build


def verify(upstream: Path) -> dict:
    build()  # Checks the reviewed source hash and all notebook code bodies.
    source = json.loads(SOURCE.read_text())
    raw_patch = "".join(source["cells"][2]["source"]).split("\n", 1)[1].rstrip("\n")
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        shutil.copytree(upstream / "ARC3-Inference", root / "ARC3-Inference")
        patch = root / "changes.patch"
        patch.write_text(raw_patch)
        command = ["git", "apply", "--include=ARC3-Inference/*", str(patch)]
        negative = subprocess.run(command + ["--check"], cwd=root, capture_output=True, text=True)
        if negative.returncode == 0 or "corrupt patch" not in negative.stderr:
            raise RuntimeError("Negative EOF control did not fail as expected")
        patch.write_text(raw_patch + "\n")
        subprocess.run(command, cwd=root, check=True, capture_output=True, text=True)
        files = list((root / "ARC3-Inference").rglob("*.py"))
        for file in files:
            compile(file.read_text(), str(file), "exec")
        sandbox = root / "ARC3-Inference/inference/agent/python_tool_sandbox.py"
        tree = ast.parse(sandbox.read_text())
        assignment = next(n for n in tree.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "_SANDBOX_BOOTSTRAP" for t in n.targets))
        bootstrap = next(n.value for n in ast.walk(assignment.value)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and "def main():" in n.value)
        compile(textwrap.dedent(bootstrap), "milestone2-embedded-bootstrap", "exec")
        return {"status": "PASS", "python_files_compiled": len(files), "embedded_bootstrap": "PASS",
                "negative_control_corrupt_eof": "PASS", "scope": "CPU integration only; Kaggle gameplay UNVERIFIED"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("upstream", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.upstream)))
