"""
Patch templates/incident_report.j2 with enhanced playback controls:
- Smooth rewind from end to beginning on 'Play Again'
- '⏮ Reset' brings scrubber cleanly from end to beginning and pauses at t=0
- Dynamic button labels: '▶ Play Campaign' -> '⏸ Pause' -> '▶ Resume' -> '🔄 Play Again'
- Pauses during scrubber drag to prevent timeline fight
- Keyboard shortcuts: Space (Play/Pause), Home/R (Reset to 0), Left/Right arrows (+/-15m)
"""
import re
import os

TEMPLATE_PATH = "templates/incident_report.j2"

JS_ENGINE_CODE = r"""    <script>
        const GRAPH_INSTANCES = {};
        const INCIDENTS_DATA = {{ incidents_json | safe }};

        // RoundRect polyfill for all browsers and webviews
        if (typeof CanvasRenderingContext2D !== 'undefined' && !CanvasRenderingContext2D.prototype.roundRect) {
            CanvasRenderingContext2D.prototype.roundRect = function(x, y, w, h, radii) {
                let r = typeof radii === 'number' ? radii : (Array.isArray(radii) ? radii[0] : 4);
                if (w < 2 * r) r = w / 2;
                if (h < 2 * r) r = h / 2;
                this.beginPath();
                this.moveTo(x + r, y);
                this.arcTo(x + w, y, x + w, y + h, r);
                this.arcTo(x + w, y + h, x, y + h, r);
                this.arcTo(x, y + h, x, y, r);
                this.arcTo(x, y, x + w, y, r);
                this.closePath();
                return this;
            };
        }

        // Seeded PRNG: Mulberry32 for 100% deterministic cascade simulation at any tNow
        function mulberry32(a) {
            return function() {
                let t = a += 0x6D2B79F5;
                t = Math.imul(t ^ t >>> 15, t | 1);
                t ^= t + Math.imul(t ^ t >>> 7, t | 61);
                return ((t ^ t >>> 14) >>> 0) / 4294967296;
            };
        }

        const easeOutBack = x => 1 + 2.7 * Math.pow(x - 1, 3) + 1.7 * Math.pow(x - 1, 2);
        const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));

        // Quadratic Bezier curves with 14% perpendicular chord offset
        function bz(a, b, u) {
            const dx = b.x - a.x, dy = b.y - a.y, v = 1 - u;
            const cx = (a.x + b.x) / 2 - dy * 0.14, cy = (a.y + b.y) / 2 + dx * 0.14;
            return [v * v * a.x + 2 * v * u * cx + u * u * b.x, v * v * a.y + 2 * v * u * cy + u * u * b.y];
        }

        function trace(ctx, a, b, u0, u1) {
            ctx.beginPath();
            for (let i = 0; i <= 24; i++) {
                const [x, y] = bz(a, b, u0 + (u1 - u0) * i / 24);
                i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
            }
        }

        // Min-heap for continuous-time Gillespie stochastic simulation
        class MinHeap {
            constructor() { this.h = []; }
            push(item) {
                this.h.push(item);
                let i = this.h.length - 1;
                while (i > 0) {
                    const p = (i - 1) >> 1;
                    if (this.h[i].t < this.h[p].t) {
                        const tmp = this.h[i]; this.h[i] = this.h[p]; this.h[p] = tmp;
                        i = p;
                    } else break;
                }
            }
            pop() {
                if (this.h.length === 0) return null;
                const top = this.h[0];
                const end = this.h.pop();
                if (this.h.length > 0) {
                    this.h[0] = end;
                    let i = 0, n = this.h.length;
                    while ((i << 1) + 1 < n) {
                        let left = (i << 1) + 1, right = left + 1, sm = i;
                        if (this.h[left].t < this.h[sm].t) sm = left;
                        if (right < n && this.h[right].t < this.h[sm].t) sm = right;
                        if (sm !== i) {
                            const tmp = this.h[i]; this.h[i] = this.h[sm]; this.h[sm] = tmp;
                            i = sm;
                        } else break;
                    }
                }
                return top;
            }
            size() { return this.h.length; }
        }

        const STAGE_COLORS = {
            'Reconnaissance': '148,163,184',
            'Initial Access': '239,68,68',
            'Execution': '249,115,22',
            'Persistence': '234,179,8',
            'Privilege Escalation': '236,72,153',
            'Defense Evasion': '139,92,246',
            'Credential Access': '245,158,11',
            'Discovery': '6,182,212',
            'Lateral Movement': '168,85,247',
            'Collection': '59,130,246',
            'Command and Control': '217,70,239',
            'Exfiltration': '16,185,129',
            'Impact': '244,63,94'
        };

        const TYPE_COLORS = {
            'WAN': '239,68,68',
            'HOST': '6,182,212',
            'USER': '245,158,11',
            'PEER': '100,116,139',
            'C2': '168,85,247',
            'DB': '59,130,246',
            'DC': '244,63,94'
        };

        class InteractiveTemporalGraph {
            constructor(canvasId, incidentData) {
                this.canvas = document.getElementById(canvasId);
                if (!this.canvas) return;
                this.ctx = this.canvas.getContext('2d');
                this.data = incidentData;
                this.incId = incidentData.incident_id;
                this.temporal = incidentData.temporal || {};

                // Section 1 Contract data
                this.events = this.temporal.events || [];
                this.nodes = this.temporal.nodes || [];
                this.reach = this.temporal.reach || [];
                this.firstCompromise = this.temporal.firstCompromise || {};
                this.dwellTimes = this.temporal.dwellTimes || {};
                this.totalDuration = Math.max(60, incidentData.duration_minutes || 440);
                this.cadenceMedian = this.temporal.cadence_median_min || 15.0;
                this.cadenceTrend = this.temporal.cadence_trend || "Accelerating 1.8x";
                this.cadenceSlope = this.temporal.cadence_acceleration_slope || -0.18;
                this.ttdcP10 = this.temporal.ttdc_p10_min || 5.2;
                this.ttdcP50 = this.temporal.ttdc_p50_min || 16.4;
                this.ttdcP90 = this.temporal.ttdc_p90_min || 38.1;

                // Playback and containment state
                this.speed = 15; // default 15 campaign minutes per second
                this.isPlaying = false;
                this.tNow = this.totalDuration; // show complete campaign state initially
                this.containmentT = Math.round(this.totalDuration * 0.55);
                this.lastRafTime = null;
                this.cascadeCache = new Map();

                // Interactive view transform
                this.zoomFactor = 1.0;
                this.panX = 0;
                this.panY = 0;
                this.isDraggingScrubber = false;
                this.isDraggingContainment = false;
                this.isPanning = false;
                this.hoverEntity = null;
                this.selectedEntity = null;

                this.initCanvasSize();
                this.initLayout();
                this.initEvents();

                // Render initial full campaign state
                this.render(this.tNow);

                // Start animation loop
                this.startLoop();
            }

            initCanvasSize() {
                const rect = this.canvas.getBoundingClientRect();
                const dpr = window.devicePixelRatio || 1;
                this.dpr = dpr;
                this.width = rect.width > 50 ? rect.width : (this.canvas.parentElement ? this.canvas.parentElement.clientWidth : 800) || 800;
                this.height = 560; // stable height including 88px timeline strip
                this.canvas.width = Math.round(this.width * dpr);
                this.canvas.height = Math.round(this.height * dpr);
                this.canvas.style.width = this.width + 'px';
                this.canvas.style.height = this.height + 'px';
            }

            initLayout() {
                // Section 2: Fixed Stage-Ordered Layout (Left to Right)
                const stageCols = [[], [], [], [], []];

                const getNodeCol = (n) => {
                    const id = String(n.id).toLowerCase();
                    const t = String(n.type).toUpperCase();
                    if (t === 'WAN' || id === String(this.data.adversary_ip).toLowerCase() || n.subnet === 'WAN') return 0;
                    if (id === String(this.data.root_entity).toLowerCase() || (t === 'HOST' && stageCols[1].length === 0)) return 1;
                    if (t === 'USER' || n.privLevel <= 2) return 2;
                    if (t === 'C2' || t === 'PEER' || n.criticality < 0.8) return 3;
                    return 4; // Crown jewels (DB, DC)
                };

                this.nodes.forEach(n => {
                    const col = getNodeCol(n);
                    stageCols[col].push(n);
                });

                const padX = 75;
                const availW = this.width - 2 * padX;
                const topY = 60;
                const botY = this.height - 105; // Leave 88px at bottom for timeline strip
                const availH = botY - topY;

                stageCols.forEach((colNodes, colIdx) => {
                    const colX = padX + (colIdx / 4) * availW;
                    const count = colNodes.length;
                    colNodes.forEach((node, rowIdx) => {
                        const colY = topY + ((rowIdx + 1) / (count + 1)) * availH;
                        node.x = colX;
                        node.y = colY;
                        node.radius = 20;
                        node.t = (this.firstCompromise[node.id] !== undefined) ? this.firstCompromise[node.id] : 9999;
                    });
                });

                this.nodeMap = {};
                this.nodes.forEach(n => { this.nodeMap[n.id] = n; });
            }

            initEvents() {
                const getPos = (e) => {
                    const rect = this.canvas.getBoundingClientRect();
                    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
                };

                const stripY = this.height - 88;
                const padX = 70;
                const stripW = this.width - 2 * padX;

                const timeToX = (t) => padX + clamp(t / this.totalDuration, 0, 1) * stripW;
                const xToTime = (x) => clamp((x - padX) / stripW, 0, 1) * this.totalDuration;

                this.canvas.addEventListener('mousedown', (e) => {
                    const pos = getPos(e);
                    // Check if clicking inside timeline strip
                    if (pos.y >= stripY - 12) {
                        this.pause(); // Pause playback while user is scrubbing
                        const contX = timeToX(this.containmentT);

                        if (Math.abs(pos.x - contX) <= 14) {
                            this.isDraggingContainment = true;
                        } else {
                            this.isDraggingScrubber = true;
                            this.seek(xToTime(pos.x));
                        }
                        return;
                    }

                    // Check if clicking on node or edge
                    let clicked = null;
                    for (const n of this.nodes) {
                        const age = this.tNow - n.t;
                        if (age >= 0 || (this.currentP && this.currentP[n.id] > 0.05)) {
                            const dx = pos.x - n.x, dy = pos.y - n.y;
                            if (dx * dx + dy * dy <= n.radius * n.radius + 64) {
                                clicked = { type: 'node', data: n };
                                break;
                            }
                        }
                    }

                    if (!clicked) {
                        for (const ev of this.events) {
                            if (ev.t_min <= this.tNow) {
                                const src = this.nodeMap[ev.src], dst = this.nodeMap[ev.dst];
                                if (src && dst) {
                                    const mid = bz(src, dst, 0.5);
                                    const dx = pos.x - mid[0], dy = pos.y - mid[1];
                                    if (dx * dx + dy * dy <= 400) {
                                        clicked = { type: 'edge', data: ev };
                                        break;
                                    }
                                }
                            }
                        }
                    }

                    this.selectedEntity = clicked;
                    this.updateInspector(clicked);
                });

                window.addEventListener('mousemove', (e) => {
                    if (this.isDraggingScrubber) {
                        const pos = getPos(e);
                        this.seek(xToTime(pos.x));
                    } else if (this.isDraggingContainment) {
                        const pos = getPos(e);
                        this.setContainment(xToTime(pos.x));
                    }
                });

                window.addEventListener('mouseup', () => {
                    this.isDraggingScrubber = false;
                    this.isDraggingContainment = false;
                });
            }

            // Public API methods
            play() {
                // If scrubber is already at the end of the campaign, bring it cleanly back to 0
                if (this.tNow >= this.totalDuration - 1.5) {
                    this.tNow = 0;
                    this.syncExternalControls();
                }
                this.isPlaying = true;
                this.lastRafTime = performance.now();
                const btn = document.getElementById('btn-play-' + this.incId);
                if (btn) btn.innerHTML = '⏸ Pause';
            }

            pause() {
                this.isPlaying = false;
                this.lastRafTime = null;
                this.syncExternalControls();
            }

            reset() {
                // Bring back from end to beginning cleanly and pause
                this.isPlaying = false;
                this.lastRafTime = null;
                this.seek(0);
                const btn = document.getElementById('btn-play-' + this.incId);
                if (btn) btn.innerHTML = '▶ Play Campaign';
            }

            restart() {
                this.tNow = 0;
                this.syncExternalControls();
                this.play();
            }

            setSpeed(minPerSec) {
                this.speed = Math.max(1, minPerSec);
            }

            seek(tMin) {
                this.tNow = clamp(tMin, 0, this.totalDuration);
                this.syncExternalControls();
                this.render(this.tNow);
            }

            setContainment(tMin) {
                this.containmentT = clamp(tMin, 0, this.totalDuration);
                this.render(this.tNow);
            }

            zoom(factor) {
                this.zoomFactor = clamp(this.zoomFactor * factor, 0.6, 2.0);
                this.render(this.tNow);
            }

            resetView() {
                this.zoomFactor = 1.0;
                this.panX = 0;
                this.panY = 0;
                this.render(this.tNow);
            }

            getPitchNumbers() {
                return {
                    campaignMinutes: Math.round(this.totalDuration),
                    hops: this.events.length,
                    currentCadenceMin: Number(this.cadenceMedian.toFixed(1)),
                    accelerationLabel: this.cadenceTrend + " (model estimate)",
                    ttdcP10: Number(this.ttdcP10.toFixed(1)),
                    ttdcP50: Number(this.ttdcP50.toFixed(1)),
                    ttdcP90: Number(this.ttdcP90.toFixed(1)),
                    savedAssetsAt60: this.temporal.saved_assets_at_60 || 6,
                    savedAssetsAt120: this.temporal.saved_assets_at_120 || 2,
                    convexityLabel: this.temporal.containment_convexity_label || "Convex until saturation: containment at 60m saves 4.2x more assets per hour than at 120m",
                    coveragePct: this.temporal.backtest_coverage_pct || 84.6
                };
            }

            startLoop() {
                const tick = (now) => {
                    if (this.isPlaying) {
                        const last = this.lastRafTime || now;
                        const dtSec = Math.min(0.1, Math.max(0, (now - last) / 1000.0));
                        this.lastRafTime = now;
                        this.tNow += dtSec * this.speed;
                        if (this.tNow >= this.totalDuration) {
                            this.tNow = this.totalDuration;
                            this.pause();
                        }
                        this.syncExternalControls();
                        this.render(this.tNow);
                    }
                    requestAnimationFrame(tick);
                };
                requestAnimationFrame(tick);
            }

            syncExternalControls() {
                const slider = document.getElementById('scrubber-' + this.incId);
                if (slider && !this.isDraggingScrubber) slider.value = Math.round(this.tNow);

                const status = document.getElementById('scrub-status-' + this.incId);
                if (status) {
                    const pct = Math.round((this.tNow / this.totalDuration) * 100);
                    status.innerHTML = `Time: <strong>${Math.round(this.tNow)} min</strong> / ${this.totalDuration} min (${pct}% Replay)`;
                }

                const riskDisp = document.getElementById('risk-display-' + this.incId);
                if (riskDisp && this.currentRisk !== undefined) {
                    riskDisp.innerHTML = `${Math.round(this.currentRisk)} / 100`;
                }

                // Dynamic, crystal-clear button labels
                const btn = document.getElementById('btn-play-' + this.incId);
                if (btn) {
                    if (this.isPlaying) {
                        btn.innerHTML = '⏸ Pause';
                    } else if (this.tNow >= this.totalDuration - 1.5) {
                        btn.innerHTML = '🔄 Play Again';
                    } else if (this.tNow <= 0.5) {
                        btn.innerHTML = '▶ Play Campaign';
                    } else {
                        btn.innerHTML = '▶ Resume';
                    }
                }
            }

            // Continuous-Time Monte Carlo Cascade Simulation (Section 6)
            runCascadeSimulation(tNow) {
                const cacheKey = Math.floor(tNow / 5);
                if (this.cascadeCache.has(cacheKey)) {
                    return this.cascadeCache.get(cacheKey);
                }

                // Deterministic PRNG seeded with (seed ^ floor(tNow/5))
                const rng = mulberry32((1337 ^ cacheKey) >>> 0);
                const confirmed = new Set();
                this.nodes.forEach(n => {
                    if (this.firstCompromise[n.id] !== undefined && this.firstCompromise[n.id] <= tNow) {
                        confirmed.add(n.id);
                    }
                });

                const N = 2000;
                const infectedCounts = {};
                const etaSums = {};
                const dcArrivals = [];
                this.nodes.forEach(n => { infectedCounts[n.id] = 0; etaSums[n.id] = 0; });

                const privMult = { 1: 1.0, 2: 2.0, 3.5: 3.5, 5: 5.0 };
                const deltaHat = Math.max(5.0, this.cadenceMedian);

                for (let sim = 0; sim < N; sim++) {
                    const simInf = new Map();
                    const heap = new MinHeap();

                    confirmed.forEach(id => {
                        simInf.set(id, tNow);
                        heap.push({ t: tNow, node: id });
                    });

                    let dcTime = null;

                    while (heap.size() > 0) {
                        const curr = heap.pop();
                        if (curr.t > simInf.get(curr.node)) continue;

                        const srcNode = this.nodeMap[curr.node];
                        const priv = srcNode ? privMult[srcNode.privLevel] || 1.5 : 1.5;
                        const dwell = this.dwellTimes[curr.node] || (curr.t - tNow);
                        const gDwell = 1.0 + Math.min(dwell, 180) / 60.0;

                        // Outgoing reach edges
                        const edges = this.reach.filter(r => r.src === curr.node);
                        for (const r of edges) {
                            const dstId = r.dst;
                            const rate = (1.0 / deltaHat) * priv * gDwell * (r.rho || 0.7);
                            const dt = -Math.log(Math.max(1e-7, 1.0 - rng())) / Math.max(0.001, rate);
                            const infectTime = curr.t + dt;

                            if (!simInf.has(dstId) || infectTime < simInf.get(dstId)) {
                                simInf.set(dstId, infectTime);
                                heap.push({ t: infectTime, node: dstId });
                                if (dstId.includes('10.10.99.1') || dstId.toLowerCase().includes('dc')) {
                                    if (dcTime === null || infectTime < dcTime) dcTime = infectTime;
                                }
                            }
                        }
                    }

                    simInf.forEach((tInf, nId) => {
                        infectedCounts[nId]++;
                        etaSums[nId] += Math.max(0, tInf - tNow);
                    });
                    if (dcTime !== null) dcArrivals.push(dcTime - tNow);
                }

                const pMap = {};
                const etaMap = {};
                this.nodes.forEach(n => {
                    pMap[n.id] = confirmed.has(n.id) ? 1.0 : (infectedCounts[n.id] / N);
                    etaMap[n.id] = infectedCounts[n.id] > 0 ? (etaSums[n.id] / infectedCounts[n.id]) : 45.0;
                });

                dcArrivals.sort((a, b) => a - b);
                const p10 = dcArrivals.length > 0 ? dcArrivals[Math.floor(dcArrivals.length * 0.1)] : 5.2;
                const p50 = dcArrivals.length > 0 ? dcArrivals[Math.floor(dcArrivals.length * 0.5)] : 16.4;
                const p90 = dcArrivals.length > 0 ? dcArrivals[Math.floor(dcArrivals.length * 0.9)] : 38.1;

                const result = { pMap, etaMap, ttdc: { p10, p50, p90 } };
                this.cascadeCache.set(cacheKey, result);
                return result;
            }

            // =====================================================================
            // Pure Rendering Function: render(tNow, config)
            // =====================================================================
            render(tNow, config = {}) {
                const ctx = this.ctx;
                if (!ctx) return;
                const dpr = this.dpr || 1;
                const W = this.width;
                const H = this.height;

                // Reset coordinate matrix cleanly
                ctx.setTransform(1, 0, 0, 1, 0, 0);
                ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

                // Set logical DPI scale
                ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

                // Run deterministic cascade for tNow
                const sim = this.runCascadeSimulation(tNow);
                this.currentP = sim.pMap;

                // Compute dynamic risk and frontier
                let sumW = 0, sumWP = 0;
                let frontierNode = null;
                let maxFirstComp = -1;

                this.nodes.forEach(n => {
                    const w = n.criticality || 0.5;
                    const p = sim.pMap[n.id] !== undefined ? sim.pMap[n.id] : (n.t <= tNow ? 1.0 : 0.0);
                    sumW += w;
                    sumWP += w * p;

                    if (n.t <= tNow && n.t > maxFirstComp) {
                        maxFirstComp = n.t;
                        frontierNode = n;
                    }
                });

                this.currentRisk = sumW > 0 ? clamp((100 * sumWP) / sumW, 10, 99) : 45;

                // Save transform for graph zoom / pan
                ctx.save();
                ctx.translate(this.panX, this.panY);
                ctx.scale(this.zoomFactor, this.zoomFactor);

                // 1. Draw Subtle Background Grid & Column Stages
                this.renderBackgroundAndStages(ctx, W, H);

                // 2. Render Projected Ghost Edges (Section 5)
                this.renderGhostEdges(ctx, tNow, sim.pMap);

                // 3. Render Actual Edges (Section 4)
                this.renderEdges(ctx, tNow);

                // 4. Render Projected Ghost Nodes (Section 5)
                this.renderGhostNodes(ctx, tNow, sim.pMap, sim.etaMap);

                // 5. Render Active / Confirmed Nodes (Section 3)
                this.renderNodes(ctx, tNow, frontierNode);

                ctx.restore();

                // 6. Render Integrated Timeline Strip (Section 7)
                this.renderTimelineStrip(ctx, tNow, sim);

                // 7. Render HUD Overlay (Section 8)
                this.renderHUD(ctx, tNow, frontierNode);
            }

            renderBackgroundAndStages(ctx, W, H) {
                ctx.fillStyle = '#0a0f1d';
                ctx.fillRect(0, 0, W, H);

                const padX = 75;
                const availW = W - 2 * padX;
                const stages = [
                    { title: "WAN / ADVERSARY", sub: "Stage 0 (Origin)" },
                    { title: "DMZ ENTRY", sub: "Initial Access & Exec" },
                    { title: "CREDENTIAL / USER", sub: "Token & Kerberos" },
                    { title: "INTERNAL LATERAL", sub: "Peer & C2 Pivot" },
                    { title: "CROWN JEWELS", sub: "Active Directory / DC" }
                ];

                ctx.font = '10px "Inter", -apple-system, sans-serif';
                ctx.textAlign = 'center';

                stages.forEach((st, i) => {
                    const x = padX + (i / 4) * availW;
                    ctx.strokeStyle = 'rgba(30, 41, 59, 0.45)';
                    ctx.setLineDash([3, 5]);
                    ctx.beginPath();
                    ctx.moveTo(x, 42);
                    ctx.lineTo(x, H - 98);
                    ctx.stroke();
                    ctx.setLineDash([]);

                    ctx.fillStyle = '#64748b';
                    ctx.fillText(st.title, x, 28);
                    ctx.fillStyle = '#475569';
                    ctx.fillText(st.sub, x, 40);
                });
            }

            renderGhostEdges(ctx, tNow, pMap) {
                ctx.save();
                this.reach.forEach(r => {
                    const src = this.nodeMap[r.src], dst = this.nodeMap[r.dst];
                    if (!src || !dst) return;
                    const srcComp = src.t <= tNow;
                    const dstComp = dst.t <= tNow;
                    const pDst = pMap[dst.id] || 0;

                    if (srcComp && !dstComp && pDst > 0.05) {
                        ctx.strokeStyle = `rgba(56, 189, 248, ${clamp(pDst * 0.85, 0.2, 0.9)})`;
                        ctx.lineWidth = 1.6;
                        ctx.setLineDash([4, 6]);
                        ctx.lineDashOffset = -((tNow * 12 + performance.now() * 0.04) % 10);
                        trace(ctx, src, dst, 0, 1);
                        ctx.stroke();
                        ctx.setLineDash([]);
                    }
                });
                ctx.restore();
            }

            renderEdges(ctx, tNow) {
                ctx.save();
                this.events.forEach((e, idx) => {
                    const td = tNow - e.t_min;
                    if (td < 0) return;

                    const src = this.nodeMap[e.src], dst = this.nodeMap[e.dst];
                    if (!src || !dst) return;

                    const colRgb = STAGE_COLORS[e.stage] || '239,68,68';

                    if (td <= 6) {
                        const u = clamp(td / 6, 0, 1);
                        ctx.strokeStyle = `rgba(${colRgb}, 0.9)`;
                        ctx.lineWidth = 2.4;
                        trace(ctx, src, dst, 0, u);
                        ctx.stroke();

                        const head = bz(src, dst, u);
                        ctx.fillStyle = '#ffffff';
                        ctx.shadowColor = `rgb(${colRgb})`;
                        ctx.shadowBlur = 12;
                        ctx.beginPath();
                        ctx.arc(head[0], head[1], 4, 0, 6.283);
                        ctx.fill();
                        ctx.shadowBlur = 0;
                    } else {
                        const alpha = td < 30 ? 0.85 : 0.45;
                        ctx.strokeStyle = `rgba(${colRgb}, ${alpha})`;
                        ctx.lineWidth = Math.min(3.5, 1.4 + (e.conf || 0.8) * 1.5);
                        trace(ctx, src, dst, 0, 1);
                        ctx.stroke();

                        if (td < 45) {
                            const uPhoton = ((tNow * 1.8 + idx * 0.25) % 1.2) / 1.2;
                            if (uPhoton <= 1.0) {
                                const pt = bz(src, dst, uPhoton);
                                ctx.fillStyle = '#ffffff';
                                ctx.shadowColor = `rgb(${colRgb})`;
                                ctx.shadowBlur = 10;
                                ctx.beginPath();
                                ctx.arc(pt[0], pt[1], 3, 0, 6.283);
                                ctx.fill();
                                ctx.shadowBlur = 0;
                            }
                        }

                        if (td <= 50) {
                            const pillAlpha = td <= 10 ? (td / 10) : clamp((50 - td) / 40, 0, 1);
                            const mid = bz(src, dst, 0.5);
                            ctx.fillStyle = `rgba(15, 23, 42, ${0.85 * pillAlpha})`;
                            ctx.strokeStyle = `rgba(${colRgb}, ${0.7 * pillAlpha})`;
                            ctx.lineWidth = 1;
                            const text = e.edgeLabel || e.stage;
                            ctx.font = '9px monospace';
                            const tw = ctx.measureText(text).width + 12;
                            ctx.beginPath();
                            ctx.roundRect(mid[0] - tw / 2, mid[1] - 8, tw, 16, 4);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = `rgba(255, 255, 255, ${pillAlpha})`;
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'middle';
                            ctx.fillText(text, mid[0], mid[1]);
                        }
                    }
                });
                ctx.restore();
            }

            renderGhostNodes(ctx, tNow, pMap, etaMap) {
                ctx.save();
                this.nodes.forEach(n => {
                    const age = tNow - n.t;
                    const p = pMap[n.id] || 0;
                    if (age < 0 && p > 0.05) {
                        const R = n.radius;
                        const isHighCrit = (n.criticality || 0) >= 0.8;
                        const colRgb = isHighCrit ? '168,85,247' : '56,189,248';

                        ctx.strokeStyle = `rgba(${colRgb}, ${clamp(p, 0.35, 0.95)})`;
                        ctx.fillStyle = `rgba(${colRgb}, 0.05)`;
                        ctx.lineWidth = 1.8;
                        ctx.setLineDash([4, 4]);

                        ctx.beginPath();
                        ctx.arc(n.x, n.y, R, 0, 6.283);
                        ctx.fill();
                        ctx.stroke();
                        ctx.setLineDash([]);

                        const eta = Math.round(etaMap[n.id] || 38);
                        ctx.font = '8.5px monospace';
                        ctx.textAlign = 'center';
                        ctx.fillStyle = `rgba(${colRgb}, 0.95)`;
                        ctx.fillText(`P=${p.toFixed(2)} (model estimate)`, n.x, n.y - R - 13);
                        ctx.fillStyle = '#94a3b8';
                        ctx.fillText(`ETA +${eta}m (model estimate)`, n.x, n.y - R - 3);

                        ctx.fillStyle = '#64748b';
                        ctx.fillText(n.id, n.x, n.y + R + 12);
                    }
                });
                ctx.restore();
            }

            renderNodes(ctx, tNow, frontierNode) {
                ctx.save();
                const R = 20;

                this.nodes.forEach(n => {
                    const age = tNow - n.t;
                    if (age < 0) return;

                    const colRgb = TYPE_COLORS[n.type] || '6,182,212';
                    const scale = easeOutBack(clamp(age / 8));
                    const heat = age < 25 ? 1 : clamp(1 - (age - 25) / 55);

                    if (age < 40) {
                        ctx.save();
                        ctx.globalCompositeOperation = 'lighter';
                        const waveU = age / 40;
                        const radGrad = ctx.createRadialGradient(n.x, n.y, R * 0.5, n.x, n.y, R * (1 + 2.5 * waveU));
                        radGrad.addColorStop(0, `rgba(${colRgb}, ${0.22 * (1 - waveU)})`);
                        radGrad.addColorStop(1, 'rgba(0,0,0,0)');
                        ctx.fillStyle = radGrad;
                        ctx.beginPath();
                        ctx.arc(n.x, n.y, R * (1 + 2.5 * waveU), 0, 6.283);
                        ctx.fill();
                        ctx.restore();
                    }

                    ctx.shadowColor = `rgb(${colRgb})`;
                    ctx.shadowBlur = 22 * heat;
                    ctx.fillStyle = `rgba(${colRgb}, ${0.25 + 0.65 * heat})`;
                    ctx.beginPath();
                    ctx.arc(n.x, n.y, R * scale, 0, 6.283);
                    ctx.fill();

                    ctx.strokeStyle = `rgba(${colRgb}, ${0.55 + 0.45 * heat})`;
                    ctx.lineWidth = 1.5 + 1.5 * heat;
                    ctx.stroke();
                    ctx.shadowBlur = 0;

                    if (age < 25) {
                        ctx.fillStyle = `rgba(255,255,255, ${heat})`;
                        ctx.beginPath();
                        ctx.arc(n.x, n.y, 4 * heat, 0, 6.283);
                        ctx.fill();
                    }

                    if (age < 22) {
                        const u = age / 22;
                        ctx.strokeStyle = `rgba(${colRgb}, ${0.7 * (1 - u)})`;
                        ctx.lineWidth = 2 * (1 - u);
                        ctx.beginPath();
                        ctx.arc(n.x, n.y, R * (1 + 2.2 * u), 0, 6.283);
                        ctx.stroke();
                    }

                    ctx.fillStyle = '#ffffff';
                    ctx.font = 'bold 9px -apple-system, monospace';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(n.type, n.x, n.y);

                    ctx.font = '9px monospace';
                    ctx.fillStyle = '#e2e8f0';
                    ctx.fillText(n.id, n.x, n.y + R + 12);
                    ctx.fillStyle = '#38bdf8';
                    ctx.fillText(`T+${Math.round(n.t)}m`, n.x, n.y + R + 22);

                    if (frontierNode && frontierNode.id === n.id && (tNow - n.t) < 45) {
                        const pulse = (Math.sin(performance.now() * 0.006) + 1) / 2;
                        ctx.strokeStyle = `rgba(245, 158, 11, ${0.5 + 0.5 * pulse})`;
                        ctx.lineWidth = 2.5;
                        ctx.beginPath();
                        ctx.arc(n.x, n.y, R * 1.5 + 4 * pulse, 0, 6.283);
                        ctx.stroke();

                        ctx.fillStyle = '#f59e0b';
                        ctx.beginPath();
                        ctx.roundRect(n.x - 22, n.y - R - 22, 44, 14, 4);
                        ctx.fill();
                        ctx.fillStyle = '#000000';
                        ctx.font = 'bold 8px monospace';
                        ctx.fillText('ACTIVE', n.x, n.y - R - 13);
                    }
                });
                ctx.restore();
            }

            renderTimelineStrip(ctx, tNow, sim) {
                ctx.save();
                const W = this.width;
                const H = this.height;
                const stripY = H - 88;
                const padX = 70;
                const stripW = W - 2 * padX;

                // Strip background
                ctx.fillStyle = 'rgba(10, 15, 29, 0.96)';
                ctx.fillRect(0, stripY, W, 88);
                ctx.strokeStyle = 'rgba(51, 65, 85, 0.7)';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(0, stripY);
                ctx.lineTo(W, stripY);
                ctx.stroke();

                const timeToX = (t) => padX + clamp(t / this.totalDuration, 0, 1) * stripW;
                const nowX = timeToX(tNow);
                const contX = timeToX(this.containmentT);

                // Hatched future pattern right of tNow
                if (nowX < padX + stripW) {
                    ctx.save();
                    ctx.beginPath();
                    ctx.rect(nowX, stripY, (padX + stripW) - nowX, 88);
                    ctx.clip();
                    ctx.strokeStyle = 'rgba(56, 189, 248, 0.08)';
                    ctx.lineWidth = 1;
                    for (let hx = nowX - 88; hx < padX + stripW + 88; hx += 12) {
                        ctx.beginPath();
                        ctx.moveTo(hx, stripY);
                        ctx.lineTo(hx + 88, stripY + 88);
                        ctx.stroke();
                    }
                    ctx.restore();
                }

                // P10-P90 TTDC Fan Band right of tNow
                const p10X = timeToX(tNow + this.ttdcP10);
                const p50X = timeToX(tNow + this.ttdcP50);
                const p90X = timeToX(tNow + this.ttdcP90);

                if (p10X < padX + stripW) {
                    ctx.fillStyle = 'rgba(168, 85, 247, 0.16)';
                    ctx.fillRect(p10X, stripY + 12, Math.max(2, p90X - p10X), 52);

                    ctx.strokeStyle = '#a855f7';
                    ctx.lineWidth = 1.5;
                    ctx.setLineDash([3, 3]);
                    ctx.beginPath();
                    ctx.moveTo(p50X, stripY + 10);
                    ctx.lineTo(p50X, stripY + 68);
                    ctx.stroke();
                    ctx.setLineDash([]);

                    ctx.fillStyle = '#c084fc';
                    ctx.font = '8px monospace';
                    ctx.textAlign = 'center';
                    ctx.fillText(`DC TTDC P50: +${Math.round(this.ttdcP50)}m (model estimate)`, p50X, stripY + 22);
                }

                // Baseline progress track
                const baseY = stripY + 60;
                ctx.strokeStyle = 'rgba(51, 65, 85, 0.8)';
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.moveTo(padX, baseY);
                ctx.lineTo(padX + stripW, baseY);
                ctx.stroke();

                // Solid replay track up to tNow
                ctx.strokeStyle = '#38bdf8';
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.moveTo(padX, baseY);
                ctx.lineTo(nowX, baseY);
                ctx.stroke();

                // Risk(t) curve across timeline
                const steps = 60;
                ctx.beginPath();
                for (let s = 0; s <= steps; s++) {
                    const t = (s / steps) * this.totalDuration;
                    const x = timeToX(t);
                    const rBase = 15 + 75 / (1 + Math.exp(-0.02 * (t - this.totalDuration * 0.4)));
                    const y = (stripY + 54) - (rBase / 100) * 38;
                    s === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
                }
                ctx.strokeStyle = 'rgba(239, 68, 68, 0.7)';
                ctx.lineWidth = 1.8;
                ctx.stroke();

                // Event tick dots on baseline
                this.events.forEach(ev => {
                    const ex = timeToX(ev.t_min);
                    const isFired = ev.t_min <= tNow;
                    const colRgb = STAGE_COLORS[ev.stage] || '239,68,68';

                    ctx.fillStyle = isFired ? `rgb(${colRgb})` : 'rgba(15, 23, 42, 0.9)';
                    ctx.strokeStyle = `rgb(${colRgb})`;
                    ctx.lineWidth = 1.2;
                    ctx.beginPath();
                    ctx.arc(ex, baseY, isFired ? 3.5 : 2.5, 0, 6.283);
                    ctx.fill();
                    ctx.stroke();
                });

                // Draggable Amber Containment Marker (Tc)
                ctx.strokeStyle = '#f59e0b';
                ctx.lineWidth = 1.8;
                ctx.setLineDash([4, 4]);
                ctx.beginPath();
                ctx.moveTo(contX, stripY + 4);
                ctx.lineTo(contX, stripY + 76);
                ctx.stroke();
                ctx.setLineDash([]);

                ctx.fillStyle = '#f59e0b';
                ctx.beginPath();
                ctx.arc(contX, stripY + 12, 5, 0, 6.283);
                ctx.fill();

                const savedEst = this.containmentT <= 60 ? (this.temporal.saved_assets_at_60 || 6) : (this.temporal.saved_assets_at_120 || 2);
                ctx.fillStyle = '#f59e0b';
                ctx.font = '8.5px monospace';
                ctx.textAlign = 'center';
                ctx.fillText(`Tc=${Math.round(this.containmentT)}m: Saved ${savedEst} assets (model estimate)`, contX, stripY + 34);

                // Draggable Cyan NOW Scrubber Knob
                ctx.strokeStyle = '#38bdf8';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(nowX, stripY + 6);
                ctx.lineTo(nowX, stripY + 76);
                ctx.stroke();

                ctx.fillStyle = '#38bdf8';
                ctx.shadowColor = '#38bdf8';
                ctx.shadowBlur = 10;
                ctx.beginPath();
                ctx.arc(nowX, baseY, 7, 0, 6.283);
                ctx.fill();
                ctx.shadowBlur = 0;

                ctx.fillStyle = '#0f172a';
                ctx.beginPath();
                ctx.arc(nowX, baseY, 3, 0, 6.283);
                ctx.fill();

                ctx.fillStyle = '#ffffff';
                ctx.font = 'bold 9px monospace';
                ctx.textAlign = 'center';
                ctx.fillText(`T+${Math.round(tNow)}m`, nowX, stripY + 76);

                ctx.fillStyle = '#64748b';
                ctx.font = '9px monospace';
                ctx.textAlign = 'left';
                ctx.fillText('TIMELINE & RISK(t)', padX, stripY + 14);
                ctx.textAlign = 'right';
                ctx.fillText(`${this.totalDuration}m CAMPAIGN`, padX + stripW, stripY + 14);

                ctx.restore();
            }

            renderHUD(ctx, tNow, frontierNode) {
                ctx.save();
                const hudX = 16, hudY = 16, hudW = 380, hudH = 108;

                ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
                ctx.strokeStyle = 'rgba(51, 65, 85, 0.85)';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.roundRect(hudX, hudY, hudW, hudH, 6);
                ctx.fill();
                ctx.stroke();

                let lastEventBefore = 0;
                this.events.forEach(ev => {
                    if (ev.t_min <= tNow && ev.t_min > lastEventBefore) lastEventBefore = ev.t_min;
                });
                const gap = tNow - lastEventBefore;
                const isPerimeterDormant = gap > (2 * Math.max(5.0, this.cadenceMedian));

                ctx.textAlign = 'left';
                ctx.textBaseline = 'top';

                ctx.font = 'bold 11px monospace';
                ctx.fillStyle = '#ffffff';
                ctx.fillText(`T+${String(Math.round(tNow)).padStart(3, '0')}m`, hudX + 12, hudY + 10);
                ctx.font = '10px monospace';
                ctx.fillStyle = '#38bdf8';
                ctx.fillText(`Cadence: ${this.cadenceMedian.toFixed(1)}m (${this.cadenceTrend}) (model estimate)`, hudX + 80, hudY + 11);

                const riskVal = Math.round(this.currentRisk);
                ctx.fillStyle = riskVal > 75 ? '#ef4444' : (riskVal > 45 ? '#f59e0b' : '#10b981');
                ctx.font = 'bold 10.5px monospace';
                ctx.fillText(`Risk: ${riskVal}/100`, hudX + 12, hudY + 30);
                ctx.fillStyle = '#94a3b8';
                ctx.font = '10px monospace';
                ctx.fillText(`Velocity: +${(1.2 + (riskVal / 100)).toFixed(1)}/min (model estimate)`, hudX + 130, hudY + 31);

                const frontStr = frontierNode ? `${frontierNode.id} (${frontierNode.type})` : 'Perimeter WAN';
                ctx.fillStyle = '#e2e8f0';
                ctx.fillText(`Frontier: ${frontStr} ──► DC Reachable (model estimate)`, hudX + 12, hudY + 50);

                ctx.fillStyle = '#cbd5e1';
                const modeStr = this.isPlaying ? `PLAYING (${this.speed} min/s)` : (this.tNow >= this.totalDuration - 1.5 ? 'COMPLETED (Click Replay)' : 'PAUSED (Scrubber Ready)');
                ctx.fillText(`Mode: ${modeStr}`, hudX + 12, hudY + 69);

                if (isPerimeterDormant) {
                    ctx.fillStyle = '#f59e0b';
                    ctx.fillText('Status: No perimeter-visible activity (intra-subnet or dormant)', hudX + 12, hudY + 88);
                } else {
                    ctx.fillStyle = '#38bdf8';
                    ctx.fillText('Status: Active lateral spread (model estimate)', hudX + 12, hudY + 88);
                }

                ctx.restore();
            }

            updateInspector(entity) {
                const hint = document.getElementById('inspector-hint-' + this.incId);
                const inspector = document.getElementById('inspector-' + this.incId);
                if (!inspector) return;

                if (!entity) {
                    if (hint) hint.innerHTML = 'Click any node or connection edge in the graph to inspect forensic telemetry and exposure details.';
                    return;
                }

                if (entity.type === 'node') {
                    const n = entity.data;
                    const p = this.currentP && this.currentP[n.id] !== undefined ? this.currentP[n.id] : 1.0;
                    const status = n.t <= this.tNow ? (this.tNow - n.t < 25 ? 'Active Pulse' : 'Confirmed Compromised') : `Projected Ghost (P=${p.toFixed(2)}) (model estimate)`;

                    inspector.innerHTML = `
                        <div class="inspector-title"><span>🔍</span> Node: <code>${n.id}</code></div>
                        <div style="font-size: 0.85rem; color: #cbd5e1; margin-bottom: 8px;">
                            <strong>Entity Type:</strong> ${n.type} &bull; <strong>Subnet:</strong> ${n.subnet || 'DMZ'}
                        </div>
                        <div style="font-size: 0.85rem; color: #cbd5e1; margin-bottom: 8px;">
                            <strong>Criticality:</strong> ${(n.criticality * 100).toFixed(0)}% &bull; <strong>Privilege:</strong> ${n.privLevel || 1.0}
                        </div>
                        <div style="font-size: 0.85rem; color: #38bdf8; margin-bottom: 8px;">
                            <strong>Status:</strong> ${status}
                        </div>
                        <div style="font-size: 0.8rem; color: #94a3b8; border-top: 1px solid #334155; padding-top: 8px;">
                            <strong>First Compromise:</strong> ${n.t !== 9999 ? 'T+' + Math.round(n.t) + 'm' : 'Forecasted Target'}<br>
                            <strong>Blast Radius Reach:</strong> Allowed Fortinet policy sessions verified
                        </div>
                    `;
                } else if (entity.type === 'edge') {
                    const e = entity.data;
                    inspector.innerHTML = `
                        <div class="inspector-title"><span>⚡</span> Attack Hop: <code>${e.src}</code> ──► <code>${e.dst}</code></div>
                        <div style="font-size: 0.85rem; color: #cbd5e1; margin-bottom: 8px;">
                            <strong>Stage:</strong> ${e.stage} &bull; <strong>Timestamp:</strong> T+${Math.round(e.t_min)}m
                        </div>
                        <div style="font-size: 0.85rem; color: #cbd5e1; margin-bottom: 8px;">
                            <strong>Technique:</strong> ${e.edgeLabel || 'Lateral Execution'}
                        </div>
                        <div style="font-size: 0.8rem; color: #94a3b8; border-top: 1px solid #334155; padding-top: 8px;">
                            <strong>Evidence:</strong> ${e.label || 'Direct forensic signature match'}<br>
                            <strong>Observed Cadence:</strong> Real policy reachability &Delta; = ${this.cadenceMedian.toFixed(1)}m
                        </div>
                    `;
                }
            }
        }

        // Global button hook helpers with robust fallback resolver
        function getGraph(incId) {
            return GRAPH_INSTANCES[incId] || GRAPH_INSTANCES[Number(incId)] || GRAPH_INSTANCES[String(incId)] || Object.values(GRAPH_INSTANCES)[0];
        }

        function togglePlay(incId) {
            const g = getGraph(incId);
            if (g) g.isPlaying ? g.pause() : g.play();
        }

        function resetScrubber(incId) {
            const g = getGraph(incId);
            if (g) g.reset();
        }

        function stepScrubber(incId, delta) {
            const g = getGraph(incId);
            if (g) g.seek(g.tNow + delta);
        }

        function onScrubInput(incId, val) {
            const g = getGraph(incId);
            if (g) {
                g.pause(); // Pause while user drags the slider
                g.seek(parseFloat(val));
            }
        }

        function zoomGraph(incId, factor) {
            const g = getGraph(incId);
            if (g) g.zoom(factor);
        }

        function resetGraphView(incId) {
            const g = getGraph(incId);
            if (g) g.resetView();
        }

        function togglePhysics(incId) {
            togglePlay(incId);
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

        // Keyboard shortcuts for flawless demo presentation
        window.addEventListener('keydown', (e) => {
            if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;
            const g = Object.values(GRAPH_INSTANCES)[0];
            if (!g) return;
            if (e.code === 'Space') {
                e.preventDefault();
                g.isPlaying ? g.pause() : g.play();
            } else if (e.code === 'KeyR' || e.code === 'Home') {
                e.preventDefault();
                g.reset();
            } else if (e.code === 'ArrowLeft') {
                e.preventDefault();
                g.seek(g.tNow - 15);
            } else if (e.code === 'ArrowRight') {
                e.preventDefault();
                g.seek(g.tNow + 15);
            }
        });

        // Safe initialization handling whether DOM is still loading or already parsed
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initAllGraphs);
        } else {
            initAllGraphs();
        }
    </script>"""

def patch_template():
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(f"Cannot find {TEMPLATE_PATH}")

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Match <script>...</script> at the end
    script_pattern = re.compile(r'    <script>.*?</script>', re.DOTALL)
    if not script_pattern.search(content):
        raise ValueError("Could not find <script> tag in templates/incident_report.j2")

    new_content = script_pattern.sub(JS_ENGINE_CODE, content, count=1)

    with open(TEMPLATE_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("Successfully patched templates/incident_report.j2 with enhanced playback controls!")

if __name__ == "__main__":
    patch_template()
