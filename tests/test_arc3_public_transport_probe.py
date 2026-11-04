"""Structural and negative controls for the real ARC transport probe; no network."""
import unittest

from scripts.arc3_public_transport_probe import select_action, validate_catalog


class ArcPublicTransportProofTests(unittest.TestCase):
    def test_selects_safe_available_action(self):
        self.assertEqual(select_action([6, 4, 7]), 4)

    def test_rejects_mouse_and_reset_only(self):
        with self.assertRaises(ValueError):
            select_action([6, 7])

    def test_rejects_missing_action_list(self):
        with self.assertRaises(ValueError):
            select_action(None)

    def test_refuses_fabricated_game(self):
        with self.assertRaises(ValueError):
            validate_catalog([{"game_id": "ls20-9607627b"}], "fake-1234")

    def test_accepts_listed_game(self):
        self.assertEqual(
            validate_catalog(
                [{"game_id": "ls20-9607627b"}, {"game_id": "vc33-5430563c"}],
                "ls20-9607627b",
            ),
            2,
        )


if __name__ == "__main__":
    unittest.main()
