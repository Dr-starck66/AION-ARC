"""Build a real-game challenger; never confuse commit Parquet with gameplay.

Reuses v2.5 and the existing v2.6 recovery patch. No credentials or network.
The old v2.7 and official submission remain untouched.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

from build_arc3_gpu_challenger import SOURCE, ROOT, cell, unwrap

TARGET = ROOT / "kaggle/ASTRA-AION-ARC-v2.8-REAL-GAMES.ipynb"
DATASETS = [
    "jeroencottaar/taaf-kaggle-source-share",
    "driessmit1/arc3-vllm-h100-wheelhouse-v3",
    "driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot",
]

BOOTSTRAP = r'''import json
import os
import platform
import random
import subprocess
import sys
from pathlib import Path

if sys.version_info[:2] != (3, 12):
    raise RuntimeError("Offline vLLM wheels require Python 3.12; copy the public Tufa notebook and pin its original environment")
TRUE_RERUN = os.environ.get("KAGGLE_IS_COMPETITION_RERUN", "").strip().lower() in ("1", "true")
ASTRA_PROFILE = os.environ.get("ASTRA_PROFILE", "recovery").strip().lower()
if ASTRA_PROFILE not in ("upstream", "recovery"):
    raise ValueError("ASTRA_PROFILE must be upstream or recovery")
ASTRA_PUBLIC_GAMES = ("ls20", "vc33")
ASTRA_PUBLIC_BUDGET_S = 1800
random.seed(0)

# Fail before the expensive offline install if inputs/hardware are missing.
ASTRA_COMPETITION_ROOT = Path("/kaggle/input/competitions/arc-prize-2026-arc-agi-3")
if not (ASTRA_COMPETITION_ROOT / "arc_agi_3_wheels").is_dir():
    candidates = sorted(Path("/kaggle/input").rglob("arc_agi_3_wheels"))
    if len(candidates) != 1:
        raise RuntimeError("Competition wheelhouse missing or ambiguous")
    ASTRA_COMPETITION_ROOT = candidates[0].parent
if not TRUE_RERUN and not (ASTRA_COMPETITION_ROOT / "environment_files").is_dir():
    raise RuntimeError("Public environment files are not attached")
for ref in __DATASETS__:
    owner, slug = ref.split("/", 1)
    paths = [Path("/kaggle/input") / slug, Path("/kaggle/input/datasets") / owner / slug]
    if not any(p.is_dir() for p in paths):
        raise RuntimeError("Missing attached dataset: " + ref)
gpu = subprocess.check_output([
    "nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"
], text=True, timeout=15).strip().splitlines()
if len(gpu) != 1 or not any(s in gpu[0].lower() for s in ("rtx pro 6000", "h100")):
    raise RuntimeError("Duck FP8 setup requires one RTX PRO 6000 or H100; found " + repr(gpu))
os.environ["KAGGLE_GPU_TYPE"] = "h100" if "h100" in gpu[0].lower() else "rtx-pro-6000"
os.environ["KAGGLE_GPU_COUNT"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
work = Path("/kaggle/working")
work.mkdir(parents=True, exist_ok=True)
# Prevent a stale demo artifact from masquerading as a new successful run.
for stale in ("submission.parquet", "astra_gameplay.jsonl", "astra_runtime_evidence.json"):
    (work / stale).unlink(missing_ok=True)
print("ASTRA_V28_RUNTIME", json.dumps({
    "mode": "HIDDEN_RERUN" if TRUE_RERUN else "REAL_PUBLIC_GAMES",
    "profile": ASTRA_PROFILE, "gpu": gpu, "python": platform.python_version(),
    "official_score": "UNVERIFIED", "preserved_submission": 57848621,
}), flush=True)
'''.replace("__DATASETS__", repr(DATASETS))

# Fix only demonstrated identity/recovery defects. Leave the original solver intact.
IDENTITY_PATCH = r'''import ast
import re
import textwrap

stext = sandbox_path.read_text()
old_signature = "                dims,\n                len(node.get(\"children\", []) or []),"
new_signature = "                bbox,\n                dims,\n                len(node.get(\"children\", []) or []),"
if stext.count(old_signature) != 1:
    raise RuntimeError("ASTRA v2.8: sandbox signature anchor changed")
stext = stext.replace(old_signature, new_signature, 1)
# ACTION6 at another coordinate is a different experiment. The old audit ignores
# coordinates entirely; keep its warning as a diagnostic rather than blocking it.
old_inert = 'if inert_warning and not bool(spec.get("force_probe", False)):'
new_inert = 'if inert_warning and str(spec.get("action", "")).upper() not in ("ACTION6", "MOUSE") and not bool(spec.get("force_probe", False)):'
if stext.count(old_inert) != 1:
    raise RuntimeError("ASTRA v2.8: inert-probe anchor changed")
stext = stext.replace(old_inert, new_inert, 1)
# The original ASTRA helpers inject triple-double-quoted docstrings inside
# Duck's raw triple-double-quoted bootstrap. Outer-cell compilation misses
# the resulting SyntaxError. Use another delimiter for the inner docstrings.
bootstrap_start = stext.index('    r"""') + len('    r"""')
bootstrap_end = stext.index('\n    """\n).replace(', bootstrap_start)
stext = stext[:bootstrap_start] + stext[bootstrap_start:bootstrap_end].replace('"""', "\x27\x27\x27") + stext[bootstrap_end:]
sandbox_path.write_text(stext)

ttext = tool_path.read_text()
old_key = 'action_key = (repr(pre_signature), str(spec.get("action", "")).upper())'
new_key = 'action_key = (repr(pre_signature), str(spec.get("action", "")).upper(), repr(spec.get("row")), repr(spec.get("col")))'
if ttext.count(old_key) != 1:
    raise RuntimeError("ASTRA v2.8: coordinate identity anchor changed")
ttext = ttext.replace(old_key, new_key, 1)
# Edge cells are observable gameplay until proven otherwise. Do not crop them
# from the persistent fatal-action identity merely because they may be HUD.
old_margin = "margin = 3 if rows >= 12 and cols >= 12 else 0"
if ttext.count(old_margin) != 1:
    raise RuntimeError("ASTRA v2.8: host signature anchor changed")
ttext = ttext.replace(old_margin, "margin = 0", 1)
tool_path.write_text(ttext)
ptext = prompts_path.read_text()
ptext = ptext.replace("aion_information_gain(predictions_by_action)", "aion_prediction_entropy(predictions_by_action)")
prompts_path.write_text(ptext)

# Compile the generated Python AND the embedded sandbox bootstrap, not just
# the outer notebook cells which contain these programs as strings.
for patched in (prompts_path, tool_path, sandbox_path):
    compile(patched.read_text(), str(patched), "exec")
tree = ast.parse(sandbox_path.read_text())
bootstrap_assignment = next(n for n in tree.body if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "_SANDBOX_BOOTSTRAP" for t in n.targets))
bootstrap = textwrap.dedent(next(n.value for n in ast.walk(bootstrap_assignment.value)
    if isinstance(n, ast.Constant) and isinstance(n.value, str) and "    def main():" in n.value))
