const { spawn } = require('child_process');
const http = require('http');
const path = require('path');

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const PORT = 9222;
const USER_DATA = path.join(__dirname, '..', '.chrome_test_profile');

async function getTargets() {
    return new Promise((resolve, reject) => {
        http.get(`http://localhost:${PORT}/json`, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve(JSON.parse(data)));
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
        await new Promise(r => setTimeout(r, 1000));

        // Test Incident #2 Briefings
        const res = await cdpSend('Runtime.evaluate', {
            expression: `(() => {
                const inst = window.GRAPH_INSTANCES['2'];
                if (!inst) return { error: 'No instance 2' };

                // 1. Check Hop 5 content
                const hop5 = inst.customBriefings ? inst.customBriefings[4] : null;

                // 2. Seek to end of campaign
                inst.seek(inst.totalDuration);

                const briefEl = document.getElementById('hud-briefing-2');
                const badge = document.getElementById('brief-badge-2')?.innerText;
                const headline = document.getElementById('brief-headline-2')?.innerText;
                const lineage = document.getElementById('brief-lineage-2')?.innerText;
                const talkingPoint = document.getElementById('brief-talking-point-2')?.innerText;

                return {
                    hop5: hop5 ? {
                        headline: hop5.headline,
                        lineage: hop5.causalLineage,
                        talkingPoint: hop5.presenterTalkingPoints[0]
                    } : null,
                    finalStateCard: {
                        displayed: briefEl ? window.getComputedStyle(briefEl).display : null,
                        badge: badge,
                        headline: headline,
                        lineage: lineage,
                        talkingPoint: talkingPoint
                    }
                };
            })()`,
            returnByValue: true
        });

        console.log('BRIEFING FIX VERIFICATION:\n', JSON.stringify(res.result?.result?.value, null, 2));
        ws.close();
    } finally {
        chromeProc.kill();
    }
}

run().catch(console.error);
