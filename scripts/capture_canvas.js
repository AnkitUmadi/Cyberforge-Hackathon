const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const PORT = 9222;
const USER_DATA = path.join(__dirname, '..', '.chrome_test_profile');

async function shot() {
    const chrome = spawn(CHROME, [
        '--headless=new',
        `--remote-debugging-port=${PORT}`,
        `--user-data-dir=${USER_DATA}`,
        '--window-size=1920,1080',
        '--disable-gpu',
        '--no-sandbox',
        'http://localhost:8000/'
    ]);
    await new Promise(r => setTimeout(r, 2200));

    try {
        const targets = await new Promise((resolve, reject) => {
            http.get(`http://localhost:${PORT}/json`, (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => resolve(JSON.parse(data)));
            }).on('error', reject);
        });

        const page = targets.find(t => t.type === 'page');
        const ws = new WebSocket(page.webSocketDebuggerUrl);
        await new Promise(r => ws.onopen = r);

        let reqId = 1;
        function send(method, params = {}) {
            return new Promise(resolve => {
                const id = reqId++;
                const handler = (evt) => {
                    const m = JSON.parse(evt.data);
                    if (m.id === id) {
                        ws.removeEventListener('message', handler);
                        resolve(m);
                    }
                };
                ws.addEventListener('message', handler);
                ws.send(JSON.stringify({ id, method, params }));
            });
        }

        await send('Runtime.enable');

        // Seek instance 2 to full campaign time to capture all nodes and connections
        await send('Runtime.evaluate', {
            expression: `(() => {
                const g = window.GRAPH_INSTANCES["2"];
                if (g) {
                    g.seek(250);
                    g.stepNextHop();
                }
            })()`
        });
        await new Promise(r => setTimeout(r, 1200));

        // Scroll canvas-box-2 into view
        await send('Runtime.evaluate', {
            expression: `(() => {
                const el = document.getElementById('canvas-box-2');
                if (el) el.scrollIntoView({ behavior: 'instant', block: 'center' });
            })()`
        });
        await new Promise(r => setTimeout(r, 600));

        // Get bounding rect of #canvas-box-2
        const clipRes = await send('Runtime.evaluate', {
            expression: `(() => {
                const el = document.getElementById('canvas-box-2');
                if (!el) return null;
                const r = el.getBoundingClientRect();
                return {
                    x: r.left,
                    y: r.top,
                    width: r.width,
                    height: r.height,
                    scale: 1
                };
            })()`,
            returnByValue: true
        });

        console.log('Canvas Clip Bounds:', clipRes.result?.result?.value);
        if (clipRes.result?.result?.value) {
            const shotRes = await send('Page.captureScreenshot', {
                format: 'png',
                clip: clipRes.result.result.value
            });
            const outPath = path.join(__dirname, '..', 'out', 'incident_2_canvas_causal.png');
            fs.writeFileSync(outPath, Buffer.from(shotRes.result.data, 'base64'));
            console.log('Saved focused canvas screenshot to:', outPath);
        }

        ws.close();
    } finally {
        chrome.kill();
    }
}

shot().catch(console.error);
