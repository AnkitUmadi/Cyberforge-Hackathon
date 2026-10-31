import time
import urllib.request
import json
import subprocess
import sys

def main():
    print("Launching Uvicorn server in background...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.killchain.api:app", "--host", "127.0.0.1", "--port", "8008"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        # Wait 2 seconds for server to start
        time.sleep(2.5)
        
        base_url = "http://127.0.0.1:8008"
        
        # Test 1: Health
        with urllib.request.urlopen(f"{base_url}/api/health") as resp:
            data = json.loads(resp.read().decode())
            print(f"[PASS] /api/health -> {resp.status} - {data['status']}")
            
        # Test 2: Metrics
        with urllib.request.urlopen(f"{base_url}/api/metrics") as resp:
            data = json.loads(resp.read().decode())
            print(f"[PASS] /api/metrics -> {resp.status} - {len(data['scorecard'])} scorecard metrics")
            
        # Test 3: Incidents (ranked)
        with urllib.request.urlopen(f"{base_url}/api/incidents?limit=5") as resp:
            data = json.loads(resp.read().decode())
            scores = [inc['risk_score'] for inc in data['incidents']]
            print(f"[PASS] /api/incidents -> {resp.status} - Top 5 Risk Scores: {scores}")
            assert scores == sorted(scores, reverse=True), "Incidents must be ranked descending by risk score!"
            
        # Test 4: Incident Detail & Plain English Briefing
        with urllib.request.urlopen(f"{base_url}/api/incidents/1") as resp:
            data = json.loads(resp.read().decode())
            summary = data['plain_english_report']['summary']
            print(f"[PASS] /api/incidents/1 -> {resp.status} - Auto Narrative: \"{summary[:65]}...\"")
            
        # Test 5: Lookahead Blast Radius Latency
        with urllib.request.urlopen(f"{base_url}/api/incidents/1/lookahead") as resp:
            data = json.loads(resp.read().decode())
            print(f"[PASS] /api/incidents/1/lookahead -> {resp.status} - Latency: {data['query_latency_ms']} ms ({data['speedup_vs_target']})")

        # Test 6: Graph JSON
        with urllib.request.urlopen(f"{base_url}/api/incidents/1/graph") as resp:
            data = json.loads(resp.read().decode())
            print(f"[PASS] /api/incidents/1/graph -> {resp.status} - {len(data['nodes'])} nodes, {len(data['edges'])} edges")

        # Test 7: UI Dashboard
        with urllib.request.urlopen(f"{base_url}/") as resp:
            html = resp.read().decode()
            print(f"[PASS] / (Dashboard UI) -> {resp.status} - Content-Length: {len(html)} bytes")
            assert "Cyberforge - Executive Attack Path" in html
            assert "Executive Threat Briefing (Plain English)" in html
            
        print("\nAll 7 FastAPI HTTP Endpoints Verified Successfully!")
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    main()
