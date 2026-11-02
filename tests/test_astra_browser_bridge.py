"""Contract tests: AION core -> existing ASTRA Browser /v1/mission API."""
import json
import unittest
from astra_aion_engine.browser import BrowserBridge, BrowserMission

ENDPOINT = "https://astra-cloud-browser-omega.dr-starck66.workers.dev/v1/mission"
TOKEN = "test-only-non-production-token-0123456789012"
SITES = frozenset({"example.com"})

def make(report, status=200):
    calls = []
    def transport(url, token, payload, timeout):
        calls.append((url, payload))
        return status, report
    return BrowserBridge(ENDPOINT, TOKEN, SITES, transport=transport), calls

class BrowserBridgeTests(unittest.TestCase):
    def test_positive_dom_text_proof(self):
        bridge, calls = make({"status":"PASS","proofLevel":"BROWSER_EXECUTION_ONLY",
                              "steps":[{"action":"assertText","status":"PASS","matched":True}]})
        out = bridge.run(BrowserMission("https://example.com/page","text-proof","#state","Chromium OK"))
        self.assertEqual((out.result.status, out.result.actions_executed), ("PASS",1))
        self.assertEqual(calls[0][1]["goal"], "text-proof")
        self.assertTrue(out.proof["dom_assertion"])

    def test_positive_audit_proof(self):
        bridge, _ = make({"status":"PASS","proofLevel":"BROWSER_EXECUTION_ONLY",
                          "steps":[{"action":"audit","status":"PASS",
                                    "findings":{"title":"ASTRA test","h1Count":1}}]})
        out=bridge.run(BrowserMission("https://example.com/page","seo-audit"))
        self.assertEqual((out.result.status, out.proof["h1_count"]),("PASS",1))

    def test_healthz_is_not_allowed(self):
        with self.assertRaises(ValueError):
            BrowserBridge(ENDPOINT.replace("/v1/mission","/healthz"),TOKEN,SITES)

    def test_wrong_worker_host_blocked(self):
        with self.assertRaises(ValueError):
            BrowserBridge("https://evil.example.com/v1/mission",TOKEN,SITES)

    def test_wrong_site_blocked_before_http(self):
        bridge, calls = make({})
        with self.assertRaises(ValueError):
            bridge.run(BrowserMission("https://evil.example.net/","seo-audit"))
        self.assertEqual(calls,[])

    def test_http_and_credentials_blocked(self):
        bridge, calls = make({})
        for url in ("http://example.com/","https://user:pw@example.com/",
                    "https://example.com:444/","file:///etc/passwd"):
            with self.subTest(url=url),self.assertRaises(ValueError):
                bridge.run(BrowserMission(url,"seo-audit"))
        self.assertEqual(calls,[])

    def test_dangerous_missions_never_allowed(self):
        bridge, _ = make({})
        for goal in ("click","type","visual-proof","javascript"):
            with self.subTest(goal=goal),self.assertRaises(ValueError):
                bridge.run(BrowserMission("https://example.com/",goal))

    def test_unverified_server_response_not_pass(self):
        bad = (
            {"status":"UNVERIFIED"},
            {"status":"PASS","steps":[]},
            {"status":"PASS","proofLevel":"BROWSER_EXECUTION_ONLY",
             "steps":[{"action":"assertText","status":"PASS","matched":False}]},
            {"status":"PASS","proofLevel":"BROWSER_EXECUTION_ONLY",
             "steps":[{"action":"read","status":"PASS"}]},
        )
        for body in bad:
            with self.subTest(body=body):
                bridge,_=make(body)
                self.assertEqual(bridge.run(BrowserMission("https://example.com/",
                             "text-proof","h1","proof")).result.status,"FAIL")

    def test_http_403_429_404_502_never_pass(self):
        good={"status":"PASS","proofLevel":"BROWSER_EXECUTION_ONLY",
              "steps":[{"action":"audit","status":"PASS",
                        "findings":{"title":"x","h1Count":1}}]}
        for status in (403,429,404,502):
            bridge,_=make(good,status)
            self.assertEqual(bridge.run(BrowserMission("https://example.com/",
                         "seo-audit")).result.status,"FAIL")

    def test_transport_failure_fails_closed(self):
        def transport(*args):
            raise TimeoutError("do-not-leak-secret")
        bridge=BrowserBridge(ENDPOINT,TOKEN,SITES,transport=transport)
        out=bridge.run(BrowserMission("https://example.com/","seo-audit"))
        self.assertEqual(out.result.status,"FAIL")
        self.assertNotIn("do-not-leak",json.dumps(out.proof))

    def test_secret_not_logged(self):
        bridge,_=make({"status":"FAIL","reason":TOKEN})
        out=bridge.run(BrowserMission("https://example.com/","seo-audit"))
        self.assertNotIn(TOKEN,json.dumps({"result":out.result.__dict__,"proof":out.proof}))

    def test_explicit_token_required(self):
        with self.assertRaises(ValueError):
            BrowserBridge(ENDPOINT,"short",SITES)

    def test_shared_bridge_path_accepted(self):
        url="https://astra-free-workers-omega.dr-starck66.workers.dev/browser/v1/mission"
        self.assertEqual(BrowserBridge(url,TOKEN,SITES,transport=lambda *args:(403,{})).endpoint,url)

if __name__ == "__main__":
    unittest.main()
