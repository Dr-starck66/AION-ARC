"""Apply the exact notebook patch to upstream, with a corrupt-EOF control."""
from __future__ import annotations

import argparse
import ast
import base64
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import types
from pathlib import Path

from build_arc3_milestone2_challenger import SOURCE, build


def verify_animation_helpers(root: Path) -> int:
    """Exercise real image helpers, isolating unrelated ToolAgent imports."""
    from PIL import Image

    saved_modules = {k: v for k, v in sys.modules.items() if k == "inference" or k.startswith("inference.")}
    keys = ("MULTIMODAL_CONTEXT", "MULTIMODAL_UPSCALE", "ARC3_ANIMATION_IMAGE", "ARC3_ANIMATION_DEATH_IMAGE")
    saved_env = {k: os.environ.get(k) for k in keys}
    try:
        for name in ("inference", "inference.agent", "inference.utils"):
            namespace = types.ModuleType(name)
            namespace.__path__ = [str(root.joinpath(*name.split(".")))]
            sys.modules[name] = namespace
        file = root / "inference/agent/vision_context.py"
        spec = importlib.util.spec_from_file_location("astra_reviewed_vision_helpers", file)
        vision = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vision)
        os.environ.update(dict(zip(keys, ("current_grid", "10", "peak", "peak"))))
        assert vision.animation_image_mode() == vision.animation_death_image_mode() == "peak"
        blank, peak = ((0, 0), (0, 0)), ((1, 2), (0, 0))
        part, index = vision.animation_peak_part([blank, peak, blank], [(0, 0), (0, 1)])
        assert index == 0  # Helper indexes the chain after its initial frame.
        image = Image.open(io.BytesIO(base64.b64decode(part["image_url"]["url"].split(",", 1)[1])))
        assert image.size == (20, 20)
        assert image.getpixel((5, 5)) == vision.ARC_COLOR_MAP[1]
        assert image.getpixel((15, 5)) == vision.ARC_COLOR_MAP[2]
        assert vision.animation_peak_part([blank, blank], [(0, 0)]) == (None, -1)
        assert vision.animation_peak_part([blank, peak, blank], []) == (None, -1)
        os.environ["ARC3_ANIMATION_IMAGE"] = "1"
        try:
            vision.animation_image_mode()
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid animation enum accepted")
        return 6
    finally:
        for key in list(sys.modules):
            if key == "inference" or key.startswith("inference."):
                del sys.modules[key]
        sys.modules.update(saved_modules)
        for key, value in saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


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
        animation_contracts = verify_animation_helpers(root / "ARC3-Inference")
        return {"status": "PASS", "python_files_compiled": len(files), "embedded_bootstrap": "PASS",
                "negative_control_corrupt_eof": "PASS", "recovery_guard_contracts": 6,
                "animation_helper_contracts": animation_contracts,
                "scope": "CPU integration only; Kaggle gameplay UNVERIFIED"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("upstream", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.upstream)))
