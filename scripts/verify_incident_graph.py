import subprocess
import time
import json
import urllib.request
import os

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT = 9222
USER_DATA = r"C:\Users\Ankit Umadi\Documents\hack\.chrome_test_profile"

def main():
    cmd = [
        CHROME,
        "--headless=new",
        f"--remote-debugging-port={PORT}",
        f"--user-data-dir={USER_DATA}",
        "--disable-gpu",
        "--no-sandbox",
        "http://localhost:8000/"
    ]
    proc = subprocess.Popen(cmd)
    time.sleep(2.5)

    try:
        # Get devtools targets
        with urllib.request.urlopen(f"http://localhost:{PORT}/json") as resp:
            targets = json.loads(resp.read().decode())
        print(f"Found {len(targets)} targets")
        page_target = next(t for t in targets if t.get("type") == "page")
        ws_url = page_target["webSocketDebuggerUrl"]
        print("WS URL:", ws_url)

        import websocket
        ws = websocket.create_connection(ws_url)

        # Helper to send CDP command
        req_id = [1]
        def cdp_send(method, params=None):
            rid = req_id[0]
            req_id[0] += 1
            msg = {"id": rid, "method": method, "params": params or {}}
            ws.send(json.dumps(msg))
            while True:
                res = json.loads(ws.recv())
                if res.get("id") == rid:
                    return res

        # Enable console and runtime
        cdp_send("Runtime.enable")
        cdp_send("Console.enable")

        # Let the page render frames
        time.sleep(2.0)

        # Evaluate window.GRAPH_INSTANCES and CausalReplay
        eval_res = cdp_send("Runtime.evaluate", {
            "expression": """
                ({
                    hasCausalReplay: typeof window.CausalReplay !== 'undefined',
                    instancesCount: Object.keys(window.GRAPH_INSTANCES || {}).length,
                    firstIncId: Object.keys(window.GRAPH_INSTANCES || {})[0],
                    firstInstanceEngine: !!(window.GRAPH_INSTANCES[Object.keys(window.GRAPH_INSTANCES || {})[0]]?.engine),
                    nodesCount: window.GRAPH_INSTANCES[Object.keys(window.GRAPH_INSTANCES || {})[0]]?.engine?.nodes?.length,
                    subnets: Array.from(window.GRAPH_INSTANCES[Object.keys(window.GRAPH_INSTANCES || {})[0]]?.engine?.subnetArchetypes?.entries() || []),
                    speed: window.GRAPH_INSTANCES[Object.keys(window.GRAPH_INSTANCES || {})[0]]?.speed
                })
            """,
            "returnByValue": True
        })
        print("CDP Eval Result:", json.dumps(eval_res.get("result", {}).get("value", {}), indent=2))

        # Test Stepper: stepNextHop on the first incident
        first_inc = eval_res.get("result", {}).get("value", {}).get("firstIncId")
        if first_inc:
            step_res = cdp_send("Runtime.evaluate", {
                "expression": f"""
                    const g = window.GRAPH_INSTANCES['{first_inc}'];
                    g.stepNextHop();
                    ({
                        tNow: g.tNow,
                        isPlaying: g.isPlaying,
                        briefingDisplay: document.getElementById('hud-briefing-' + '{first_inc}')?.style?.display,
                        briefingHeadline: document.getElementById('brief-headline-' + '{first_inc}')?.innerText
                    })
                """,
                "returnByValue": True
            })
            print("Step Next Hop Result:", json.dumps(step_res.get("result", {}).get("value", {}), indent=2))

        # Capture a screenshot of the incident graph viewport
        snap_res = cdp_send("Page.captureScreenshot", {"format": "png"})
        if "result" in snap_res and "data" in snap_res["result"]:
            import base64
            img_data = base64.b64decode(snap_res["result"]["data"])
            out_img = os.path.abspath("out/verified_incident_graph.png")
            with open(out_img, "wb") as f:
                f.write(img_data)
            print("Screenshot saved to:", out_img)

        ws.close()

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    main()
