"""Exercise the actual notebook patches on a supplied public Duck source tree.

This compiles real upstream files and the embedded sandbox. No LLM, GPU,
gameplay or score is claimed. The source directory is never modified.
"""
import argparse
import ast
import contextlib
import io
import importlib.util
import json
import pathlib
import sys
import tempfile

from build_arc3_gpu_challenger import SOURCE, unwrap
from build_arc3_verified_challenger import IDENTITY_PATCH, build


def verify(upstream):
    upstream = pathlib.Path(upstream).resolve()
    tool = upstream / "ARC3-Inference/inference/agent/tool_agent.py"
    if not tool.is_file():
        raise FileNotFoundError(tool)
    original = json.loads(SOURCE.read_text())
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp) / "work"
        work.mkdir()
        bundle = pathlib.Path(tmp) / "bundle"
        (bundle / "src").mkdir(parents=True)
        (bundle / "src/duck").symlink_to(upstream / "ARC3-Inference", target_is_directory=True)
        # Path.rglob does not follow a symlink at the repo root. Copy only the
        # inference source, avoiding benchmark artifacts and any external data.
        (bundle / "src/duck").unlink()
        import shutil
        shutil.copytree(upstream / "ARC3-Inference/inference", bundle / "src/duck/inference")
        ns = {"WORKING_DIR": work, "BUNDLE_DIR": bundle, "ASTRA_PROFILE":"recovery"}
        output = io.StringIO()
        saved_path = list(sys.path)
        saved_modules = {k:v for k,v in sys.modules.items() if k == "inference" or k.startswith("inference.")}
        try:
            with contextlib.redirect_stdout(output):
                for c in original["cells"]:
                    if c.get("cell_type") == "code" and str(c.get("id", "")).startswith("aion-"):
                        exec(compile(unwrap("".join(c["source"])), c["id"], "exec"), ns)
                v28 = build()
                recovery = next(c for c in v28["cells"] if c.get("id") == "astra-v26-reused-recovery")
                exec(compile("".join(recovery["source"]), recovery["id"], "exec"), ns)
                try:
                    compile(ns["sandbox_path"].read_text(), "v27_negative_control", "exec")
                except SyntaxError as exc:
                    negative_control = {"status":"FAIL", "expected":True,
                                        "error":type(exc).__name__, "line":exc.lineno}
                else:
                    raise AssertionError("Expected original overlay syntax defect was not reproduced")
                exec(compile(IDENTITY_PATCH, "identity_patch", "exec"), ns)
            for p in pathlib.Path(ns["overlay_root"]).rglob("*.py"):
                compile(p.read_text(), str(p), "exec")
            # An actual function extracted from patched host source must retain
            # gameplay at the outermost border, not merge it with another state.
            tree = ast.parse(ns["tool_path"].read_text())
            signature = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_aion_host_signature")
            scope = {}
            exec(compile(ast.Module(body=[signature], type_ignores=[]), "host_signature", "exec"), scope)
            from types import SimpleNamespace
            grid = [[0]*16 for _ in range(16)]
            changed = [row[:] for row in grid]
            changed[0][0] = 5
            assert scope["_aion_host_signature"](SimpleNamespace(level=1,grid=grid)) != scope["_aion_host_signature"](SimpleNamespace(level=1,grid=changed))
            # Run the REAL patched subprocess sandbox with a controlled host.
            # This validates action transport, not an ARC game or LLM score.
            spec = importlib.util.spec_from_file_location("astra_sandbox_integration", ns["sandbox_path"])
            sandbox = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(sandbox)
            frame = {"grid":grid, "ascii":"synthetic test frame", "level":1, "step":2, "shape":[16,16]}
            state = {"current_frame":frame, "history":[
                {"action":"RESET", "frame":frame}, {"action":"MOUSE", "frame":frame}],
                "last_action_result":{"executed":True, "board_changed":False},
                "valid_actions":["MOUSE", "UP", "RESET"]}
            executed = []
            def controlled_host(actions):
                executed.extend(actions)
                return {"action_result":{"executed":True, "board_changed":False}, "state":state}
            child = sandbox.run_sandboxed_python(
                code='action({"action":"MOUSE","row":5,"col":6})\naction({"action":"MOUSE","row":5,"col":9})\nresult="transport-ok"',
                timeout_seconds=10, initial_state=state, action_handler=controlled_host)
            if child.get("error") or len(executed) != 2 or child.get("result") != "transport-ok":
                raise AssertionError({"child":child, "executed":executed})
            return {"status":"PASS", "scope":"real upstream source patch and nested compilation only",
                    "patched_python_files":len(list(pathlib.Path(ns["overlay_root"]).rglob("*.py"))),
                    "original_v27_negative_control":negative_control,
                    "real_sandbox_subprocess":{"status":"PASS", "controlled_actions":len(executed), "arc_game":False},
                    "logs":output.getvalue().splitlines(), "gameplay":"UNVERIFIED", "score":"UNVERIFIED"}
        finally:
            sys.path[:] = saved_path
            for name in list(sys.modules):
                if name == "inference" or name.startswith("inference."):
                    del sys.modules[name]
            sys.modules.update(saved_modules)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("upstream", type=pathlib.Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.upstream), indent=2))
