"""Regression and negative controls; none is a Kaggle score."""
import ast
import importlib.util
import json
import pathlib
import sys
import tempfile
import functools
import threading
import types
import unittest
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_arc3_verified_challenger as builder


class RealGameBuilderTests(unittest.TestCase):
    def test_no_demo_only_execution_path(self):
        nb = builder.build()
        code = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
        self.assertNotIn("if TRUE_RERUN else None", code)
        self.assertIn("_astra_validate(bm)", code)
        self.assertIn("_astra_original_action", code)
        self.assertIn("_astra_original_chat", code)

    def test_both_ablation_profiles_compile(self):
        for profile in ("upstream", "recovery"):
            nb = builder.build(profile)
            self.assertEqual(nb["metadata"]["astra"]["official_score"], "UNVERIFIED")
            self.assertEqual(nb["metadata"]["astra"]["preserved_submission"], 57848621)
            for c in nb["cells"]:
                if c["cell_type"] == "code":
                    compile("".join(c["source"]), "cell", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)

    def test_gpu_specific_and_internet_off(self):
        cfg = builder.build()["metadata"]["kaggle"]
        self.assertEqual(cfg["accelerator"], "nvidiaRtxPro6000")
        self.assertFalse(cfg["isInternetEnabled"])
        self.assertIn("KAGGLE_GPU_TYPE", builder.BOOTSTRAP)

    def test_v26_recovery_precedes_unpickle(self):
        ids = [c["id"] for c in builder.build()["cells"]]
        self.assertLess(ids.index("astra-v26-reused-recovery"), ids.index("astra-v28-original-20"))
        self.assertLess(ids.index("astra-v28-instrumentation"), ids.index("astra-v28-original-20"))

    def test_original_signature_negative_control_aliases_translation(self):
        original = json.loads(builder.SOURCE.read_text())
        body = builder.unwrap("".join(original["cells"][10]["source"]))
        tree = ast.parse(body)
        guard = next(n.value.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == "guard" for t in n.targets))
        import textwrap
        ns = {}
        exec(compile(textwrap.dedent(guard), "guard", "exec"), ns)
        a, b = self.frames()
        # Demonstrates the defect in the shipped notebook, even though the
        # separately tested reference file already includes the bbox.
        self.assertEqual(ns["aion_frame_signature"](a), ns["aion_frame_signature"](b))
        corrected = guard.replace("                dims,", "                bbox,\n                dims,")
        ns2 = {}
        exec(compile(textwrap.dedent(corrected), "fixed_guard", "exec"), ns2)
        self.assertNotEqual(ns2["aion_frame_signature"](a), ns2["aion_frame_signature"](b))

    @staticmethod
    def frames():
        def frame(offset):
            return types.SimpleNamespace(shape=(64, 64), segmentation={"nodes":[{
                "color":"A", "hash":"same-position-invariant-shape", "pixels":4,
                "boundary":[[10, 10+offset], [12, 12+offset]], "children":[]}]})
        return frame(0), frame(4)

    def test_identity_patch_distinguishes_click_coordinates(self):
        # This is a source-level check; the live-upstream integration below
        # compiles the actual generated tool and embedded sandbox programs.
        self.assertIn('repr(spec.get("row")), repr(spec.get("col"))', builder.IDENTITY_PATCH)
        self.assertIn('margin = 0', builder.IDENTITY_PATCH)

    def test_invalid_profile_rejected(self):
        with self.assertRaises(ValueError):
            builder.build("random-fallback")


