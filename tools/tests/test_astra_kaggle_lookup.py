#!/usr/bin/env python3
"""Offline regression gates for Kaggle owned-kernel lookup; no network or quota."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "astra_kaggle_research.py"
spec = importlib.util.spec_from_file_location("astra_kaggle_research", MODULE)
research = importlib.util.module_from_spec(spec)
spec.loader.exec_module(research)
JOB = {"name": "nfl", "slug": "drstarck/astra-nfl-2027-real-data-audit"}

class KaggleKernelLookupTests(unittest.TestCase):
    def fake(self, direct=(1, "Permission denied"), pages=None, alternative=(0, "COMPLETE")):
        pages = pages or {}
        calls = []
        def invoke(args, timeout=90):
            calls.append(args)
            if args[:2] == ("kernels", "status"):
                return direct if args[-1] == JOB["slug"] else alternative
            term = "targeted" if "--search" in args else "all"
            page = int(args[args.index("--page") + 1])
            return pages.get((term, page), (0, "ref,title\n"))
        patcher = patch.object(research, "invoke", invoke)
        patcher.start()
        self.addCleanup(patcher.stop)
        return calls

    def test_exact_slug_is_reused(self):
        calls = self.fake(direct=(0, "COMPLETE"))
        self.assertEqual(research.find_owned_kernel(JOB), JOB["slug"])
        self.assertEqual(len(calls), 1)

    def test_renamed_slug_is_resolved(self):
        self.fake(pages={("targeted", 1): (0, "ref,title\ndrstarck/astra-nfl-2027-real-data-audit-1,x\n")})
        self.assertEqual(research.find_owned_kernel(JOB), JOB["slug"] + "-1")

    def test_ambiguous_slug_rejected(self):
        self.fake(pages={("targeted", 1): (0, "ref,title\ndrstarck/astra-nfl-2027-copy-1,x\ndrstarck/astra-nfl-2027-copy-2,x\n")})
        with self.assertRaisesRegex(RuntimeError, "2 candidates"):
            research.find_owned_kernel(JOB)

    def test_missing_slug_never_pushes(self):
        calls = self.fake()
        with self.assertRaisesRegex(RuntimeError, "0 candidates"):
            research.find_owned_kernel(JOB)
        self.assertFalse(any(c[:2] == ("kernels", "push") for c in calls))

    def test_owned_but_unreadable_rejected(self):
        self.fake(pages={("targeted", 1): (0, "ref,title\ndrstarck/astra-nfl-2027-other,x\n")},
                  alternative=(1, "Permission denied"))
        with self.assertRaisesRegex(RuntimeError, "unreadable"):
            research.find_owned_kernel(JOB)

    def test_listing_error_rejected(self):
        self.fake(pages={("targeted", 1): (1, "rate limit")})
        with self.assertRaisesRegex(RuntimeError, "rate limit"):
            research.find_owned_kernel(JOB)

    def test_foreign_owner_rejected(self):
        self.fake(pages={("targeted", 1): (0, "ref,title\nother/astra-nfl-2027,x\n")})
        with self.assertRaisesRegex(RuntimeError, "0 candidates"):
            research.find_owned_kernel(JOB)

    def test_page_two_discovery(self):
        first = "ref,title\n" + "".join("drstarck/dummy-%03d,x\n" % i for i in range(100))
        self.fake(pages={("targeted", 1): (0, first),
                         ("targeted", 2): (0, "ref,title\ndrstarck/astra-nfl-2027-other,x\n")})
        self.assertEqual(research.find_owned_kernel(JOB), "drstarck/astra-nfl-2027-other")

if __name__ == "__main__":
    unittest.main(verbosity=2)
