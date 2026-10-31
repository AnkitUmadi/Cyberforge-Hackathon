const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

async function testCanvas() {
    const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
        '--headless=new',
        '--remote-debugging-port=9222',
        '--user-data-dir=C:\\Users\\Ankit Umadi\\Documents\\hack\\.chrome_test_profile',
        '--window-size=1920,1080',
        'http://localhost:8000/'
    ]);
    await new Promise(r => setTimeout(r, 2200));

    try {
        const targets = await new Promise((resolve, reject) => {
            http.get('http://localhost:9222/json', (res) => {
                let d = '';
                res.on('data', c => d += c);
                res.on('end', () => resolve(JSON.parse(d)));
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

        const canvasInfo = await send('Runtime.evaluate', {
            expression: `(() => {
                const g = window.GRAPH_INSTANCES["2"];
                if (!g) return { error: "no instance 2" };
                g.seek(250);
                const c = document.getElementById("graph-canvas-2");
                return {
                    canvasWidth: c.width,
                    canvasHeight: c.height,
                    clientWidth: c.clientWidth,
                    clientHeight: c.clientHeight,
                    tNow: g.tNow,
                    nodes: g.engine.nodes.map(n => ({
                        id: n.id,
                        cluster: n.cluster,
                        x: Math.round(n.x),
                        y: Math.round(n.y),
                        birth: n.birthTime
                    })),
                    dataUrlLen: c.toDataURL().length
                };
            })()`,
            returnByValue: true
        });
        console.log('Canvas Info:', JSON.stringify(canvasInfo.result.result.value, null, 2));

        const urlRes = await send('Runtime.evaluate', {
            expression: 'document.getElementById("graph-canvas-2").toDataURL("image/png")',
            returnByValue: true
        });

        const base64 = urlRes.result.result.value.replace(/^data:image\/png;base64,/, '');
        const buf = Buffer.from(base64, 'base64');
        fs.writeFileSync('out/canvas_2_direct.png', buf);
        console.log('Saved out/canvas_2_direct.png, bytes:', buf.length);

        ws.close();
    } finally {
        chrome.kill();
    }
}

testCanvas().catch(console.error);
