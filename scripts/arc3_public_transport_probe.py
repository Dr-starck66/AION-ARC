#!/usr/bin/env python3
"""One real ARC-AGI-3 public transport smoke test, NOT an AION score comparison.

Reuses ONE cookie-aware HTTP session for anonkey, catalog, scorecard,
RESET, one safe ACTION, and close. No Kaggle token, model, or GPU is used.
The API does not expose a verified seed in this protocol.
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "https://three.arcprize.org"
DEFAULT_GAME = "ls20-9607627b"


class ArcPublicTransport:
    def __init__(self) -> None:
        self.cookies = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookies)
        )
        self.key = None

    def request(self, method: str, path: str, body: dict | None = None) -> dict:
        headers = {
            "Accept": "application/json",
            "User-Agent": "AION-ARC-public-transport-proof/1.0",
        }
        if self.key:
            headers["X-API-Key"] = self.key
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            BASE_URL + path,
            data=json.dumps(body).encode("utf-8") if body is not None else None,
            headers=headers,
            method=method,
        )
        try:
            with self.opener.open(request, timeout=20) as response:
                if response.status != 200:
                    raise RuntimeError(f"Unexpected HTTP {response.status} on {path}")
                result = json.load(response)
                if not isinstance(result, dict) and path != "/api/games":
                    raise ValueError(f"Unexpected response shape on {path}")
                return result
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"ARC returned HTTP {error.code} on {path}") from None


def select_action(available_actions: list) -> int:
    """Avoid mouse ACTION6 and reset ACTION7 in a non-scoring smoke test."""
    if not isinstance(available_actions, list):
        raise ValueError("Missing available action list")
    for candidate in (1, 2, 3, 4, 5):
        if candidate in available_actions:
            return candidate
    raise ValueError("No safe non-mouse action offered by the game")


def validate_catalog(games: list, game_id: str) -> int:
    if not isinstance(games, list):
        raise ValueError("Expected ARC games list")
    if not any(isinstance(item, dict) and item.get("game_id") == game_id for item in games):
        raise ValueError("Requested game not present in authenticated ARC catalog")
    return len(games)


def probe(game_id: str = DEFAULT_GAME) -> dict:
    start_at = time.monotonic()
    transport = ArcPublicTransport()
    anonymous = transport.request("GET", "/api/games/anonkey")
    key = anonymous.get("api_key")
    if not isinstance(key, str) or not key:
        raise RuntimeError("Anonymous ARC API key unavailable")
    transport.key = key  # Never print or persist this token.
    games = transport.request("GET", "/api/games")
    game_count = validate_catalog(games, game_id)
    scorecard = transport.request("POST", "/api/scorecard/open", {"tags": ["astra-public-transport-probe"]})
    card_id = scorecard.get("card_id")
    if not isinstance(card_id, str) or not card_id:
        raise ValueError("Scorecard was not created")
    closed = False
    try:
        before = transport.request(
            "POST", "/api/cmd/RESET", {"card_id": card_id, "game_id": game_id}
        )
        if before.get("game_id") != game_id or not before.get("guid") or not before.get("frame"):
            raise RuntimeError("ARC did not return a real initialized game frame")
        action = select_action(before.get("available_actions"))
        after = transport.request(
            "POST", f"/api/cmd/ACTION{action}",
            {"game_id": game_id, "guid": before["guid"]},
        )
        if after.get("game_id") != game_id or not after.get("frame"):
            raise RuntimeError("ARC did not return a real post-action game frame")
        closed_result = transport.request("POST", "/api/scorecard/close", {"card_id": card_id})
        closed = True
        return {
            "status": "PASS",
            "scope": "public_api_transport_one_real_action_only",
            "official_kaggle_score_status": "UNVERIFIED",
            "aion_v25_v26_score_comparison": "UNVERIFIED",
            "source": BASE_URL,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "game_id": game_id,
            "available_game_count": game_count,
            "scorecard_open": True,
            "scorecard_closed": True,
            "reset_http": 200,
            "action_http": 200,
            "action": f"ACTION{action}",
            "start_state": before.get("state"),
            "end_state": after.get("state"),
            "start_levels_completed": before.get("levels_completed"),
            "end_levels_completed": after.get("levels_completed"),
            "raw_scorecard_score": closed_result.get("score"),
            "seed_provenance": "UNVERIFIED_NOT_EXPOSED",
            "cookie_session_used": len(transport.cookies) > 0,
            "elapsed_seconds": round(time.monotonic() - start_at, 3),
        }
    finally:
        if not closed:
            try:
                transport.request("POST", "/api/scorecard/close", {"card_id": card_id})
            except Exception:
                pass  # Preserve the original error, never fabricate a closed card.


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-id", default=DEFAULT_GAME)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = probe(args.game_id)
    except Exception as error:
        result = {
            "status": "FAIL",
            "scope": "public_api_transport",
            "error_type": type(error).__name__,
            "error": str(error),
            "official_kaggle_score_status": "UNVERIFIED",
            "aion_v25_v26_score_comparison": "UNVERIFIED",
        }
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
