import unittest
from scripts.compare_arc3_runs import compare

def sample(score):
    return {"engine": "arc3_official_local", "games": [
        {"game_id": "g"+str(i), "seed": seed, "score_percent": score,
         "levels_completed": 2, "actions": 20, "runtime_seconds": 1.5}
        for i in range(25) for seed in (7, 8)
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
        self.assertEqual(compare(a, b)["status"], "INSUFFICIENT_GAME_COVERAGE")

    def test_five_game_two_seed_sample_is_not_sufficient(self):
        a, b = sample(5), sample(7)
        a["games"], b["games"] = a["games"][:10], b["games"][:10]
        out = compare(a, b)
        self.assertEqual(out["status"], "INSUFFICIENT_GAME_COVERAGE")
        self.assertEqual(out["unique_games"], 5)
        self.assertEqual(out["minimum_seeds_per_game"], 2)

    def test_twenty_five_games_only_one_seed_not_sufficient(self):
        a, b = sample(5), sample(7)
        a["games"] = [game for game in a["games"] if game["seed"] == 7]
        b["games"] = [game for game in b["games"] if game["seed"] == 7]
        out = compare(a, b)
        self.assertEqual(out["status"], "INSUFFICIENT_GAME_COVERAGE")
        self.assertEqual(out["unique_games"], 25)
        self.assertEqual(out["minimum_seeds_per_game"], 1)

    def test_level_completion_regression_blocks_score_gain(self):
        a, b = sample(5), sample(7)
        b["games"][0]["levels_completed"] = 1
        out = compare(a, b)
        self.assertEqual(out["status"], "REGRESSION")
        self.assertEqual(out["level_regressions"], 1)

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
        b["games"][1]["seed"] = 7  # same (g0, 7) pair as the first record
        with self.assertRaises(ValueError):
            compare(sample(5), b)

if __name__ == "__main__":
    unittest.main()
