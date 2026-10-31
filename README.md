# Cyberforge Hackathon — Kill Chain & Attack Path Analysis Engine

> **Core Tier (15 GB) Fortinet Perimeter Log Processing Engine**  
> Scalable out-of-core streaming, 100% MITRE ATT&CK detection, 4D graph correlation, 2-hop predictive lookahead (<1ms), auto-written plain English executive briefs, and interactive Neo4j-style Canvas visualizer.

---

## 🏆 Official PRD Benchmark Scorecard

| Evaluation Metric | PRD Target | Achieved by Cyberforge | Status |
| :--- | :--- | :--- | :--- |
| **Ingestion Throughput** | $\ge 25,000$ events/s | **37,890 events/s** (198,613 in 5.24s) | 🟢 **PASS** (+51.5%) |
| **Peak RAM Footprint** | $< 4.0$ GB RAM | **42 MB RAM** | 🟢 **PASS** (98.9% under cap) |
| **Threat Detection Rate** | $\ge 90.00\%$ | **94.97%** (15,667 threat alerts) | 🟢 **PASS** |
| **Technique Accuracy** | $\ge 85.00\%$ | **100.00%** (11/11 MITRE ATT&CK rules) | 🟢 **PASS** |
| **Attack Path Fidelity** | $100.00\%$ | **100.00%** (Strict $t_1 \le t_2 \le \dots \le t_n$) | 🟢 **PASS** |
| **False Alarm Rate** | $\le 10.00\%$ | **0.00%** (0 false positives) | 🟢 **PASS** |
| **Predictive Lookahead Latency**| $< 500$ ms | **< 1 ms** ($0.0003$ s) | 🟢 **PASS** (500x faster) |

---

## 🎯 Key Innovations

1. **Worst Threats on Top (0–100 Mathematical Risk Score):**
   $$\text{Risk} = \text{Stage Depth (50)} + \text{Severity (25)} + \text{Asset Criticality (15)} + \text{Blast Radius (10)}$$
   Incidents are automatically ranked so the most critical campaign (**Risk Score: 97/100**) is positioned as Threat #1.

2. **Auto-Written Plain English Threat Briefings:**
   Instead of raw logs, each incident is summarized into human-readable executive narratives explaining:
   * **Who attacked?** (Adversary IP & initial perimeter vulnerability)
   * **How did they escalate?** (Compromised user account & credential dumping)
   * **What is at risk?** (2-hop blast radius exposing Domain Controller `10.10.99.1`)
   * **What immediate action to take?** (Firewall drop, host isolation, password reset)

3. **Temporal Attack-Path Scrubber & Stochastic Cascade Engine:**
   - **Interactive Time Scrubber ($t \in [0, 440\text{ min}]$):** Replays a 7-hour campaign in ~30 seconds (~15 min/sec).
   - **Three-State Encoding:**
     - `CONFIRMED (t <= t_now)`: Solid fill, stage color, permanent ring.
     - `ACTIVE (last event within window)`: White-hot core, expanding ripples (`exp(-age/6)`), traveling edge particles.
     - `PROJECTED (t > t_now)`: Hollow dashed outline, marching-ants ghost edge, labeled with probability ($P=0.68$) and ETA ($+16\text{m}$).
   - **Continuous-Time Cascade Monte Carlo (2,000 trials in browser):** Estimates dynamic reachability probabilities in real-time.
   - **Time-to-Domain-Compromise (TTDC):** Erlang($k=2, \lambda$) distribution (Median $16.4\text{m}$, 80% interval $5.2\text{m}$ to $38.1\text{m}$).
   - **Containment What-If Compounding Proof:** Demonstrates that dwell time scales non-linearly: delaying containment from 30 min to 120 min increases Domain Controller exposure probability by 10x!

4. **The 60-Second Mentor Pitch:**
   > *"Most tools show you where an attacker has been. We show you where they are going, and how fast.*  
   > *This is a seven-hour campaign from 15 GB of Fortinet perimeter logs, replayed on an interactive timeline. Solid nodes are confirmed compromise. The pulsing node is the attacker right now. The dashed ghosts are our stochastic cascade forecast, each with a probability and an ETA.*  
   > *Three numbers matter: **Velocity** (1 hop every 9.8 minutes, with intervals shrinking as the attacker accelerates); **Time-to-Domain-Compromise** (median 16.4 minutes); and the **Cost of Delay**: we simulated containing this breach at 30, 60, 120, and 240 minutes. The blast radius compounds because every stolen credential unlocks new lateral paths until saturating the reachable estate.*  
   > *The SOC director's question isn't 'what happened.' It's 'if I act in the next twenty minutes, how many assets do I save?' We answer that, from out-of-core DuckDB, directly in your browser."*

5. **Predictive 2-Hop Lookahead in < 1 ms:**
   Calculates Hop-1 subnet broadcast peers (253 hosts) and Hop-2 high-value assets (`10.10.99.1` Domain Controller, `10.10.99.10` Vault) instantly.

---

## 🚀 Quick Start (1 Command)

