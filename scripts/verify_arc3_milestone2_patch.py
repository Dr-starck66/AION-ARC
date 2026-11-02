"""Apply the exact notebook patch to upstream, with a corrupt-EOF control."""
from __future__ import annotations

import argparse
import ast
import importlib.util
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
        guard_file = root / "ARC3-Inference/inference/agent/noop_repeat_guard.py"
        spec = importlib.util.spec_from_file_location("astra_reviewed_noop_guard", guard_file)
        guard_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard_module)
        guard = guard_module.NoopRepeatGuard()
        guard.note_level(1)
        guard.observe("same", "UP", gameplay_changed=False)
        assert guard.should_block("same", "UP")
        assert not guard.should_block("same", "UP"), "Insistence must remain possible"
        guard.observe("same", "UP", gameplay_changed=True)
        assert not guard.should_block("same", "UP"), "Contradictory evidence must clear a verdict"
        guard.observe("same", "UP", gameplay_changed=False)
        guard.note_level(2)
        assert not guard.should_block("same", "UP"), "No verdict may leak across levels"
        assert guard_module.action_signature({"action": "MOUSE", "row": 4, "col": 7}) == guard_module.action_signature("MOUSE(row=4, col=7)")
        guard.observe("same", "MOUSE(4,7)", gameplay_changed=False)
        assert not guard.should_block("same", "MOUSE(4,8)"), "Different click must remain possible"
        assert guard.should_block("same", "MOUSE(4,7)")
        assert not guard.should_block_death("same", "MOUSE(4,7)", lambda *_: False)
        assert not guard.should_block("same", "MOUSE(4,7)"), "Death checks must not consume the no-op override"
        return {"status": "PASS", "python_files_compiled": len(files), "embedded_bootstrap": "PASS",
                "negative_control_corrupt_eof": "PASS", "recovery_guard_contracts": 6,
                "scope": "CPU integration only; Kaggle gameplay UNVERIFIED"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("upstream", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.upstream)))
