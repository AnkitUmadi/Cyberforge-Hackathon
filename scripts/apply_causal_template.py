import sys
import os

TEMPLATE_PATH = "templates/incident_report.j2"

def main():
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    # 1. Ensure /causal_replay_bundle.js is in <head>
    if "/causal_replay_bundle.js" not in text:
        text = text.replace("<head>", "<head>\n    <script src=\"/causal_replay_bundle.js\"></script>")

    # 2. Insert HUD CSS before </style>
    hud_css = """
        /* Causal Replay HUD Overlays */
        .hud-card-inc {
            position: absolute;
            background: rgba(15, 23, 42, 0.90);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(51, 65, 85, 0.6);
            border-radius: 6px;
            padding: 8px 12px;
            font-family: 'JetBrains Mono', monospace, -apple-system;
            pointer-events: none;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            z-index: 15;
        }

        .hud-top-left-inc {
            top: 48px;
            left: 12px;
            display: flex;
            flex-direction: column;
            gap: 4px;
            min-width: 190px;
        }

        .hud-top-right-inc {
            top: 12px;
            right: 12px;
            text-align: right;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .hud-stat-row {
            display: flex;
            justify-content: space-between;
            font-size: 10.5px;
            gap: 8px;
        }

        .hud-clock-inc {
            font-size: 18px;
            font-weight: 700;
            color: #38bdf8;
            letter-spacing: -0.01em;
        }

        /* Floating Forensic Briefing Card */
        .hud-briefing-card-inc {
            position: absolute;
            bottom: 50px;
            right: 14px;
            max-width: 340px;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(14px);
            border: 1px solid rgba(56, 189, 248, 0.45);
            border-left: 4px solid #38bdf8;
            border-radius: 8px;
            padding: 12px 14px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
            z-index: 20;
            font-family: 'Inter', -apple-system, sans-serif;
            pointer-events: auto;
            transition: all 0.2s ease;
        }

        .brief-badge {
            font-size: 9.5px;
            font-weight: 700;
            background: rgba(244, 63, 94, 0.2);
            color: #f43f5e;
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid rgba(244, 63, 94, 0.4);
            font-family: monospace;
        }

        .speed-btn-group {
            display: inline-flex;
            gap: 4px;
            align-items: center;
        }

        .btn-speed {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid #334155;
            color: #94a3b8;
            font-family: monospace;
            font-size: 11px;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.15s;
        }

        .btn-speed:hover {
            color: #fff;
            background: rgba(255, 255, 255, 0.08);
        }

        .btn-speed.active {
            background: rgba(56, 189, 248, 0.25);
            border-color: #38bdf8;
            color: #38bdf8;
            font-weight: 700;
        }
    """
    if ".hud-card-inc" not in text:
        text = text.replace("</style>", hud_css + "\n    </style>")

    # 3. Replace Scrubber & Canvas Container HTML
    scrubber_marker = "<!-- TEMPORAL PLAYBACK SCRUBBER -->"
    whatif_marker = "<!-- CONTAINMENT WHAT-IF PROOF CURVE (DWELL TIME IMPACT) -->"

    new_graph_html = """<!-- TEMPORAL PLAYBACK SCRUBBER -->
        <div class="scrubber-panel">
            <div class="scrubber-top">
                <div class="scrubber-controls">
                    <button class="btn-scrub" id="btn-play-{{ inc.incident_id }}" onclick="togglePlay('{{ inc.incident_id }}')">
                        ▶ Play Campaign
                    </button>
                    <button class="btn-scrub" onclick="resetScrubber('{{ inc.incident_id }}')">
                        ↺ Reset
                    </button>
                    <!-- Presenter Milestone Hop Stepper -->
                    <button class="btn-scrub" onclick="stepPrevHop('{{ inc.incident_id }}')" title="Previous Critical Hop (Left Arrow)">
                        ⏮ Prev Hop
                    </button>
                    <button class="btn-scrub" onclick="stepNextHop('{{ inc.incident_id }}')" title="Next Critical Hop (Right Arrow)">
                        Next Hop ⏭
                    </button>
                    <button class="btn-scrub" id="btn-pacing-{{ inc.incident_id }}" onclick="toggleAdaptivePacing('{{ inc.incident_id }}')" style="border-color: rgba(56, 189, 248, 0.4); color: #38bdf8;">
                        ⚡ Adaptive Decel: ON
                    </button>
                    <div class="speed-btn-group">
                        <button class="btn-speed btn-speed-15-{{ inc.incident_id }}" onclick="setSpeed('{{ inc.incident_id }}', 15)">15x</button>
                        <button class="btn-speed btn-speed-30-{{ inc.incident_id }} active" onclick="setSpeed('{{ inc.incident_id }}', 30)">30x</button>
                        <button class="btn-speed btn-speed-60-{{ inc.incident_id }}" onclick="setSpeed('{{ inc.incident_id }}', 60)">60x</button>
                    </div>
                    <span style="font-size: 0.8rem; color: #94a3b8; font-family: monospace;" id="scrub-status-{{ inc.incident_id }}">
                        Time: <strong>0 min</strong> / {{ inc.duration_minutes }} min
                    </span>
                </div>
                <div style="font-size: 0.75rem; color: #38bdf8; font-family: monospace;">
                    Engine: <span style="color: #38bdf8;">Deterministic Closed-Form</span> &bull; <span style="color: #ef4444;">No Physics Drift</span> &bull; <span style="color: #f59e0b;">Heterogeneous Subnets</span>
                </div>
            </div>
            <input type="range" class="scrubber-slider" id="scrubber-{{ inc.incident_id }}"
                   min="0" max="{{ inc.duration_minutes }}" step="1" value="0"
                   oninput="onScrubInput('{{ inc.incident_id }}', this.value)">
        </div>
        {% endif %}

        <!-- VISUAL 1: ATTACK PATH AS A CAUSAL TERRITORIAL REPLAY GRAPH -->
        <div class="section-title">
            <span>🛡️</span> 1. Causal Territorial Attack Graph & Replay Engine (Deterministic Closed-Form $O(1)$)
        </div>
        <div class="neo4j-graph-wrapper">
            <div class="canvas-container" id="canvas-box-{{ inc.incident_id }}">
                <div class="graph-legend">
                    <div class="legend-item"><div class="legend-dot" style="background: #ef4444;"></div>Attacker / Ingress</div>
                    <div class="legend-item"><div class="legend-dot" style="background: #06b6d4;"></div>Compromised Host</div>
                    <div class="legend-item"><div class="legend-dot" style="background: #f59e0b;"></div>Compromised User</div>
                    <div class="legend-item"><div class="legend-dot" style="background: #a855f7;"></div>C2 / Exfil</div>
                    <div class="legend-item"><div class="legend-dot" style="background: #64748b;"></div>Hop-1 Peer</div>
                    <div class="legend-item"><div class="legend-dot" style="background: #f43f5e; border: 2px dashed #fca5a5;"></div>Tier-0 Domain Controller</div>
                </div>

                <!-- HUD Top-Left Overlay -->
                <div id="hud-top-left-{{ inc.incident_id }}" class="hud-card-inc hud-top-left-inc">
                    <div class="hud-stat-row">
                        <span style="color: #64748b;">ESTATE NODES</span>
                        <span style="color: #f8fafc; font-weight:600;" id="hud-nodes-{{ inc.incident_id }}">0 / 0</span>
                    </div>
                    <div class="hud-stat-row">
                        <span style="color: #64748b;">ACTIVE VPCs</span>
                        <span style="color: #f8fafc; font-weight:600;" id="hud-clusters-{{ inc.incident_id }}">0</span>
                    </div>
                    <div class="hud-stat-row">
                        <span style="color: #64748b;">CAMERA ZOOM</span>
                        <span style="color: #38bdf8; font-weight:600;" id="hud-zoom-{{ inc.incident_id }}">1.00x</span>
                    </div>
                    <div class="hud-stat-row">
                        <span style="color: #64748b;">WARP RATIO</span>
                        <span style="color: #f59e0b; font-weight:600;" id="hud-warp-{{ inc.incident_id }}">30.0x</span>
                    </div>
                </div>

                <!-- HUD Top-Right Overlay -->
                <div id="hud-top-right-{{ inc.incident_id }}" class="hud-card-inc hud-top-right-inc">
                    <div class="hud-clock-inc" id="hud-clock-{{ inc.incident_id }}">T+00h 00m</div>
                    <div style="font-size: 9.5px; color: #64748b;" id="hud-status-{{ inc.incident_id }}">ADAPTIVE CAUSAL REPLAY</div>
                </div>

                <!-- Live Forensic Briefing Card (Milestone Telemetry) -->
                <div id="hud-briefing-{{ inc.incident_id }}" class="hud-briefing-card-inc" style="display: none;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                        <span id="brief-badge-{{ inc.incident_id }}" class="brief-badge">HOP 1 / 5</span>
                        <span id="brief-dwell-{{ inc.incident_id }}" style="font-size: 10px; color: #94a3b8; font-family: monospace;">+45m dwell</span>
                    </div>
                    <div id="brief-headline-{{ inc.incident_id }}" style="font-size: 12.5px; font-weight: 700; color: #fff; margin-bottom: 3px;">Tier-0 Asset Compromised</div>
                    <div style="font-size: 10.5px; color: #38bdf8; font-family: monospace; margin-bottom: 6px;" id="brief-lineage-{{ inc.incident_id }}">10.10.1.5 → 10.10.99.1</div>
                    <div style="font-size: 11px; color: #cbd5e1; line-height: 1.4; border-top: 1px solid rgba(51, 65, 85, 0.6); padding-top: 5px;" id="brief-talking-point-{{ inc.incident_id }}">
                        Adversary exploited lateral credentials to breach crown jewels.
                    </div>
                </div>

                <canvas id="graph-canvas-{{ inc.incident_id }}"></canvas>

                <div class="graph-controls">
                    <button class="btn-graph" onclick="zoomGraph('{{ inc.incident_id }}', 1.25)">🔍 Zoom In</button>
                    <button class="btn-graph" onclick="zoomGraph('{{ inc.incident_id }}', 0.8)">🔍 Zoom Out</button>
                    <button class="btn-graph" onclick="resetGraphView('{{ inc.incident_id }}')">⤢ Fit Graph</button>
                </div>
            </div>

            <!-- Side Inspector -->
            <div class="node-inspector" id="inspector-{{ inc.incident_id }}">
                <div class="inspector-title"><span>🔍</span> Entity Inspector</div>
                <div style="font-size: 0.8rem; color: var(--text-muted);" id="inspector-hint-{{ inc.incident_id }}">
                    Click any node or connection edge in the graph to inspect forensic telemetry and exposure details.
                </div>
                <div id="inspector-content-{{ inc.incident_id }}" style="display: none;"></div>
            </div>
        </div>

        """

    p1 = text.find(scrubber_marker)
    p2 = text.find(whatif_marker)
    if p1 != -1 and p2 != -1:
        text = text[:p1] + new_graph_html + text[p2:]
        print("Scrubber and graph HTML replaced successfully.")
    else:
        print("ERROR: markers not found", p1, p2)
        sys.exit(1)

    # 4. Replace Javascript section
    script_marker = "<!-- Standalone Force-Directed Graph Engine Script -->"
    p3 = text.find(script_marker)
    if p3 == -1:
        script_marker = "<!-- Causal Territorial Replay Engine Script -->"
        p3 = text.find(script_marker)
    if p3 == -1:
        print("ERROR: script marker not found")
        sys.exit(1)

    new_script_html = """<!-- Causal Territorial Replay Engine Script -->
    <script>
        window.GRAPH_INSTANCES = {};
        const GRAPH_INSTANCES = window.GRAPH_INSTANCES;
        const INCIDENTS_DATA = {{ incidents_json | safe }};

        class InteractiveTemporalGraph {
            constructor(canvasId, incidentData) {
                this.canvas = document.getElementById(canvasId);
                if (!this.canvas) return;
                this.ctx = this.canvas.getContext('2d');
                this.data = incidentData;
                this.incId = incidentData.incident_id;
                this.temporal = incidentData.temporal || {};
                this.totalDuration = Math.max(60, incidentData.duration_minutes || 440);

                // Replay pacing: default fast pace 30 campaign min/sec (400m in ~13s)
                this.speed = 30.0;
                this.isPlaying = false;
                this.tNow = 0;
                this.isAdaptivePacing = true;
                this.lastTimestamp = performance.now();

                // Mouse interaction state
                this.isDragging = false;
                this.lastMouseX = 0;
                this.lastMouseY = 0;

                // DOM elements
                this.hudNodes = document.getElementById('hud-nodes-' + this.incId);
                this.hudClusters = document.getElementById('hud-clusters-' + this.incId);
                this.hudZoom = document.getElementById('hud-zoom-' + this.incId);
                this.hudWarp = document.getElementById('hud-warp-' + this.incId);
                this.hudClock = document.getElementById('hud-clock-' + this.incId);
                this.hudStatus = document.getElementById('hud-status-' + this.incId);
                this.scrubber = document.getElementById('scrubber-' + this.incId);
                this.scrubStatus = document.getElementById('scrub-status-' + this.incId);
                this.btnPlay = document.getElementById('btn-play-' + this.incId);
                this.btnPacing = document.getElementById('btn-pacing-' + this.incId);

                // Briefing Card elements
                this.hudBriefing = document.getElementById('hud-briefing-' + this.incId);
                this.briefBadge = document.getElementById('brief-badge-' + this.incId);
                this.briefDwell = document.getElementById('brief-dwell-' + this.incId);
                this.briefHeadline = document.getElementById('brief-headline-' + this.incId);
                this.briefLineage = document.getElementById('brief-lineage-' + this.incId);
                this.briefTalkingPoint = document.getElementById('brief-talking-point-' + this.incId);

                // Initialize Causal Engine
                this.initEngine();
                this.initCanvasSize();
                this.bindInteractions();

                // Auto-start animation loop
                this.animate = this.animate.bind(this);
                requestAnimationFrame(this.animate);
            }

            initEngine() {
                this.engine = new CausalReplay.CausalTerritorialEngine({
                    seed: 42
                });

                const nodes = this.temporal.nodes || [];
                const firstComp = this.temporal.firstCompromise || {};
                const hops = this.data.timeline_hops || [];

                const hopMap = new Map();
                hops.forEach(h => {
                    if (h.dest_ip) hopMap.set(h.dest_ip, h);
                });

                // Generate structured briefing cards from real timeline hops
                const customBriefings = hops.map((h, idx) => {
                    const tVal = h.t_min !== undefined ? h.t_min : idx * 15;
                    const prevT = idx > 0 ? (hops[idx - 1].t_min || 0) : 0;
                    const dwell = idx === 0 ? "Perimeter Ingress" : `+${Math.max(1, Math.round(tVal - prevT))}m dwell`;
                    const isCrown = (h.dest_ip && h.dest_ip.includes('99.')) || (h.stage && h.stage.includes('Impact'));

                    return {
                        hopIndex: idx + 1,
                        totalCriticalHops: hops.length,
                        eventId: `ev_${h.dest_ip || idx}`,
                        timestampFormatted: `T+${Math.floor(tVal / 60)}h ${Math.floor(tVal % 60)}m`,
                        dwellSincePreviousHop: dwell,
                        headline: `${h.stage || 'Lateral Movement'}: ${h.tech_name || 'Exploitation'}`,
                        mitreBadge: {
                            tactic: h.stage || 'LATERAL_MOVEMENT',
                            techniqueId: h.tech_id || 'T1021.002',
                            techniqueName: h.tech_name || 'Lateral Hop'
                        },
                        causalLineage: {
                            sourceHostname: h.src_ip || 'Gateway',
                            sourceIp: h.src_ip || '198.51.100.23',
                            targetHostname: h.dest_ip || 'TargetHost',
                            targetIp: h.dest_ip || '10.10.1.5',
                            compromisedCredential: isCrown ? 'DomainAdmin' : 'LocalAdmin'
                        },
                        blastRadiusStats: {
                            downstreamNodesExposed: isCrown ? 250 : 8,
                            cascadeRatePerMin: isCrown ? 4.5 : 1.8
                        },
                        presenterTalkingPoints: [
                            h.evidence || `Attacker executed ${h.tech_name} (${h.tech_id}) from ${h.src_ip} into ${h.dest_ip}.`,
                            isCrown ? "CRITICAL: Tier-0 Domain Controller reachable - immediate forest isolation required." : "Lateral spread across subnet boundary.",
                            "Containment: Revoke authentication tickets and quarantine host interface."
                        ]
                    };
                });

                // Build NodeEvent objects for CausalTerritorialEngine
                const events = nodes.map(n => {
                    const t = (firstComp[n.id] !== undefined) ? firstComp[n.id] : (n.t !== undefined ? n.t : 0);
                    const hop = hopMap.get(n.id);

                    let parent = null;
                    if (hop && hop.src_ip && hop.src_ip !== n.id) {
                        parent = hop.src_ip;
                    } else if (n.parent) {
                        parent = n.parent;
                    } else if (n.id !== this.data.adversary_ip && nodes.length > 0) {
                        parent = this.data.adversary_ip || nodes[0].id;
                    }

                    return {
                        id: n.id,
                        cluster: n.subnet || (n.type === 'WAN' ? 'WAN' : (n.type === 'DC' ? '10.10.99.0/24' : '10.10.1.0/24')),
                        parent: parent,
                        t: t,
                        criticality: n.criticality || (n.type === 'DC' ? 1.0 : (n.type === 'HOST' ? 0.75 : 0.4)),
                        type: n.type,
                        label: n.label || n.id,
                        mitreTactic: hop ? hop.stage : undefined,
                        mitreTechId: hop ? hop.tech_id : undefined,
                        mitreTechName: hop ? hop.tech_name : undefined,
                        evidence: hop ? hop.evidence : undefined
                    };
                });

                this.engine.ingest(events, customBriefings);
                this.tNow = 0;
            }

            initCanvasSize() {
                const rect = this.canvas.getBoundingClientRect();
                const dpr = window.devicePixelRatio || 1;
                this.canvas.width = Math.round(rect.width * dpr);
                this.canvas.height = Math.round(rect.height * dpr);
            }

            bindInteractions() {
                this.canvas.addEventListener('mousedown', (e) => {
                    this.isDragging = true;
                    this.lastMouseX = e.clientX;
                    this.lastMouseY = e.clientY;
                });

                window.addEventListener('mousemove', (e) => {
                    if (this.isDragging && this.engine) {
                        const dx = e.clientX - this.lastMouseX;
                        const dy = e.clientY - this.lastMouseY;
                        this.lastMouseX = e.clientX;
                        this.lastMouseY = e.clientY;
                        const rect = this.canvas.getBoundingClientRect();
                        this.engine.pan(dx, dy, rect.width, rect.height, this.tNow);
                    }
                });

                window.addEventListener('mouseup', () => {
                    this.isDragging = false;
                });

                this.canvas.addEventListener('wheel', (e) => {
                    e.preventDefault();
                    if (!this.engine) return;
                    const factor = e.deltaY < 0 ? 1.15 : 0.87;
                    this.engine.zoom(factor);
                }, { passive: false });

                this.canvas.addEventListener('click', (e) => {
                    if (!this.engine) return;
                    const rect = this.canvas.getBoundingClientRect();
                    const sx = e.clientX - rect.left;
                    const sy = e.clientY - rect.top;
                    const node = this.engine.getNodeAt(sx, sy, rect.width, rect.height, this.tNow);
                    if (node) {
                        this.engine.selectedNodeId = node.id;
                        this.inspectEntity(node);
                    } else {
                        this.engine.selectedNodeId = null;
                    }
                });

                this.canvas.addEventListener('mousemove', (e) => {
                    if (this.isDragging || !this.engine) return;
                    const rect = this.canvas.getBoundingClientRect();
                    const sx = e.clientX - rect.left;
                    const sy = e.clientY - rect.top;
                    const node = this.engine.getNodeAt(sx, sy, rect.width, rect.height, this.tNow);
                    this.canvas.style.cursor = node ? 'pointer' : 'default';
                    this.engine.hoverNodeId = node ? node.id : null;
                });
            }

            inspectEntity(node) {
                const hint = document.getElementById('inspector-hint-' + this.incId);
                const content = document.getElementById('inspector-content-' + this.incId);
                if (hint) hint.style.display = 'none';
                if (!content) return;
                content.style.display = 'block';

                const arch = this.engine.subnetArchetypes.get(node.cluster) || 'WORKSTATION_POOL';
                const archNames = {
                    'PERIMETER_DMZ': 'Curvilinear Ribbon DMZ Fence',
                    'WORKSTATION_POOL': 'Anisotropic Forward Cone Scatter',
                    'SERVER_CLUSTER': 'Quantized Rack Blade Grid',
                    'CROWN_JEWELS_AD': 'Concentric Bastion Rings + Moat'
                };

                content.innerHTML = `
                    <div class="inspector-card" style="border-left: 3px solid ${node.type === 'DC' ? '#f43f5e' : (node.type === 'WAN' ? '#ef4444' : '#38bdf8')};">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <span style="font-weight: 800; font-size: 0.95rem; color: #fff;">${node.id}</span>
                            <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">${node.type || 'HOST'}</span>
                        </div>
                        <div style="font-size: 0.75rem; color: #94a3b8; font-family: monospace;">Subnet: ${node.cluster}</div>
                        <div style="font-size: 0.75rem; color: #cbd5e1; margin-top: 4px;">Morphology: <strong>${archNames[arch] || arch}</strong></div>
                    </div>
                    <div class="inspector-card">
                        <div style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase;">Temporal Telemetry</div>
                        <div style="margin-top: 4px; font-size: 0.82rem; color: #cbd5e1;">Compromise Time: <strong style="color: #38bdf8;">T+${Math.round(node.birthTime)}m</strong></div>
                        <div style="margin-top: 2px; font-size: 0.82rem; color: #cbd5e1;">Ingress In-Edge: <span style="font-family: monospace; color: #f59e0b;">${node.parent || 'Patient Zero (Perimeter)'}</span></div>
                        <div style="margin-top: 2px; font-size: 0.82rem; color: #cbd5e1;">Criticality Score: <strong style="color: ${node.criticality >= 0.75 ? '#ef4444' : '#10b981'};">${Math.round(node.criticality * 100)} / 100</strong></div>
                    </div>
                    ${node.mitreTechName ? `
                    <div class="inspector-card">
                        <div style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase;">MITRE ATT&CK Mapping</div>
                        <div style="margin-top: 4px; font-weight: 700; color: #f8fafc; font-size: 0.82rem;">${node.mitreTechName} <span style="color: #38bdf8;">(${node.mitreTechId})</span></div>
                        <div style="margin-top: 2px; font-size: 0.75rem; color: #94a3b8;">${node.mitreTactic || 'Lateral Movement'}</div>
                        ${node.evidence ? `<div style="margin-top: 4px; font-size: 0.73rem; color: #e2e8f0; font-family: monospace; background: rgba(0,0,0,0.3); padding: 4px; border-radius: 4px;">${node.evidence}</div>` : ''}
                    </div>` : ''}
                `;
            }

            animate(timestamp) {
                const dt = Math.min(0.1, (timestamp - this.lastTimestamp) / 1000);
                this.lastTimestamp = timestamp;

                if (this.isPlaying && this.engine) {
                    if (this.isAdaptivePacing && this.engine.playbackEngine) {
                        const tickRes = this.engine.playbackEngine.tick(dt * (this.speed / 5.0));
                        this.tNow = tickRes.currentSimTime;
                        if (this.hudWarp) {
                            this.hudWarp.innerText = `${(tickRes.instantaneousWarpRatio * (this.speed / 5.0)).toFixed(1)}x`;
                        }

                        if (tickRes.activeBriefing && this.hudBriefing) {
                            this.hudBriefing.style.display = 'block';
                            if (this.briefBadge) this.briefBadge.innerText = `HOP ${tickRes.activeBriefing.hopIndex} / ${tickRes.activeBriefing.totalCriticalHops}`;
                            if (this.briefDwell) this.briefDwell.innerText = tickRes.activeBriefing.dwellSincePreviousHop;
                            if (this.briefHeadline) this.briefHeadline.innerText = tickRes.activeBriefing.headline;
                            if (this.briefLineage) this.briefLineage.innerText = `${tickRes.activeBriefing.causalLineage.sourceHostname} → ${tickRes.activeBriefing.causalLineage.targetHostname}`;
                            if (this.briefTalkingPoint) this.briefTalkingPoint.innerText = tickRes.activeBriefing.presenterTalkingPoints[0] || '';
                        } else if (this.hudBriefing) {
                            this.hudBriefing.style.display = 'none';
                        }
                    } else {
                        this.tNow += dt * this.speed;
                        if (this.hudWarp) this.hudWarp.innerText = `${this.speed.toFixed(0)}x (Fixed)`;
                        if (this.hudBriefing) this.hudBriefing.style.display = 'none';
                    }

                    if (this.tNow >= this.totalDuration) {
                        this.tNow = this.totalDuration;
                        this.isPlaying = false;
                        this.updatePlayState();
                    }

                    if (this.scrubber) {
                        this.scrubber.value = Math.round(this.tNow);
                    }
                }

                // Render Canvas
                const rect = this.canvas.getBoundingClientRect();
                const dpr = window.devicePixelRatio || 1;
                if (this.canvas.width !== Math.round(rect.width * dpr) || this.canvas.height !== Math.round(rect.height * dpr)) {
                    this.canvas.width = Math.round(rect.width * dpr);
                    this.canvas.height = Math.round(rect.height * dpr);
                }
                this.ctx.resetTransform();
                this.ctx.scale(dpr, dpr);

                if (this.engine) {
                    const snapshot = this.engine.render(this.ctx, this.tNow, rect.width, rect.height);

                    if (this.hudNodes) this.hudNodes.innerText = `${snapshot.totalActive} / ${snapshot.totalEstate}`;
                    if (this.hudClusters) this.hudClusters.innerText = `${this.engine.territoryEngine.clusters.size}`;
                    if (this.hudZoom) this.hudZoom.innerText = `${(snapshot.camera.zoom * this.engine.userZoom).toFixed(2)}x`;

                    const hrs = Math.floor(this.tNow / 60);
                    const mins = Math.floor(this.tNow % 60);
                    if (this.hudClock) this.hudClock.innerText = `T+${String(hrs).padStart(2, '0')}h ${String(mins).padStart(2, '0')}m`;
                    if (this.scrubStatus) {
                        this.scrubStatus.innerHTML = `Time: <strong>${Math.round(this.tNow)} min</strong> / ${this.totalDuration} min`;
                    }
                }

                requestAnimationFrame(this.animate);
            }

            togglePlay() {
                if (this.tNow >= this.totalDuration) {
                    this.tNow = 0;
                    if (this.engine && this.engine.playbackEngine) this.engine.playbackEngine.seekToSimTime(0);
                }
                this.isPlaying = !this.isPlaying;
                this.lastTimestamp = performance.now();
                this.updatePlayState();
            }

            reset() {
                this.tNow = 0;
                if (this.engine && this.engine.playbackEngine) this.engine.playbackEngine.seekToSimTime(0);
                this.isPlaying = true;
                this.lastTimestamp = performance.now();
                this.updatePlayState();
                if (this.scrubber) this.scrubber.value = 0;
            }

            seek(t) {
                this.tNow = Math.max(0, Math.min(this.totalDuration, t));
                if (this.engine && this.engine.playbackEngine) this.engine.playbackEngine.seekToSimTime(this.tNow);
                this.lastTimestamp = performance.now();
                if (this.scrubber) this.scrubber.value = Math.round(this.tNow);
            }

            stepNextHop() {
                if (!this.engine || !this.engine.playbackEngine) return;
                const res = this.engine.playbackEngine.stepToNextCriticalHop({ arrivalStyle: 'ANIMATE_IMPACT' });
                if (res) {
                    this.tNow = res.simTimeSetTo;
                    this.isPlaying = true;
                    this.updatePlayState();
                    if (this.scrubber) this.scrubber.value = Math.round(this.tNow);
                    if (res.briefingCard && this.hudBriefing) {
                        this.hudBriefing.style.display = 'block';
                        if (this.briefBadge) this.briefBadge.innerText = `HOP ${res.briefingCard.hopIndex} / ${res.briefingCard.totalCriticalHops}`;
                        if (this.briefDwell) this.briefDwell.innerText = res.briefingCard.dwellSincePreviousHop;
                        if (this.briefHeadline) this.briefHeadline.innerText = res.briefingCard.headline;
                        if (this.briefLineage) this.briefLineage.innerText = `${res.briefingCard.causalLineage.sourceHostname} → ${res.briefingCard.causalLineage.targetHostname}`;
                        if (this.briefTalkingPoint) this.briefTalkingPoint.innerText = res.briefingCard.presenterTalkingPoints[0] || '';
                    }
                }
            }

            stepPrevHop() {
                if (!this.engine || !this.engine.playbackEngine) return;
                const res = this.engine.playbackEngine.stepToPreviousCriticalHop({ arrivalStyle: 'SNAP_COMPLETE' });
                if (res) {
                    this.tNow = res.simTimeSetTo;
                    this.isPlaying = false;
                    this.updatePlayState();
                    if (this.scrubber) this.scrubber.value = Math.round(this.tNow);
                    if (res.briefingCard && this.hudBriefing) {
                        this.hudBriefing.style.display = 'block';
                        if (this.briefBadge) this.briefBadge.innerText = `HOP ${res.briefingCard.hopIndex} / ${res.briefingCard.totalCriticalHops}`;
                        if (this.briefDwell) this.briefDwell.innerText = res.briefingCard.dwellSincePreviousHop;
                        if (this.briefHeadline) this.briefHeadline.innerText = res.briefingCard.headline;
                        if (this.briefLineage) this.briefLineage.innerText = `${res.briefingCard.causalLineage.sourceHostname} → ${res.briefingCard.causalLineage.targetHostname}`;
                        if (this.briefTalkingPoint) this.briefTalkingPoint.innerText = res.briefingCard.presenterTalkingPoints[0] || '';
                    }
                }
            }

            toggleAdaptivePacing() {
                this.isAdaptivePacing = !this.isAdaptivePacing;
                if (this.btnPacing) {
                    this.btnPacing.innerText = this.isAdaptivePacing ? '⚡ Adaptive Decel: ON' : '⚡ Adaptive Decel: OFF';
                    this.btnPacing.style.color = this.isAdaptivePacing ? '#38bdf8' : '#94a3b8';
                }
            }

            setSpeed(speedVal) {
                this.speed = parseFloat(speedVal);
                document.querySelectorAll('.btn-speed-' + this.incId).forEach(btn => btn.classList.remove('active'));
                const cur = document.querySelector('.btn-speed-' + speedVal + '-' + this.incId);
                if (cur) cur.classList.add('active');
            }

            zoom(factor) {
                if (this.engine) this.engine.zoom(factor);
            }

            resetView() {
                if (this.engine) this.engine.resetView();
            }

            updatePlayState() {
                if (this.btnPlay) {
                    this.btnPlay.innerText = this.isPlaying ? '⏸ Pause Campaign' : '▶ Play Campaign';
                }
            }
        }

        // Global Action Proxies for HTML Button Handlers
        function togglePlay(incId) {
            const g = GRAPH_INSTANCES[incId];
            if (g) g.togglePlay();
        }

        function resetScrubber(incId) {
            const g = GRAPH_INSTANCES[incId];
            if (g) g.reset();
        }

        function stepNextHop(incId) {
            const g = GRAPH_INSTANCES[incId];
            if (g) g.stepNextHop();
        }

        function stepPrevHop(incId) {
            const g = GRAPH_INSTANCES[incId];
            if (g) g.stepPrevHop();
        }

        function toggleAdaptivePacing(incId) {
            const g = GRAPH_INSTANCES[incId];
            if (g) g.toggleAdaptivePacing();
        }

        function setSpeed(incId, speed) {
            const g = GRAPH_INSTANCES[incId];
            if (g) g.setSpeed(speed);
        }

        function onScrubInput(incId, val) {
            const g = GRAPH_INSTANCES[incId];
            if (g) g.seek(parseFloat(val));
        }

        function zoomGraph(incId, factor) {
            const g = GRAPH_INSTANCES[incId];
            if (g) g.zoom(factor);
        }

        function resetGraphView(incId) {
            const g = GRAPH_INSTANCES[incId];
            if (g) g.resetView();
        }

        function initAllGraphs() {
            if (Array.isArray(INCIDENTS_DATA)) {
                INCIDENTS_DATA.forEach(inc => {
                    const canvasId = 'graph-canvas-' + inc.incident_id;
                    const el = document.getElementById(canvasId);
                    if (el) {
                        GRAPH_INSTANCES[inc.incident_id] = new InteractiveTemporalGraph(canvasId, inc);
                    }
                });
            }
        }

        // Keyboard shortcuts for demo presentation
        window.addEventListener('keydown', (e) => {
            if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;
            const g = Object.values(GRAPH_INSTANCES)[0];
            if (!g) return;
            if (e.code === 'Space') {
                e.preventDefault();
                g.togglePlay();
            } else if (e.code === 'KeyR' || e.code === 'Home') {
                e.preventDefault();
                g.reset();
            } else if (e.code === 'ArrowRight') {
                e.preventDefault();
                g.stepNextHop();
            } else if (e.code === 'ArrowLeft') {
                e.preventDefault();
                g.stepPrevHop();
            }
        });

        window.initAllGraphs = initAllGraphs;
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initAllGraphs);
        } else {
            initAllGraphs();
        }
    </script>
</body>
</html>
"""

    text = text[:p3] + new_script_html

    with open(TEMPLATE_PATH, "w", encoding="utf-8") as f:
        f.write(text)

    print("Template updated successfully!")

if __name__ == "__main__":
    main()
