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
            if (data.method === 'Runtime.consoleAPICalled') {
                console.log('[CONSOLE]', data.params.type, data.params.args.map(a => a.value || a.description));
            }
            if (data.method === 'Runtime.exceptionThrown') {
                console.error('[PAGE EXCEPTION]', data.params.exceptionDetails.text, data.params.exceptionDetails.exception?.description);
            }
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
        await cdpSend('Console.enable');

        await new Promise(r => setTimeout(r, 1500));

        // Check if CausalReplay is defined
        const r1 = await cdpSend('Runtime.evaluate', {
            expression: 'typeof window.CausalReplay',
            returnByValue: true
        });
        console.log('window.CausalReplay type:', r1.result?.result?.value);

        // Check GRAPH_INSTANCES keys
        const r2 = await cdpSend('Runtime.evaluate', {
            expression: 'Object.keys(window.GRAPH_INSTANCES || {})',
            returnByValue: true
        });
        console.log('GRAPH_INSTANCES keys:', r2.result?.result?.value);

        // Check first instance
        const r3 = await cdpSend('Runtime.evaluate', {
            expression: `(() => {
                const keys = Object.keys(window.GRAPH_INSTANCES || {});
                if (!keys.length) return { empty: true };
                const k = keys[0];
                const g = window.GRAPH_INSTANCES[k];
                return {
                    incId: k,
                    hasEngine: !!g.engine,
                    nodeCount: g.engine ? g.engine.nodes.length : 0,
                    speed: g.speed,
                    isPlaying: g.isPlaying,
                    tNow: g.tNow,
                    totalDuration: g.totalDuration
                };
            })()`,
            returnByValue: true
        });
        console.log('First instance info:', r3.result?.result?.value);

        // Test stepNextHop on first instance
        const r4 = await cdpSend('Runtime.evaluate', {
            expression: `(() => {
                const keys = Object.keys(window.GRAPH_INSTANCES || {});
                if (!keys.length) return null;
                const g = window.GRAPH_INSTANCES[keys[0]];
                g.stepNextHop();
                return {
                    tNowAfterStep: g.tNow,
                    isPlaying: g.isPlaying
                };
            })()`,
            returnByValue: true
        });
        console.log('\n--- STEP NEXT HOP RESULT ---');
        console.log(r4.result?.result?.value);

        // Wait 400ms for RAF to update briefing card
        await new Promise(r => setTimeout(r, 400));

        const r5 = await cdpSend('Runtime.evaluate', {
            expression: `(() => {
                const keys = Object.keys(window.GRAPH_INSTANCES || {});
                if (!keys.length) return null;
                const k = keys[0];
                const brief = document.getElementById('hud-briefing-' + k);
                return {
                    briefingDisplay: brief ? window.getComputedStyle(brief).display : null,
                    briefingBadge: document.getElementById('brief-badge-' + k)?.innerText,
                    briefingHeadline: document.getElementById('brief-headline-' + k)?.innerText,
                    briefingLineage: document.getElementById('brief-lineage-' + k)?.innerText,
                    briefingTalkingPoint: document.getElementById('brief-talking-point-' + k)?.innerText
                };
            })()`,
            returnByValue: true
        });
        console.log('\n--- BRIEFING CARD AFTER TICK ---');
        console.log(r5.result?.result?.value);

        // Capture screenshot
        const shotRes = await cdpSend('Page.captureScreenshot', { format: 'png' });
        if (shotRes.result && shotRes.result.data) {
            const buf = Buffer.from(shotRes.result.data, 'base64');
            const outPath = path.join(__dirname, '..', 'out', 'verified_incident_report.png');
            fs.writeFileSync(outPath, buf);
            console.log('\nScreenshot saved to:', outPath);
        }

        ws.close();
    } finally {
        chromeProc.kill();
    }
}

run().catch(console.error);