class RuntimeEvidenceTests(unittest.TestCase):
    def extract(self, name, scope):
        tree = ast.parse(builder.INSTRUMENTATION)
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
        exec(compile(ast.Module(body=[function], type_ignores=[]), "instrumentation_unit", "exec"), scope)
        return scope[name]

    def test_duck_dataclass_response_is_counted(self):
        events = []
        reply = types.SimpleNamespace(message={"content":"inspect board"}, usage={"completion_tokens":8})
        scope = {"functools":functools, "urlparse":urlparse, "_astra_original_chat":lambda *a,**k:reply,
                 "ASTRA_TRACE_LOCK":threading.Lock(), "ASTRA_EVIDENCE":{"model_responses":0,"errors":[]},
                 "_astra_event":events.append}
        call = self.extract("_astra_chat", scope)
        self.assertIs(call(types.SimpleNamespace(_model=types.SimpleNamespace(base_url="http://127.0.0.1:1234/v1"))), reply)
        self.assertEqual(scope["ASTRA_EVIDENCE"]["model_responses"], 1)
        self.assertEqual(events[0]["usage"]["completion_tokens"], 8)

    def test_external_model_endpoint_rejected_before_call(self):
        scope = {"functools":functools, "urlparse":urlparse, "_astra_original_chat":lambda *a,**k:self.fail("external call")}
        call = self.extract("_astra_chat", scope)
        with self.assertRaises(RuntimeError):
            call(types.SimpleNamespace(_model=types.SimpleNamespace(base_url="https://example.org/v1")))

    def test_reasoning_only_response_reaches_duck_unchanged(self):
        for key in ("reasoning", "reasoning_content"):
            with self.subTest(key=key):
                events = []
                reply = types.SimpleNamespace(message={"content":None, key:"Inspecting the board"},
                                              usage={"completion_tokens":12288}, finish_reason="length")
                scope = {"functools":functools, "urlparse":urlparse,
                         "_astra_original_chat":lambda *a,**k:reply,
                         "ASTRA_TRACE_LOCK":threading.Lock(),
                         "ASTRA_EVIDENCE":{"model_responses":0,"errors":[]}, "_astra_event":events.append}
                call = self.extract("_astra_chat", scope)
                agent = types.SimpleNamespace(_model=types.SimpleNamespace(base_url="http://127.0.0.1:8001/v1"))
                self.assertIs(call(agent), reply)
                self.assertTrue(events[0]["reasoning_only"])
                self.assertEqual(events[0]["finish_reason"], "length")
                self.assertEqual(scope["ASTRA_EVIDENCE"]["errors"], [])

    def test_entirely_empty_response_still_fails_and_is_recorded(self):
        for message in ({"content":None}, {}, None):
            with self.subTest(message=message):
                reply = types.SimpleNamespace(message=message, usage={})
                evidence = {"model_responses":0,"errors":[]}
                scope = {"functools":functools, "urlparse":urlparse,
                         "_astra_original_chat":lambda *a,**k:reply,
                         "ASTRA_TRACE_LOCK":threading.Lock(), "ASTRA_EVIDENCE":evidence}
                call = self.extract("_astra_chat", scope)
                with self.assertRaisesRegex(RuntimeError, "entirely empty"):
                    call(types.SimpleNamespace(_model=types.SimpleNamespace(base_url="http://127.0.0.1:8001/v1")))
                self.assertEqual(evidence["model_responses"], 0)
                self.assertEqual(evidence["errors"], ["model:EmptyAssistantResponse"])

    def validate(self, actions, responses, state="gave_up", errors=None, *, hidden=False, budget_timeouts=None):
        with tempfile.TemporaryDirectory() as tmp:
            work = pathlib.Path(tmp)
            (work / "submission.parquet").write_bytes(b"demo file is not evidence")
            scope = {"json":json, "WORKING_DIR":work, "ASTRA_PROFILE":"recovery", "TRUE_SUBMISSION":hidden,
                     "ASTRA_EVIDENCE":{"environment_actions":actions, "model_responses":responses,
                                       "errors":errors or [], "budget_timeouts":budget_timeouts or []}}
            validate = self.extract("_astra_validate", scope)
            run = types.SimpleNamespace(to_json_dict=lambda:{"game_id":"unit-control", "state":state})
            try:
                validate(types.SimpleNamespace(game_runs=[run]))
                raised = False
            except RuntimeError:
                raised = True
            report = json.loads((work / "astra_runtime_evidence.json").read_text())
            return raised, report

    def test_demo_parquet_does_not_pass_without_game_actions(self):
        raised, report = self.validate(0, 1)
        self.assertTrue(raised)
        self.assertEqual(report["status"], "FAIL")

    def test_random_actions_do_not_pass_without_model_responses(self):
        raised, _ = self.validate(10, 0)
        self.assertTrue(raised)

    def test_swallowed_benchmark_crash_cannot_pass(self):
        raised, _ = self.validate(10, 3, state="crashed")
        self.assertTrue(raised)

    def test_controlled_evidence_is_never_an_official_score(self):
        raised, report = self.validate(10, 3)
        self.assertFalse(raised)
        self.assertEqual(report["official_score"], "UNVERIFIED")
        self.assertIn("not an official Kaggle score", report["scope"])

    def test_expected_public_budget_stop_is_partial_never_full_pass(self):
        raised, report = self.validate(99, 50, state="cancelled", budget_timeouts=["ReadTimeout"])
        self.assertFalse(raised)
        self.assertEqual(report["status"], "PARTIAL")
        self.assertEqual(report["budget_timeouts"], ["ReadTimeout"])

    def test_early_public_timeout_still_blocks_validation(self):
        raised, report = self.validate(99, 50, state="cancelled", errors=["model:ReadTimeout"])
        self.assertTrue(raised)
        self.assertEqual(report["status"], "FAIL")

    def test_hidden_failures_are_preserved_and_not_relabelled_pass(self):
        raised, report = self.validate(99, 50, state="crashed", errors=["model:ReadTimeout"], hidden=True)
        self.assertFalse(raised)
        self.assertEqual(report["status"], "PARTIAL")
        self.assertEqual(report["crashed_games"], ["unit-control"])
        self.assertEqual(report["errors"], ["model:ReadTimeout"])
        self.assertEqual(report["official_score"], "UNVERIFIED")

    def test_hidden_no_real_gameplay_still_fails(self):
        raised, report = self.validate(0, 0, hidden=True)
        self.assertTrue(raised)
        self.assertEqual(report["status"], "FAIL")

    def test_budget_timeout_classifier_requires_expired_public_deadline(self):
        class ReadTimeout(Exception):
            pass
        def timeout(*args, **kwargs):
            raise ReadTimeout()
        agent = types.SimpleNamespace(_model=types.SimpleNamespace(base_url="http://127.0.0.1:8001/v1"))
        for hidden, deadline, expected in ((False, 99, True), (False, 101, False), (False, None, False), (True, 99, False)):
            with self.subTest(hidden=hidden, deadline=deadline):
                events = []
                evidence = {"model_responses":0,"errors":[]}
                scope = {"functools":functools, "urlparse":urlparse, "_astra_original_chat":timeout,
                         "ASTRA_TRACE_LOCK":threading.Lock(), "ASTRA_EVIDENCE":evidence,
                         "TRUE_SUBMISSION":hidden,"ASTRA_PUBLIC_STOP_DEADLINE":deadline,
                         "time":types.SimpleNamespace(monotonic=lambda:100), "_astra_event":events.append}
                call = self.extract("_astra_chat", scope)
                with self.assertRaises(ReadTimeout):
                    call(agent)
                self.assertEqual(bool(evidence.get("budget_timeouts")), expected)
                self.assertEqual(events[0]["expected_public_budget_stop"], expected)
                self.assertEqual(bool(evidence["errors"]), not expected)


if __name__ == "__main__":
    unittest.main()
