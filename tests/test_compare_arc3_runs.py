import unittest
from scripts.compare_arc3_runs import compare

def sample(score):
    return {"engine": "arc3_official_local", "games": [
        {"game_id": "g"+str(i), "seed": 7, "score_percent": score,
         "levels_completed": 2, "actions": 20, "runtime_seconds": 1.5}
        for i in range(5)
    ]}

class ComparisonTests(unittest.TestCase):
    def test_game_score_gain_is_only_promising(self):
        out = compare(sample(5), sample(7))
        self.assertEqual(out["status"], "PROMISING_REQUIRES_OFFICIAL_VALIDATION")
        self.assertEqual(out["score_delta_percentage_points"], 2)
        self.assertIn("NOT_OFFICIAL", out["proof_level"])

    def test_regression_prevents_promotion(self):
        b = sample(5)
        b["games"][0]["score_percent"] = 0
        self.assertEqual(compare(sample(5), b)["status"], "REGRESSION")

    def test_small_sample_insufficient(self):
        a, b = sample(5), sample(7)
        a["games"], b["games"] = a["games"][:2], b["games"][:2]
        self.assertEqual(compare(a, b)["status"], "INSUFFICIENT_GAMES")

    def test_unpaired_rejected(self):
        b = sample(7)
        b["games"][0]["seed"] = 8
        with self.assertRaises(ValueError):
            compare(sample(5), b)

    def test_invalid_or_synthetic_rejected(self):
        b = sample(7)
        b["games"][0]["score_percent"] = 101
        with self.assertRaises(ValueError):
            compare(sample(5), b)
        with self.assertRaises(ValueError):
            compare({"engine":"synthetic","games":sample(5)["games"]}, sample(5))

    def test_duplicate_game_seed_rejected(self):
        b = sample(5)
        b["games"][1]["game_id"] = "g0"
        with self.assertRaises(ValueError):
            compare(sample(5), b)

if __name__ == "__main__":
    unittest.main()
