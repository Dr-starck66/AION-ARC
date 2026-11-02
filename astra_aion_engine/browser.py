"""Read-only adapter from AION ENGINE to existing ASTRA Cloud Browser v0.2 API.

Uses POST /v1/mission; no replacement browser, secret storage or deployment.
"""
from __future__ import annotations
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
import json
from .core import AionEngine, Feedback, Observation, Outcome, Plan

_ALLOWED_BROWSER_HOSTS = frozenset({
    "astra-cloud-browser-omega.dr-starck66.workers.dev",
    "astra-free-workers-omega.dr-starck66.workers.dev",
})

class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

def _check_https(url: str, hosts: frozenset[str]) -> None:
    if not isinstance(url, str):
        raise ValueError("invalid_url")
    parts = urlsplit(url)
    try:
        port = parts.port
    except ValueError as exc:
        raise ValueError("invalid_port") from exc
    if (parts.scheme != "https" or not parts.hostname
            or parts.username is not None or parts.password is not None
            or port not in (None, 443) or parts.hostname not in hosts
            or not parts.path.startswith("/")):
        raise ValueError("url_not_allowlisted")

def _request(url: str, token: str, payload: dict, timeout: int) -> tuple[int, dict]:
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    req = Request(url, method="POST", data=data, headers={
        "Content-Type": "application/json", "Authorization": "Bearer " + token,
    })
    opener = build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=timeout) as res:
            status, raw = res.status, res.read(131072)
    except HTTPError as exc:
        status, raw = exc.code, exc.read(131072)
    return status, json.loads(raw.decode("utf-8"))

@dataclass(frozen=True)
class BrowserMission:
    """Explicit read-only mission: no click, type, arbitrary JavaScript or screenshots."""
    url: str
    goal: str  # "seo-audit" or "text-proof"
    selector: str = ""
    contains: str = ""

    def payload(self, allowed_site_hosts: frozenset[str]) -> dict:
        _check_https(self.url, allowed_site_hosts)
        if self.goal == "seo-audit":
            return {"goal": "seo-audit", "url": self.url}
        if (self.goal == "text-proof" and 1 <= len(self.selector) <= 160
                and 1 <= len(self.contains) <= 250):
            return {"goal": "text-proof", "url": self.url,
                    "selector": self.selector, "contains": self.contains}
        raise ValueError("unsupported_mission")

@dataclass(frozen=True)
class BrowserOutcome:
    result: Outcome
    http_status: int | None
    proof: dict

class BrowserBridge:
    """Cloudflare Worker contract + AION fail-closed confirmation of DOM evidence."""

    def __init__(self, endpoint: str, token: str, allowed_site_hosts: frozenset[str],
                 *, transport=None, timeout: int = 25):
        _check_https(endpoint, _ALLOWED_BROWSER_HOSTS)
        if endpoint.rstrip("/") not in {
            "https://astra-cloud-browser-omega.dr-starck66.workers.dev/v1/mission",
            "https://astra-free-workers-omega.dr-starck66.workers.dev/browser/v1/mission",
        }:
            raise ValueError("unsupported_browser_endpoint")
        if not isinstance(token, str) or len(token) < 32:
            raise ValueError("private_browser_token_required")
        if not isinstance(allowed_site_hosts, frozenset) or not allowed_site_hosts:
            raise ValueError("explicit_site_allowlist_required")
        if not isinstance(timeout, int) or not 1 <= timeout <= 60:
            raise ValueError("invalid_timeout")
        self.endpoint = endpoint
        self.token = token
        self.allowed_site_hosts = allowed_site_hosts
        self.transport = transport or _request
        self.timeout = timeout

    def run(self, mission: BrowserMission) -> BrowserOutcome:
        payload = mission.payload(self.allowed_site_hosts)
        recorded: dict = {}
        finished = False

        def observe() -> Observation:
            return Observation(payload=None, legal_actions=frozenset({"RUN_READONLY_MISSION"}),
                               goal_reached=finished)

        def plan(_: Observation) -> Plan:
            return Plan(("RUN_READONLY_MISSION",), method="astra-browser-v0.2-mission")

        def execute(_: str) -> Feedback:
            nonlocal finished
            try:
                status, body = self.transport(self.endpoint, self.token, payload, self.timeout)
            except (URLError, TimeoutError, OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                recorded.update(http_status=None, reason=f"transport_error:{type(exc).__name__}")
                return Feedback(executed=False, changed=False)
            recorded["http_status"] = status
            if not isinstance(body, dict):
                recorded["reason"] = "malformed_browser_response"
                return Feedback(executed=False, changed=False)
            recorded["browser_status"] = body.get("status")
            recorded["proof_level"] = body.get("proofLevel")
            steps = body.get("steps")
            valid = False
            if (isinstance(steps, list) and status == 200
                    and body.get("status") == "PASS"
                    and body.get("proofLevel") == "BROWSER_EXECUTION_ONLY"):
                if mission.goal == "seo-audit" and len(steps) == 1:
                    s = steps[0]
                    f = s.get("findings") if isinstance(s, dict) else None
                    valid = (isinstance(s, dict) and s.get("action") == "audit"
                             and s.get("status") == "PASS"
                             and isinstance(f, dict) and isinstance(f.get("title"), str)
                             and isinstance(f.get("h1Count"), int))
                    if valid:
                        recorded["title"] = f["title"][:160]
                        recorded["h1_count"] = f["h1Count"]
                elif mission.goal == "text-proof" and len(steps) == 1:
                    s = steps[0]
                    valid = (isinstance(s, dict) and s.get("action") == "assertText"
                             and s.get("status") == "PASS" and s.get("matched") is True)
                    if valid:
                        recorded["dom_assertion"] = True
            if not valid:
                recorded["reason"] = "no_valid_chromium_dom_proof"
                return Feedback(executed=False, changed=False)
            finished = True
            return Feedback(executed=True, changed=True, goal_reached=True)

        outcome = AionEngine(observe, plan, execute, max_actions=1).run()
        return BrowserOutcome(outcome, recorded.get("http_status"), recorded)
