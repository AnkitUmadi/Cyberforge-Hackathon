const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const PORT = 9226;
const USER_DATA = path.join(__dirname, '..', '.chrome_test_profile_causal_verify');

async function testCausal() {
    const chrome = spawn(CHROME, [
        '--headless=new',
        `--remote-debugging-port=${PORT}`,
        `--user-data-dir=${USER_DATA}`,
        '--window-size=1600,1000',
        '--disable-gpu',
        '--no-sandbox',
        'http://localhost:8000/causal'
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
        if (!page) throw new Error('No page target found');

        const ws = new WebSocket(page.webSocketDebuggerUrl);
        let reqId = 1;
        const pending = new Map();
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.id && pending.has(data.id)) {
                pending.get(data.id)(data.result);
                pending.delete(data.id);
            }
        };

        await new Promise(r => ws.onopen = r);

        function send(method, params = {}) {
            return new Promise((resolve) => {
                const id = reqId++;
                pending.set(id, resolve);
                ws.send(JSON.stringify({ id, method, params }));
            });
        }

        await send('Page.enable');
        await send('Runtime.enable');

        // Seek simulation to Domain Compromise timestamp (around t=220)
        await send('Runtime.evaluate', {
            expression: `(() => {
                if (window.engine && window.engine.playbackEngine) {
                    window.engine.playbackEngine.seekToSimTime(220);
                }
                tNow = 220;
            })()`
        });

        await new Promise(r => setTimeout(r, 1200));

        const shotRes = await send('Page.captureScreenshot', {
            format: 'png',
            clip: { x: 0, y: 0, width: 1600, height: 1000, scale: 1 }
        });

        const outPath = path.join('C:', 'Users', 'Ankit Umadi', '.gemini', 'antigravity', 'brain', '6a9d9833-85d5-46e8-ad11-e15e60757e5e', 'causal_dc_threat_verified.png');
        fs.writeFileSync(outPath, Buffer.from(shotRes.data, 'base64'));
        console.log('Saved causal screenshot to:', outPath);

        ws.close();
    } finally {
        chrome.kill();
    }
}

testCausal().catch(err => {
    console.error(err);
    process.exit(1);
});
