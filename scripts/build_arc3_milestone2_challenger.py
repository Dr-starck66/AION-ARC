"""Adapt the public Milestone 2 Duck solver and reuse ASTRA's gameplay gate.

Upstream attribution and license are retained in the source notebook. The
public two-game validation is not a hidden-score prediction or an ablation.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from build_arc3_gpu_challenger import cell
from build_arc3_verified_challenger import INSTRUMENTATION

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "kaggle/vendor/dfranzen-milestone2-v3-source.ipynb"
TARGET = ROOT / "kaggle/v29-milestone2/submission.ipynb"
SOURCE_SHA256 = "a6e4b090de28b4da0e7d1fe801881b94345ad68b7f377dd62cf0d8830013f6c4"


GRAPH_NAV_SOURCE = ROOT / "kaggle/arc3_graph_nav.py"


def graph_install_code() -> str:
    """Install the proven pixel-graph policy inside the *actual* Duck harness.

    The hook runs before model analysis only when a conservative visual
    signature matches. Original LLM behavior remains the fallback.
    The entire module is embedded in the notebook: Kaggle needs no network.
    """
    nav_source = GRAPH_NAV_SOURCE.read_text(encoding="utf-8")
    compile(nav_source, str(GRAPH_NAV_SOURCE), "exec")
    body = (
        "from pathlib import Path\n"
        "graph_module = BUNDLE_DIR / 'src/ARC3-Inference/inference/utils/astra_graph_nav.py'\n"
        "graph_module.parent.mkdir(parents=True, exist_ok=True)\n"
        "graph_module.write_text(" + repr(nav_source) + ", encoding='utf-8')\n"
        "solver_file = BUNDLE_DIR / 'src/ARC3-Inference/inference/framework/solver.py'\n"
        "solver_code = solver_file.read_text(encoding='utf-8')\n"
        "future = 'from __future__ import annotations\\n'\n"
        "anchor = '                if retry_analysis_step is None:\\n'\n"
        "if solver_code.count(future) != 1 or solver_code.count(anchor) != 1:\n"
        "    raise RuntimeError('ASTRA graph navigator hook anchors changed; abort')\n"
        "solver_code = solver_code.replace(future, future + "
        "'from inference.utils.astra_graph_nav import try_graph_step as _astra_graph_nav_try_step\\n', 1)\n"
        "solver_code = solver_code.replace(anchor, "
        "'                if _astra_graph_nav_try_step(self):\\n"
        "                    retry_analysis_step = None\\n"
        "                    continue\\n' + anchor, 1)\n"
        "compile(solver_code, str(solver_file), 'exec')\n"
        "solver_file.write_text(solver_code, encoding='utf-8')\n"
        "print('ASTRA_GRAPH_NAV_HOOK_INSTALLED', graph_module.stat().st_size, flush=True)\n"
    )
    compile(body, "astra_graph_install", "exec")
    return body


BOOTSTRAP = '''import json
import os
import platform
import subprocess
import sys
from pathlib import Path

if sys.version_info[:2] != (3, 12):
    raise RuntimeError("Offline wheels require Python 3.12: copy the upstream notebook and pin its original environment")
ASTRA_PROFILE = "milestone2"
ASTRA_PUBLIC_GAMES = ("ls20", "vc33")
ASTRA_PUBLIC_BUDGET_S = 1800
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
gpu = subprocess.check_output(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"], text=True).strip().splitlines()
if len(gpu) != 1 or "rtx pro 6000" not in gpu[0].lower():
    raise RuntimeError("Milestone 2 serving configuration requires a single RTX PRO 6000: " + repr(gpu))
work = Path("/kaggle/working")
work.mkdir(parents=True, exist_ok=True)
for stale in ("submission.parquet", "astra_gameplay.jsonl", "astra_runtime_evidence.json"):
    (work / stale).unlink(missing_ok=True)
print("ASTRA_V29_RUNTIME", json.dumps({"profile": ASTRA_PROFILE, "gpu": gpu, "python": platform.python_version(), "official_score": "UNVERIFIED", "preserved_submission": 57848621}), flush=True)
'''


def wrap(body: str, label: str) -> dict:
    tree = ast.parse(body)
    is_async = any(isinstance(n, ast.Await) for n in ast.walk(tree))
    compile(body, label, "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    if is_async:
        expr = f"await eval(compile({json.dumps(body, ensure_ascii=False)}, {label!r}, 'exec', flags=__import__('ast').PyCF_ALLOW_TOP_LEVEL_AWAIT), globals())\n"
    else:
        expr = f"exec(compile({json.dumps(body, ensure_ascii=False)}, {label!r}, 'exec'), globals())\n"
    result = cell(expr)
    result["id"] = label
    return result


def build() -> dict:
    raw = SOURCE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("Reviewed public source changed")
    source = json.loads(raw)
    cells = [{"cell_type": "markdown", "metadata": {}, "source": [
        "# ASTRA AION-ARC v2.9 — Milestone 2 comparison\n",
        "Reuses Daniel Franzen's Apache-2.0 public Duck solver, built on Tufa Labs, and ASTRA v2.8 instrumentation. All upstream notices are retained below.\n",
        "Normal runs: ls20 and vc33, one pass, 30 minutes after setup. Hidden rerun: original upstream competition settings and all gateway games.\n",
        "This changes both model and harness; differences are not isolated causal effects. Existing submission #57848621 is preserved. Official score UNVERIFIED.\n",
    ]}, wrap(BOOTSTRAP, "astra-v29-preflight")]
    for index, original in enumerate(source["cells"]):
        if original["cell_type"] != "code":
            cells.append(original)
            continue
        body = "".join(original["source"])
        if index == 2:
            magic, patch = body.split("\n", 1)
            assert magic == "%%writefile /kaggle/harness-changes.patch"
            # IPython's %%writefile adds the trailing newline. git apply needs it.
            patch = patch.rstrip("\n") + "\n"
            body = "from pathlib import Path\nPath('/kaggle/harness-changes.patch').write_text(" + repr(patch) + ")\n"
        elif index == 4:
            old = "!rm -Rf $BUNDLE_DIR\n!cp -a $ORIG_BUNDLE_DIR $BUNDLE_DIR"
            assert body.count(old) == 1
            body = body.replace(old, "import shutil\nshutil.rmtree(BUNDLE_DIR, ignore_errors=True)\nshutil.copytree(ORIG_BUNDLE_DIR, BUNDLE_DIR)")
            body += '\nfor input_path in (WHEELHOUSE_DIR, MODEL_DIR, DRAFT_MODEL_DIR, ORIG_BUNDLE_DIR):\n    if not Path(input_path).is_dir():\n        raise RuntimeError("Required Milestone 2 input is missing: " + input_path)\n'
        elif index == 14:
            cells.append(wrap(INSTRUMENTATION, "astra-v29-reused-gameplay-evidence"))
        elif index == 16:
            body += '\nif not TRUE_SUBMISSION:\n    bm.n_passes = 1\n    bm.solver.concurrency = 2\n    bm.solver.max_runtime_s_per_game = ASTRA_PUBLIC_BUDGET_S\n'
        elif index == 20:
            anchor = '    bm.games = _offline_games(competition_env_files)'
            assert body.count(anchor) == 1
            body = body.replace(anchor, anchor + '''
    wanted = set(ASTRA_PUBLIC_GAMES)
    bm.games = sorted((g for g in bm.games if g.env_name.split("-", 1)[0] in wanted), key=lambda g: g.env_name)
    if {g.env_name.split("-", 1)[0] for g in bm.games} != wanted:
        raise RuntimeError("Requested public comparison games are missing")
    print("ASTRA_PUBLIC_GAMES", [g.env_name for g in bm.games], flush=True)
''')
            old = '        soft_end = datetime.fromtimestamp(NOTEBOOK_START_EPOCH) + timedelta(seconds=budget - min(600.0, budget / 2))'
            assert body.count(old) == 1
            body = body.replace(old, '        soft_end = datetime.now() + timedelta(seconds=ASTRA_PUBLIC_BUDGET_S)')
            run = 'await bm.run(soft_end_time=soft_end, runtime_environment=target, minimal_diagnostics=TRUE_SUBMISSION)'
            assert body.count(run) == 1
            body = body.replace(run, run + '\n_astra_validate(bm)')
        cells.append(wrap(body, f"astra-v29-source-{index}"))
        if index == 4:
            cells.append(wrap(graph_install_code(), "astra-v29-graph-nav-install"))
    metadata = {"kernelspec": source["metadata"]["kernelspec"], "language_info": {"name": "python"},
                "kaggle": {**source["metadata"]["kaggle"], "accelerator": "nvidiaRtxPro6000", "isGpuEnabled": True},
                "astra": {"version": "2.9-experimental", "upstream": "dfranzen/arc-agi-3-milestone-2-solution@354920985", "source_sha256": SOURCE_SHA256, "official_score": "UNVERIFIED", "preserved_submission": 57848621,
                          "graph_nav": "visual-lattice-bfs", "graph_nav_source": "kaggle/arc3_graph_nav.py"}}
    return {"nbformat": 4, "nbformat_minor": 5, "metadata": metadata, "cells": cells}


if __name__ == "__main__":
    nb = build()
    TARGET.parent.mkdir(exist_ok=True)
    TARGET.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({"status": "PASS", "scope": "generation and compilation only", "cells": len(nb["cells"]), "bytes": TARGET.stat().st_size, "official_score": "UNVERIFIED"}))
