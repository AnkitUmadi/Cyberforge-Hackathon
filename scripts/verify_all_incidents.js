const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const PORT = 9222;
const USER_DATA = path.join(__dirname, '..', '.chrome_test_profile');

async function getTargets() {
    return new Promise((resolve, reject) => {
        http.get(`http://localhost:${PORT}/json`, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch (e) {
                    reject(e);
                }
            });
        }).on('error', reject);
    });
}

async function run() {
    const chromeProc = spawn(CHROME, [
        '--headless=new',
        `--remote-debugging-port=${PORT}`,
        `--user-data-dir=${USER_DATA}`,
        '--disable-gpu',
        '--no-sandbox',
        'http://localhost:8000/'
    ]);

    await new Promise(r => setTimeout(r, 2000));

    try {
        const targets = await getTargets();
        const page = targets.find(t => t.type === 'page');
        if (!page) throw new Error('No page target found');

        const ws = new WebSocket(page.webSocketDebuggerUrl);
        let reqId = 1;
        const pending = new Map();

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.id && pending.has(data.id)) {
                pending.get(data.id)(data);
                pending.delete(data.id);
            }
        };

        await new Promise(r => ws.onopen = r);

        function cdpSend(method, params = {}) {
            return new Promise((resolve) => {
                const id = reqId++;
                pending.set(id, resolve);
                ws.send(JSON.stringify({ id, method, params }));
            });
        }

        await cdpSend('Runtime.enable');
        await cdpSend('Emulation.setDeviceMetricsOverride', {
            width: 1440,
            height: 960,
            deviceScaleFactor: 2,
            mobile: false
        });
        await new Promise(r => setTimeout(r, 1500));

        // Evaluate all top incidents dynamically
        const evalRes = await cdpSend('Runtime.evaluate', {
            expression: `(() => {
                const results = {};
                const keys = Object.keys(window.GRAPH_INSTANCES || {});
                for (const id of keys) {
                    const inst = window.GRAPH_INSTANCES[id];
                    const engine = inst.engine;
                    results[id] = {
                        found: true,
                        nodeCount: engine ? engine.nodes.length : 0,
                        nodeTypes: engine ? engine.nodes.map(n => n.type + ':' + n.label) : [],
                        totalDuration: inst.totalDuration,
                        milestoneCount: inst.milestones ? inst.milestones.length : 0
                    };
                }
                return results;
            })()`,
            returnByValue: true
        });

        console.log('ALL 5 INCIDENTS VERIFICATION:\n', JSON.stringify(evalRes.result?.result?.value, null, 2));

        // Also take a screenshot of Incident 2 specifically
        await cdpSend('Runtime.evaluate', {
            expression: `(() => {
                const el = document.getElementById('canvas-box-2');
                if (el) el.scrollIntoView({ block: 'center', behavior: 'instant' });
                const inst = window.GRAPH_INSTANCES ? window.GRAPH_INSTANCES['2'] : null;
                if (inst) {
                    inst.seek(inst.totalDuration); // Scrub to completed state to see all nodes
                }
            })()`
        });

        await new Promise(r => setTimeout(r, 800));

        const scrollRes = await cdpSend('Runtime.evaluate', {
            expression: `(() => {
                const el = document.getElementById('canvas-box-2');
                if (el) {
                    const rect = el.getBoundingClientRect();
                    return {
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    };
                }
                return null;
            })()`,
            returnByValue: true
        });
        console.log('\nIncident 2 Canvas-Box BoundingRect:', scrollRes.result?.result?.value);

        const box = scrollRes.result?.result?.value;
        const shotRes = await cdpSend('Page.captureScreenshot', {
            format: 'png',
            clip: box && box.y >= 0 && box.height > 0 ? {
                x: Math.max(0, box.x),
                y: Math.max(0, box.y),
                width: box.width,
                height: box.height,
                scale: 1
            } : undefined
        });

        if (shotRes.result && shotRes.result.data) {
            const buf = Buffer.from(shotRes.result.data, 'base64');
            const outPath = path.join(__dirname, '..', 'out', 'incident_2_canvas_focused.png');
            fs.writeFileSync(outPath, buf);
            console.log('\nFocused Incident 2 Screenshot saved to:', outPath);
        }

        ws.close();
    } finally {
        chromeProc.kill();
    }
}

run().catch(console.error);
