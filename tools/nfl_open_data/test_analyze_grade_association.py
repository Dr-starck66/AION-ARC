#!/usr/bin/env python3
"""Offline guarded test of ASTRA's no-contest scouting grade pilot."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("grade", Path(__file__).with_name("analyze_grade_association.py"))
grade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grade)
HEAD = "year,player,position_group,forty_yard_dash,draft_grade\n"
FIXTURE = HEAD + "\n".join([
    "2025,A,WR,4.3,90", "2025,B,WR,4.5,75",
    "2025,C,WR,4.7,65", "2025,D,WR,4.9,55",
    "2026,E,DB,4.4,90", "2026,F,DB,4.6,80",
    "2026,G,DB,4.8,60", "2026,H,DB,5.0,50"
]) + "\n"


class GradeTests(unittest.TestCase):
    def test_realistic_negative_correlation(self):
        r = grade.analyze(FIXTURE.encode(), permutations=30)
        self.assertEqual(r["rows_with_both_valid_and_classified"], 8)
        self.assertEqual(r["strata_count"], 2)
        self.assertEqual(r["usable_within_strata_rows"], 8)
        self.assertLess(r["within_year_position_pearson_r"], -0.9)
        self.assertEqual(r["competition"], "NOT_USED")
        self.assertEqual(r["predictive_validity"], "UNVERIFIED")

    def test_deterministic_permutations(self):
        a = grade.analyze(FIXTURE.encode(), permutations=40, seed=20261113)
        b = grade.analyze(FIXTURE.encode(), permutations=40, seed=20261113)
        self.assertEqual(a["monte_carlo_two_sided_p_corrected"], b["monte_carlo_two_sided_p_corrected"])
        self.assertEqual((a["null_min"], a["null_max"]), (b["null_min"], b["null_max"]))

    def test_missing_dash_is_rejected(self):
        data = FIXTURE + "2026,I,WR,,80\n"
        r = grade.analyze(data.encode(), permutations=5)
        self.assertEqual(r["skipped"]["missing_dash"], 1)

    def test_missing_grade_is_rejected(self):
        data = FIXTURE + "2026,I,WR,4.5,\n"
        r = grade.analyze(data.encode(), permutations=5)
        self.assertEqual(r["skipped"]["missing_grade"], 1)

    def test_missing_position_is_rejected(self):
        data = FIXTURE + "2026,I,,4.5,85\n"
        r = grade.analyze(data.encode(), permutations=5)
        self.assertEqual(r["skipped"]["unclassified"], 1)

    def test_out_of_range_is_rejected(self):
        data = FIXTURE + "2026,I,WR,2.0,120\n"
        r = grade.analyze(data.encode(), permutations=5)
        self.assertEqual(r["skipped"]["invalid"], 1)

    def test_ragged_csv_rejected(self):
        with self.assertRaisesRegex(ValueError, "Ragged"):
            grade.analyze((FIXTURE+"2026,J,WR,4.2,70,extra\n").encode(), permutations=5)

    def test_missing_columns_rejected(self):
        with self.assertRaisesRegex(ValueError, "Missing required columns"):
            grade.analyze(b"year,grade\n2026,80\n", permutations=5)

    def test_constant_within_group_refused(self):
        d = HEAD + "\n".join("2025,X"+str(i)+",WR,4.4,80" for i in range(10)) + "\n"
        with self.assertRaisesRegex(ValueError, "no within-stratum variation"):
            grade.analyze(d.encode(), permutations=5)

    def test_zero_permutations_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid permutation count"):
            grade.analyze(FIXTURE.encode(), permutations=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