compile(bootstrap, "astra_v28_sandbox_bootstrap", "exec")
print("ASTRA_V28_PATCH_COMPILE_PASS", flush=True)
'''

INSTRUMENTATION = r'''import functools
import hashlib
import threading
import time
from urllib.parse import urlparse

import taaf.game_api
from inference.agent.tool_agent import ToolAgent

ASTRA_EVIDENCE = {"model_responses": 0, "environment_actions": 0, "errors": []}
ASTRA_TRACE_LOCK = threading.Lock()
ASTRA_TRACE_PATH = WORKING_DIR / "astra_gameplay.jsonl"
ASTRA_PUBLIC_STOP_DEADLINE = None

def _astra_event(event):
    with ASTRA_TRACE_LOCK:
        with ASTRA_TRACE_PATH.open("a") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")

_astra_original_chat = ToolAgent._chat_completion
@functools.wraps(_astra_original_chat)
def _astra_chat(self, *args, **kwargs):
    if urlparse(self._model.base_url).hostname not in ("localhost", "127.0.0.1", "::1"):
        raise RuntimeError("ASTRA requires the offline local model endpoint")
    try:
        reply = _astra_original_chat(self, *args, **kwargs)
    except Exception as exc:
        expected_stop = (
            not TRUE_SUBMISSION and ASTRA_PUBLIC_STOP_DEADLINE is not None
            and type(exc).__name__ in ("ReadTimeout", "Timeout")
            and time.monotonic() >= ASTRA_PUBLIC_STOP_DEADLINE
        )
        with ASTRA_TRACE_LOCK:
            if expected_stop:
                ASTRA_EVIDENCE.setdefault("budget_timeouts", []).append(type(exc).__name__)
            else:
                ASTRA_EVIDENCE["errors"].append("model:" + type(exc).__name__)
        _astra_event({"kind": "model_exception", "type": type(exc).__name__,
                      "expected_public_budget_stop": expected_stop})
        raise
    # Duck returns _ChatCompletionResult, not the raw OpenAI JSON body.
    message = getattr(reply, "message", None)
    usage = getattr(reply, "usage", None)
    # Qwen/SGLang can return a reasoning-only turn (including length-limited
    # turns). Duck owns its continuation/recovery policy; do not abort before
    # it can process that real response. An entirely empty reply still fails.
    reasoning = (message.get("reasoning_content") or message.get("reasoning")) if isinstance(message, dict) else None
    if not isinstance(message, dict) or not (message.get("content") or message.get("tool_calls") or reasoning):
        with ASTRA_TRACE_LOCK:
            ASTRA_EVIDENCE["errors"].append("model:EmptyAssistantResponse")
        raise RuntimeError("Local model returned an entirely empty assistant response")
    with ASTRA_TRACE_LOCK:
        ASTRA_EVIDENCE["model_responses"] += 1
    _astra_event({"kind": "local_model_response", "usage": usage or {},
                  "reasoning_only": bool(reasoning and not message.get("content") and not message.get("tool_calls")),
                  "finish_reason": getattr(reply, "finish_reason", "")})
    return reply
