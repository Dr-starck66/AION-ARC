"""Real local Chromium end-to-end acceptance test for the ASTRA Browser v0.2 contract.

Requires Python playwright + /usr/bin/chromium. Uses actual HTTP POST over 127.0.0.1
and a *real* Chromium DOM, but a local test-double service, NOT Cloudflare.
"""
from __future__ import annotations
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from playwright.sync_api import sync_playwright
import hashlib
import json
from astra_aion_engine.browser import BrowserBridge, BrowserMission

TOKEN="local-e2e-only-token-no-production-use-00000000"
WORKER_ENDPOINT="https://astra-cloud-browser-omega.dr-starck66.workers.dev/v1/mission"
EXPECTED_URL="https://example.com/astra-bridge-e2e"
BASE=Path(__file__).resolve().parents[1]
EVIDENCE=BASE/"reports"/"browser-real-chromium-e2e.json"
SCREENSHOT=BASE/"reports"/"browser-real-chromium-e2e.png"
HTML="""<!doctype html><html lang='fr'><head><meta charset='utf-8'>
<title>ASTRA AION Chromium E2E</title><meta name='description' content='Vrai DOM Chromium'>
<link rel='canonical' href='https://example.com/astra-bridge-e2e'></head>
<body><h1>ASTRA navigateur réel</h1><p id='state'>Initial</p>
<script>document.addEventListener('DOMContentLoaded', () => {
 document.querySelector('#state').textContent = 'ASTRA CHROMIUM EXECUTED';
 document.body.setAttribute('data-js-did-execute', 'true');
});</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def send(self, status, body):
        data=json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def do_POST(self):
        if self.path!="/v1/mission" or self.headers.get("Authorization")!="Bearer "+TOKEN:
            return self.send(403,{"status":"DENIED"})
        try:
            mission=json.loads(self.rfile.read(int(self.headers.get("Content-Length","0"))))
            if mission.get("url")!=EXPECTED_URL or mission.get("goal") not in ("text-proof","seo-audit"):
                return self.send(422,{"status":"FAIL","reason":"UNSUPPORTED_MISSION"})
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True,executable_path="/usr/bin/chromium",args=["--no-sandbox"])
                try:
                    page=browser.new_page()
                    # Container browser policy blocks local HTTP navigation.
                    # Injected HTML still runs in genuine Chromium and executes real JS.
                    page.set_content(HTML,wait_until="domcontentloaded")
                    page.wait_for_function("document.body.dataset.jsDidExecute === 'true'")
                    if mission["goal"]=="text-proof":
                        actual=page.locator(mission["selector"]).inner_text(timeout=2000)
                        if mission.get("contains") not in actual:
                            return self.send(502,{"status":"FAIL","proofLevel":"BROWSER_EXECUTION_ONLY",
                                                  "steps":[{"action":"assertText","status":"FAIL"}]})
                        steps=[{"action":"assertText","status":"PASS","matched":True}]
                    else:
                        steps=[{"action":"audit","status":"PASS",
                                "findings":{"title":page.title(),"h1Count":page.locator("h1").count()}}]
                    if not SCREENSHOT.exists():
                        SCREENSHOT.parent.mkdir(exist_ok=True,parents=True)
                        page.screenshot(path=str(SCREENSHOT),full_page=True)
                    return self.send(200,{"status":"PASS","proofLevel":"BROWSER_EXECUTION_ONLY",
                                          "version":"0.2.0-local-real-chromium","steps":steps,
                                          "initial":{"fixture":"injected_html_not_external_navigation"}})
                finally:
                    browser.close()
        except Exception as exc:
            return self.send(502,{"status":"FAIL","reason":type(exc).__name__})

def main():
    EVIDENCE.parent.mkdir(exist_ok=True,parents=True)
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    def transport(remote_endpoint,token,payload,timeout):
        assert remote_endpoint==WORKER_ENDPOINT
        req=Request(f"http://127.0.0.1:{server.server_port}/v1/mission",
                    data=json.dumps(payload).encode(),method="POST",
                    headers={"Content-Type":"application/json","Authorization":"Bearer "+token})
        try:
            with urlopen(req,timeout=timeout) as response:
                return response.status,json.loads(response.read())
        except HTTPError as exc:
            return exc.code,json.loads(exc.read())
    try:
        bridge=BrowserBridge(WORKER_ENDPOINT,TOKEN,frozenset({"example.com"}),transport=transport)
        positive=bridge.run(BrowserMission(EXPECTED_URL,"text-proof","#state","ASTRA CHROMIUM EXECUTED"))
        assert positive.result.status=="PASS",positive
        audit=bridge.run(BrowserMission(EXPECTED_URL,"seo-audit"))
        assert audit.result.status=="PASS" and audit.proof["title"]=="ASTRA AION Chromium E2E",audit
        negative=bridge.run(BrowserMission(EXPECTED_URL,"text-proof","#state","INTENTIONALLY ABSENT"))
        assert negative.result.status=="FAIL" and negative.http_status==502,negative
        proof={
            "at_utc":datetime.now(timezone.utc).isoformat(),
            "status":"PASS_LOCAL_REAL_CHROMIUM_E2E",
            "aion_engine_execution":True,
            "browser_runtime":"/usr/bin/chromium via Playwright",
            "existing_astra_browser_api_contract":"POST /v1/mission, text-proof and seo-audit",
            "endpoint_kind":"loopback_test_double_with_REAL_CHROMIUM",
            "fixture_kind":"injected_HTML_executed_by_real_browser",
            "cloudflare_worker_deployment":"UNVERIFIED",
            "remote_token":"NOT_AVAILABLE",
            "positive":{"aion_status":positive.result.status,"actions":positive.result.actions_executed,
                        "reason":positive.result.reason,"http_status":positive.http_status,"proof":positive.proof},
            "seo_audit":{"aion_status":audit.result.status,"http_status":audit.http_status,"proof":audit.proof},
            "negative_control":{"aion_status":negative.result.status,"http_status":negative.http_status},
            "screenshot":{"sha256":hashlib.sha256(SCREENSHOT.read_bytes()).hexdigest(),"bytes":SCREENSHOT.stat().st_size},
        }
        EVIDENCE.write_text(json.dumps(proof,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print(json.dumps(proof,ensure_ascii=False))
    finally:
        server.shutdown()
        thread.join(timeout=4)
        server.server_close()

if __name__=="__main__":
    main()