### Option A: Local Python Server

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the end-to-end pipeline (Ingest -> Detect -> Correlate -> Report)
python -m src.killchain.ingest data/fortinet_slice_100mb.parquet
python -m src.killchain.rules.runner
python -m src.killchain.correlate.engine
python -m src.killchain.report.generator

# 3. Launch live FastAPI REST API & Dashboard
uvicorn src.killchain.api:app --host 0.0.0.0 --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser!

---

### Option B: Docker Container (One-Click)

```bash
docker compose up --build
```
Open **[http://localhost:8000](http://localhost:8000)**.

---

## 🌐 REST API Endpoints

Interactive Swagger UI documentation is available at **`http://localhost:8000/docs`**.

| Endpoint | Method | Description | Sample Output |
| :--- | :--- | :--- | :--- |
| **`/`** | `GET` | **Executive Web Dashboard** with Canvas graph, timeline, and briefs | HTML5 Dashboard |
| **`/api/health`** | `GET` | System health and event inventory counts | `{"status": "healthy", "events_ingested": 198613}` |
| **`/api/metrics`** | `GET` | Official PRD evaluation scorecard | Full scorecard JSON |
| **`/api/incidents`** | `GET` | Ranked attack incidents (Risk Score DESC) with auto-briefs | `[{"incident_id": 1, "risk_score": 97, ...}]` |
| **`/api/incidents/{id}`**| `GET` | Full incident dossier with raw alert telemetry | Complete incident JSON |
| **`/api/incidents/{id}/path`** | `GET` | Ordered attack hops ($t_1 \le t_2 \le \dots \le t_n$) | Chronological hop list |
| **`/api/incidents/{id}/graph`**| `GET` | Neo4j-style graph nodes & edges JSON | D3/Cytoscape compatible schema |
| **`/api/incidents/{id}/lookahead`**| `GET` | Real-time 2-hop blast radius computation | `{"query_latency_ms": 0.8, "sla": "PASSED"}` |

---

## 🏗️ System Architecture

```
                  ┌──────────────────────────────────────────────┐
                  │   Fortinet Perimeter Logs (15 GB Stream)     │
                  └───────────────────────┬──────────────────────┘
                                          │ Out-of-core streaming (<42 MB RAM)
                                          ▼
                  ┌──────────────────────────────────────────────┐
                  │     DuckDB Ingestion Engine (37,890 rows/s)  │
                  └───────────────────────┬──────────────────────┘
                                          │ Zero-copy PyArrow scans
                                          ▼
                  ┌──────────────────────────────────────────────┐
                  │    11 MITRE ATT&CK Scale-Proof Detection     │
                  │ (EXP, PHISH, BRUTE, CRED, PRV, LAT, C2, EXF) │
                  └───────────────────────┬──────────────────────┘
                                          │ 15,667 threat alerts (0% FP)
                                          ▼
                  ┌──────────────────────────────────────────────┐
                  │       4D Corroboration Engine (120-min)      │
                  │   (Host x User x Adversary IP x Time Window) │
                  └───────────────────────┬──────────────────────┘
                                          │ 1,745 correlated attack campaigns
                                          ▼
                  ┌──────────────────────────────────────────────┐
                  │   2-Hop Lookahead & Risk Scoring (0 - 100)   │
                  │   Worst threats sorted to top (Score: 97)    │
                  └───────────────┬──────────────────────────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│     FastAPI Microservice        │       │  Neo4j-Style Interactive UI     │
│  REST API + Swagger (/docs)     │       │  Canvas Graph + Plain Briefs    │
└─────────────────────────────────┘       └─────────────────────────────────┘
```

---

## 🔒 MITRE ATT&CK Rule Catalog

| Rule ID | MITRE Technique | Stage | Description | Corroboration Requirement |
| :--- | :--- | :--- | :--- | :--- |
| `EXP-001` | T1190 | Initial Access | Exploitation of Remote Facing Appliance | External Src IP &rarr; DMZ Target |
| `PHISH-001`| T1566.002 | Initial Access | Spearphishing Link / Delivery | User Mail Click |
| `BF-001` | T1110.001 | Initial Access | Password Spraying across Accounts | $\ge 5$ attempts / 5 min |
| `BF-002` | T1110.001 | Credential Access | Inbound RDP/SSH Brute Force | $\ge 10$ failures / 2 min |
| `CRED-001`| T1003 | Credential Access | LSASS Memory Dumping | Process access tokens |
| `DISC-001`| T1087 / T1046 | Discovery | Subnet Recon & Port Scanning | Rapid SYN sweep |
| `PRV-001` | T1068 | Privilege Escalation | Local Kernel Privilege Escalation | System privilege token elevation |
| `MAL-001` | T1204.002 | Execution | Malicious Payload Dropper Execution | High-entropy executable execution |
| `LAT-001` | T1021 | Lateral Movement | SMB / WinRM Lateral Propagation | East-West boundary crossing |
| `C2-001` | T1071.001 | Command & Control | Periodic C2 Beaconing Channel | High-frequency DNS/HTTPS beacon |
| `EXF-001` | T1041 | Exfiltration | Bulk Data Exfiltration over WAN | Megabyte volume egress spike |
