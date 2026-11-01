import re

html_path = "out/causal_replay.html"
with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add CSS for zoom buttons
nav_css = """
        .canvas-nav-btn {
            background: rgba(15, 23, 42, 0.90);
            border: 1px solid rgba(51, 65, 85, 0.8);
            color: #f8fafc;
            padding: 7px 13px;
            border-radius: 6px;
            font-size: 11.5px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 5px;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 14px rgba(0,0,0,0.4);
            transition: all 0.15s ease;
        }
        .canvas-nav-btn:hover {
            background: rgba(30, 41, 59, 0.95);
            border-color: var(--accent-cyan);
            color: var(--accent-cyan);
            transform: translateY(-1px);
        }
"""
if ".canvas-nav-btn" not in content:
    content = content.replace("</style>", nav_css + "\n    </style>")

# 2. Add floating Zoom In, Zoom Out, Fit Graph controls inside viewport-container
zoom_html = """
        <!-- Interactive Canvas Zoom & Pan Controls -->
        <div id="canvas-nav-controls" style="position: absolute; bottom: 18px; left: 18px; display: flex; gap: 8px; z-index: 50;">
            <button class="canvas-nav-btn" id="btn-zoom-in" title="Zoom In (or Mouse Wheel Up)">
                <span>🔍</span> Zoom In
            </button>
            <button class="canvas-nav-btn" id="btn-zoom-out" title="Zoom Out (or Mouse Wheel Down)">
                <span>🔍</span> Zoom Out
            </button>
            <button class="canvas-nav-btn" id="btn-fit-graph" title="Reset View & Fit Graph" style="color: #38bdf8;">
                <span>⛶</span> Fit Graph
            </button>
        </div>
"""
if 'id="canvas-nav-controls"' not in content:
    content = content.replace('<canvas id="visCanvas"></canvas>', '<canvas id="visCanvas"></canvas>\n' + zoom_html)

# 3. Update generateStochasticEvents and loadScenario
old_gen = """            for (let i = 0; i < count; i++) {
                const cIdx = i === 0 ? 0 : (i === count - 1 ? 6 : Math.floor(Math.pow(prng(), 0.8) * Math.min(numClusters, clusterNames.length)));
                const cluster = clusterNames[cIdx];

                let parent = null;
                if (i > 0) {
                    const parentIdx = Math.floor(Math.pow(prng(), 1.4) * i);
                    parent = `node_${parentIdx}`;
                }

                // Stochastic dwell dormancy gaps via Lomax distribution
                const dwell = (i % 6 === 0 && i > 0) ? CausalReplay.sampleLomaxDwell(prng(), 1.5, 24.0, 3.0) : (0.5 + prng() * 2.5);
                curT += dwell;

                const isCrown = cluster.includes('DC') || cluster.includes('Vault');
                const isHighCrit = isCrown || (i % 12 === 0);

                events.push({
                    id: `node_${i}`,
                    cluster,
                    parent,
                    t: curT,
                    criticality: isCrown ? 0.95 : (isHighCrit ? 0.78 : 0.35)
                });
            }"""

new_gen = """            for (let i = 0; i < count; i++) {
                const cIdx = i === 0 ? 0 : (i === count - 1 ? 6 : Math.floor(Math.pow(prng(), 0.8) * Math.min(numClusters, clusterNames.length)));
                const cluster = clusterNames[cIdx];

                let parent = null;
                if (i > 0) {
                    const parentIdx = Math.floor(Math.pow(prng(), 1.4) * i);
                    parent = `node_${parentIdx}`;
                }

                // Stochastic dwell dormancy gaps via Lomax distribution
                const dwell = (i % 6 === 0 && i > 0) ? CausalReplay.sampleLomaxDwell(prng(), 1.5, 24.0, 3.0) : (0.5 + prng() * 2.5);
                curT += dwell;

                const isCrown = cluster.includes('DC') || cluster.includes('Vault') || (i === count - 1);
                const isHighCrit = isCrown || (i % 12 === 0);

                let nodeType = 'HOST';
                let nodeLabel = `10.10.20.${10 + i}`;
                if (i === 0) {
                    nodeType = 'WAN';
                    nodeLabel = '92.151.63.124 (Attacker WAN)';
                } else if (isCrown) {
                    nodeType = 'DC';
                    nodeLabel = '10.10.99.1 (Domain Controller)';
                } else if (i % 7 === 0) {
                    nodeType = 'USER';
                    nodeLabel = `User: admin_operator_${i}`;
                }

                events.push({
                    id: `node_${i}`,
                    cluster,
                    parent,
                    t: curT,
                    criticality: isCrown ? 0.98 : (isHighCrit ? 0.78 : 0.35),
                    type: nodeType,
                    label: nodeLabel,
                    mitreTechName: isCrown ? 'Active Directory DCSync' : (i === 0 ? 'Initial Remote Ingress' : 'Lateral Remote Services')
                });
            }"""

if old_gen in content:
    content = content.replace(old_gen, new_gen)

# 4. Ensure isCausalReplay: true is passed
old_engine_init = """            engine = new CausalReplay.CausalTerritorialEngine({
                seed: 42
            });"""
new_engine_init = """            engine = new CausalReplay.CausalTerritorialEngine({
                seed: 42,
                isCausalReplay: true
            });"""
if old_engine_init in content:
    content = content.replace(old_engine_init, new_engine_init)

# 5. Add interactive Wheel, Pan, and Zoom Button Event Handlers
interact_js = """
        // Interactive Canvas Navigation (Scrolling / Wheel Zoom & Drag-to-Pan)
        let isCanvasPanning = false;
        let panStartX = 0;
        let panStartY = 0;

        canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            if (!engine) return;
            const factor = e.deltaY < 0 ? 1.15 : 0.87;
            engine.zoom(factor);
        }, { passive: false });

        canvas.addEventListener('mousedown', (e) => {
            if (e.button === 0) {
                isCanvasPanning = true;
                panStartX = e.clientX;
                panStartY = e.clientY;
                canvas.style.cursor = 'grabbing';
            }
        });

        window.addEventListener('mousemove', (e) => {
            if (!isCanvasPanning || !engine) return;
            const dx = e.clientX - panStartX;
            const dy = e.clientY - panStartY;
            panStartX = e.clientX;
            panStartY = e.clientY;
            const rect = canvas.getBoundingClientRect();
            engine.pan(dx, dy, rect.width, rect.height, tNow);
        });

        window.addEventListener('mouseup', () => {
            if (isCanvasPanning) {
                isCanvasPanning = false;
                canvas.style.cursor = 'default';
            }
        });

        // Floating Zoom In / Zoom Out / Fit Graph Buttons
        document.getElementById('btn-zoom-in').addEventListener('click', () => {
            if (engine) engine.zoom(1.25);
        });
        document.getElementById('btn-zoom-out').addEventListener('click', () => {
            if (engine) engine.zoom(0.80);
        });
        document.getElementById('btn-fit-graph').addEventListener('click', () => {
            if (engine) engine.resetView();
        });
"""

if "isCanvasPanning" not in content:
    content = content.replace("// Speed buttons", interact_js + "\n        // Speed buttons")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully patched out/causal_replay.html with zoom, scrolling, and threat animations!")