ToolAgent._chat_completion = _astra_chat

_astra_original_action = taaf.game_api.GameAPI._execute_action
@functools.wraps(_astra_original_action)
def _astra_action(self, action):
    try:
        result = _astra_original_action(self, action)
    except Exception as exc:
        with ASTRA_TRACE_LOCK:
            ASTRA_EVIDENCE["errors"].append("environment:" + type(exc).__name__)
        raise
    pixels = result.frame.data
    event = {
        "kind": "environment_return", "game_id": self.env_name,
        "action": action.id.name, "data": dict(action.data),
        "levels_completed": int(result.levels_completed),
        "engine_state": result.raw.state.name,
        "observation_sha256": hashlib.sha256(pixels.tobytes()).hexdigest(),
    }
    with ASTRA_TRACE_LOCK:
        ASTRA_EVIDENCE["environment_actions"] += 1
    _astra_event(event)
    return result
taaf.game_api.GameAPI._execute_action = _astra_action

def _astra_validate(benchmark):
    runs = [r.to_json_dict() for r in benchmark.game_runs]
    crashed = [r.get("game_id") for r in runs if r.get("state") == "crashed"]
    played = ASTRA_EVIDENCE["model_responses"] > 0 and ASTRA_EVIDENCE["environment_actions"] > 0
    degraded = bool(crashed or ASTRA_EVIDENCE["errors"] or ASTRA_EVIDENCE.get("budget_timeouts"))
    status = "FAIL" if not played else ("PARTIAL" if degraded else "PASS")
    # Public validation stays strict for genuine crashes and early errors.
    # During a hidden rerun, retain every failure and mark PARTIAL while letting
    # Kaggle score the real actions already taken in the other games.
    reject = not played or (not TRUE_SUBMISSION and (crashed or ASTRA_EVIDENCE["errors"]))
    if reject:
        status = "FAIL"
    evidence = {
        **ASTRA_EVIDENCE, "profile": ASTRA_PROFILE,
        "mode": "hidden" if TRUE_SUBMISSION else "public",
        "runs": runs, "crashed_games": crashed,
        "status": status,
        "scope": "instrumented gameplay only; not an official Kaggle score",
        "official_score": "UNVERIFIED",
    }
    (WORKING_DIR / "astra_runtime_evidence.json").write_text(json.dumps(evidence, indent=2))
    if reject:
        raise RuntimeError("ASTRA gameplay gate failed; see astra_runtime_evidence.json")
    print("ASTRA_REAL_GAMEPLAY_" + status, json.dumps({
        "model_responses": evidence["model_responses"], "environment_actions": evidence["environment_actions"],
        "games": len(runs), "crashed_games": crashed, "errors": evidence["errors"],
        "budget_timeouts": evidence.get("budget_timeouts", []), "official_score": "UNVERIFIED",
    }), flush=True)
'''


def wrapped(body: str, label: str, *, asynchronous=False, overlay=False) -> dict:
    condition = ' if ASTRA_PROFILE == "recovery" else None' if overlay else ""
    if asynchronous:
        expr = ("await eval(compile(" + json.dumps(body, ensure_ascii=False) + ", " + repr(label)
                + ', "exec", flags=__import__("ast").PyCF_ALLOW_TOP_LEVEL_AWAIT), globals())')
    else:
        expr = "exec(compile(" + json.dumps(body, ensure_ascii=False) + ", " + repr(label) + ', "exec"), globals())'
    result = cell(expr + condition + "\n")
    result["id"] = label
    return result


def build(profile="recovery") -> dict:
    if profile not in ("upstream", "recovery"):
        raise ValueError("Unknown profile")
    original = json.loads(SOURCE.read_text())
    recovery_nb = json.loads((ROOT / "kaggle/AION-ARC-v2.6-recovery.ipynb").read_text())
    recovery = next("".join(c["source"]) for c in recovery_nb["cells"] if c.get("id") == "aion-v26-recovery-policy")
    headers = (
        "# ASTRA AION-ARC v2.8 — real-game validation challenger\n\n"
        "Reuses the Tufa Labs Duck/TAAF notebook and original AION v2.5 overlays. "
        "Default profile: " + profile + ". Existing official submission #57848621 is preserved.\n\n"
        "Normal execution plays ls20 and vc33 with the offline local model for at most 30 minutes after setup. "
        "Competition rerun plays the gateway game list without the public-game filter. "
        "The commit-only Parquet is generated AFTER instrumented model responses and environment actions. "
        "It is never evidence of a leaderboard score.\n\n"
        "No Kaggle run or score is claimed. All third-party code/model notices remain applicable.\n"
    )
    # Reuse the repository's original attribution, omitting stale execution metadata.
    attribution = "".join(original["cells"][0]["source"])
    cells = [{"cell_type": "markdown", "id": "astra-v28-notice", "metadata": {}, "source": headers.splitlines(keepends=True)}]
    cells.append({"cell_type": "markdown", "id": "upstream-attribution", "metadata": {},
                  "source": attribution.splitlines(keepends=True), "attachments": original["cells"][0].get("attachments", {})})
    cells.append(wrapped(BOOTSTRAP.replace('get("ASTRA_PROFILE", "recovery")', f'get("ASTRA_PROFILE", "{profile}")'), "astra-v28-runtime"))
    for i, c in enumerate(original["cells"]):
        if c.get("cell_type") != "code":
            continue
        body = unwrap("".join(c["source"]))
        is_overlay = str(c.get("id", "")).startswith("aion-")
        if c.get("id") == "10":
            cells.append(wrapped(recovery, "astra-v26-reused-recovery", overlay=True))
            cells.append(wrapped(IDENTITY_PATCH, "astra-v28-identity", overlay=True))
            cells.append(wrapped(INSTRUMENTATION, "astra-v28-instrumentation"))
        body = body.replace('"/kaggle/input/competitions/arc-prize-2026-arc-agi-3/arc_agi_3_wheels"', 'str(ASTRA_COMPETITION_ROOT / "arc_agi_3_wheels")')
        if "await bm.run(" in body:
            anchor = "bm.n_passes = 1\n"
            selection = '''if not TRUE_SUBMISSION:
    wanted = set(ASTRA_PUBLIC_GAMES)
    bm.games = sorted((g for g in bm.games if g.env_name.split("-", 1)[0] in wanted), key=lambda g: g.env_name)
    if {g.env_name.split("-", 1)[0] for g in bm.games} != wanted:
        raise RuntimeError("One or more requested public validation games are missing")
    print("ASTRA_PUBLIC_GAMES", [g.env_name for g in bm.games], flush=True)

'''
            if body.count(anchor) != 1:
                raise ValueError("game selection anchor changed")
            body = body.replace(anchor, selection + anchor, 1)
            body = body.replace('budget = float(getattr(target, "max_runtime_s", 0.0) or 0.0)', 'budget = float(ASTRA_PUBLIC_BUDGET_S + 600)')
            body = body.replace('datetime.fromtimestamp(NOTEBOOK_START_EPOCH)', 'datetime.now()')
            run_anchor = "    await bm.run(soft_end_time=soft_end, runtime_environment=target, minimal_diagnostics=TRUE_SUBMISSION)\n"
            if body.count(run_anchor) != 1:
                raise ValueError("benchmark execution anchor changed")
            body = body.replace(run_anchor, run_anchor + "    _astra_validate(bm)\n", 1)
        cells.append(wrapped(body, "astra-v28-original-" + str(i), asynchronous="await bm.run(" in body, overlay=is_overlay))
    metadata = {
        "kernelspec": original["metadata"]["kernelspec"],
        "language_info": {"name": "python"},
        "kaggle": {"accelerator": "nvidiaRtxPro6000", "isInternetEnabled": False, "isGpuEnabled": True,
                   "language": "python", "sourceType": "notebook"},
        "astra": {"version": "2.8-experimental", "profile": profile, "kaggle_execution": "UNVERIFIED",
                  "official_score": "UNVERIFIED", "preserved_submission": 57848621},
    }
    for i, c in enumerate(cells):
        if c["cell_type"] == "code":
            compile("".join(c["source"]), f"v28_cell_{i}", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    return {"nbformat": 4, "nbformat_minor": 5, "metadata": metadata, "cells": cells}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("upstream", "recovery"), default="recovery")
    parser.add_argument("--out", type=Path, default=TARGET)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(build(args.profile), indent=1, ensure_ascii=False) + "\n").encode()
    args.out.write_bytes(data)
    metadata = {
        "id": "drstarck/astra-aion-arc3-v28-" + args.profile,
        "title": "ASTRA AION ARC3 v2.8 " + args.profile,
        "code_file": args.out.name, "language": "python", "kernel_type": "notebook",
        "is_private": True, "enable_gpu": True, "enable_tpu": False, "enable_internet": False,
        "dataset_sources": DATASETS, "competition_sources": ["arc-prize-2026-arc-agi-3"],
        "kernel_sources": [], "model_sources": [],
    }
    (args.out.parent / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "scope": "notebook build only", "profile": args.profile,
                      "path": str(args.out), "sha256": hashlib.sha256(data).hexdigest(),
                      "kaggle_execution": "UNVERIFIED", "score": "UNVERIFIED"}))


if __name__ == "__main__":
    main()
