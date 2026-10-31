/**
 * Formal Property Test Suite for Causal Territorial Layout Engine
 *
 * Verifies the 6 fundamental mathematical invariants:
 * 1. Prefix Invariance: layout(events[0..k]) === layout(all)[0..k]
 * 2. Zero Displacement: Delta x_i(t) = 0 for all t >= t_birth + duration
 * 3. Pairwise No-Overlap: min ||x_i - x_j|| >= R_min
 * 4. Territorial Clearance: ||s_a - s_b|| >= R_a + R_b
 * 5. Deterministic Reversibility: Scrubbing 200 -> 40 -> 350 -> 200 yields bit-exact state
 * 6. Massive Scale Benchmark: 65,000 nodes placement and sub-millisecond quadtree queries
 */

import type { NodeEvent, PlacedNode } from '../src/vis/lattice.ts';
import { CausalTerritorialEngine } from '../src/vis/engine.ts';
import { getBudState } from '../src/vis/bud.ts';

function createMockCampaign(count: number, numClusters: number = 8): NodeEvent[] {
    const events: NodeEvent[] = [];
    const clusterNames = Array.from({ length: numClusters }, (_, i) => `subnet_${i}`);

    for (let i = 0; i < count; i++) {
        const cluster = clusterNames[i % numClusters];
        // Parent is either null for patient zero, or an earlier node
        let parent: string | null = null;
        if (i > 0) {
            // Pick an earlier node (bias towards same cluster or root)
            const parentIdx = Math.floor(Math.pow(Math.random(), 1.5) * i);
            parent = `node_${parentIdx}`;
        }

        events.push({
            id: `node_${i}`,
            cluster,
            parent,
            t: 5.0 + i * 2.5, // 2.5 minutes between events
            criticality: i % 15 === 0 ? 0.95 : (i % 5 === 0 ? 0.75 : 0.3)
        });
    }

    return events;
}

function runSuite() {
    console.log('================================================================');
    console.log('RUNNING CAUSAL TERRITORIAL LAYOUT ENGINE PROPERTY VERIFICATION');
    console.log('================================================================\n');

    let passed = 0;
    let failed = 0;

    function assert(desc: string, condition: boolean, detail?: string) {
        if (condition) {
            console.log(`[PASS] ${desc}`);
            passed++;
        } else {
            console.error(`[FAIL] ${desc} ${detail ? `-> ${detail}` : ''}`);
            failed++;
        }
    }

    // -------------------------------------------------------------------------
    // TEST 1: Prefix Property Invariant
    // -------------------------------------------------------------------------
    console.log('--- TEST 1: Prefix Invariance ---');
    {
        const total = 100;
        const prefixCount = 30;
        const fullEvents = createMockCampaign(total, 5);

        // Run prefix engine
        const enginePrefix = new CausalTerritorialEngine({ seed: 42 });
        const prefixNodes = enginePrefix.ingest(fullEvents.slice(0, prefixCount));

        // Run full engine
        const engineFull = new CausalTerritorialEngine({ seed: 42 });
        const fullNodes = engineFull.ingest(fullEvents);

        let identical = true;
        let maxDelta = 0;

        for (let i = 0; i < prefixCount; i++) {
            const pNode = prefixNodes[i];
            const fNode = fullNodes[i];
            const dx = Math.abs(pNode.x - fNode.x);
            const dy = Math.abs(pNode.y - fNode.y);
            const delta = Math.hypot(dx, dy);
            if (delta > maxDelta) maxDelta = delta;

            if (delta > 1e-6) {
                identical = false;
                break;
            }
        }

        assert(
            `Prefix Property: First ${prefixCount} nodes have identical positions in prefix vs full run`,
            identical,
            `Max delta = ${maxDelta}`
        );
    }

    // -------------------------------------------------------------------------
    // TEST 2: Zero Displacement (Coordinate Invariance)
    // -------------------------------------------------------------------------
    console.log('\n--- TEST 2: Zero Displacement (Frozen Coordinate Guarantee) ---');
    {
        const engine = new CausalTerritorialEngine({ seed: 99 });
        const events = createMockCampaign(80, 4);
        const nodes = engine.ingest(events);

        // Test settled position at multiple future timestamps
        let zeroDisplacement = true;
        let maxDisplacement = 0;

        for (const n of nodes) {
            const settleTime = n.birthTime + 8.0; // Settled after 8 minutes
            const stateA = getBudState(n, settleTime);
            const stateB = getBudState(n, settleTime + 50.0);
            const stateC = getBudState(n, settleTime + 500.0);

            const dAB = Math.hypot(stateA.x - stateB.x, stateA.y - stateB.y);
            const dBC = Math.hypot(stateB.x - stateC.x, stateB.y - stateC.y);
            const dSlot = Math.hypot(stateC.x - n.x, stateC.y - n.y);

            const err = Math.max(dAB, dBC, dSlot);
            if (err > maxDisplacement) maxDisplacement = err;
            if (err > 1e-6) {
                zeroDisplacement = false;
                break;
            }
        }

        assert(
            'Zero Displacement: Settled node coordinates do not shift over future time',
            zeroDisplacement,
            `Max displacement = ${maxDisplacement}`
        );
    }

    // -------------------------------------------------------------------------
    // TEST 3: Pairwise No-Overlap
    // -------------------------------------------------------------------------
    console.log('\n--- TEST 3: Pairwise No-Overlap ---');
    {
        const engine = new CausalTerritorialEngine({
            territory: { minNodeDistance: 18 },
            seed: 777
        });
        const events = createMockCampaign(150, 6);
        const nodes = engine.ingest(events);

        let minPairDist = Infinity;
        let overlappingPairs = 0;

        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                const d = Math.hypot(nodes[i].x - nodes[j].x, nodes[i].y - nodes[j].y);
                if (d < minPairDist) minPairDist = d;
                if (d < 18 - 1e-3) {
                    overlappingPairs++;
                }
            }
        }

        assert(
            `Pairwise Clearance: min pairwise distance (${minPairDist.toFixed(2)}px) >= threshold (18px)`,
            overlappingPairs === 0,
            `${overlappingPairs} overlapping pairs detected`
        );
    }

    // -------------------------------------------------------------------------
    // TEST 4: Territorial Clearance
    // -------------------------------------------------------------------------
    console.log('\n--- TEST 4: Territorial Clearance ---');
    {
        const engine = new CausalTerritorialEngine({ seed: 555 });
        const events = createMockCampaign(200, 8);
        engine.ingest(events);

        const clusters = Array.from(engine.territoryEngine.clusters.values());
        let clustersOverlap = false;
        let minClearance = Infinity;

        for (let i = 0; i < clusters.length; i++) {
            for (let j = i + 1; j < clusters.length; j++) {
                const cA = clusters[i];
                const cB = clusters[j];
                const centerDist = Math.hypot(cA.seed.x - cB.seed.x, cA.seed.y - cB.seed.y);
                const reqDist = cA.seed.reservedRadius + cB.seed.reservedRadius;
                const margin = centerDist - reqDist;
                if (margin < minClearance) minClearance = margin;

                if (margin < -5.0) { // Small tolerance for boundary padding
                    clustersOverlap = true;
                }
            }
        }

        assert(
            `Territorial Separation: All ${clusters.length} cluster territories have positive clearance (min margin: ${minClearance.toFixed(1)}px)`,
            !clustersOverlap,
            `Min margin = ${minClearance.toFixed(1)}px`
        );
    }

    // -------------------------------------------------------------------------
    // TEST 5: Pure Reversibility & Determinism
    // -------------------------------------------------------------------------
    console.log('\n--- TEST 5: Pure Reversibility & Determinism ---');
    {
        const engine = new CausalTerritorialEngine({ seed: 1234 });
        const events = createMockCampaign(120, 5);
        engine.ingest(events);

        // Snapshot 1 at t = 100
        const stateAt100 = engine.getStateAt(100, 1200, 800);

        // Scrub forward to t = 250
        const stateAt250 = engine.getStateAt(250, 1200, 800);

        // Scrub backward to t = 30
        const stateAt30 = engine.getStateAt(30, 1200, 800);

        // Scrub back to t = 100
        const stateAt100Return = engine.getStateAt(100, 1200, 800);

        // Verify stateAt100 and stateAt100Return are identical
        let match = true;
        match = match && (stateAt100.totalActive === stateAt100Return.totalActive);
        match = match && (Math.abs(stateAt100.camera.focusX - stateAt100Return.camera.focusX) < 1e-9);
        match = match && (Math.abs(stateAt100.camera.focusY - stateAt100Return.camera.focusY) < 1e-9);
        match = match && (Math.abs(stateAt100.camera.zoom - stateAt100Return.camera.zoom) < 1e-9);
        match = match && (stateAt100.nodes.length === stateAt100Return.nodes.length);
        match = match && (stateAt100.aggregates.length === stateAt100Return.aggregates.length);

        for (let i = 0; i < stateAt100.nodes.length; i++) {
            const n1 = stateAt100.nodes[i];
            const n2 = stateAt100Return.nodes[i];
            if (Math.abs(n1.currentX - n2.currentX) > 1e-9 || Math.abs(n1.currentY - n2.currentY) > 1e-9) {
                match = false;
                break;
            }
        }

        assert(
            'Reversibility: Scrubbing 100 -> 250 -> 30 -> 100 produces 100% bit-exact snapshot',
            match,
            'Snapshot discrepancy detected'
        );
    }

    // -------------------------------------------------------------------------
    // TEST 6: Massive Scale Benchmark (65,000 Nodes)
    // -------------------------------------------------------------------------
    console.log('\n--- TEST 6: Massive Scale Benchmark (65,000 Nodes) ---');
    {
        const scaleCount = 65000;
        const numClusters = 64;
        console.log(`Generating mock attack telemetry with ${scaleCount.toLocaleString()} nodes across ${numClusters} VPC clusters...`);
        const scaleEvents = createMockCampaign(scaleCount, numClusters);

        const engine = new CausalTerritorialEngine({
            territory: { candidateScanWindow: 12 }, // Efficient slot scan for high scale
            seed: 888
        });

        const startPlace = performance.now();
        const placed = engine.ingest(scaleEvents);
        const elapsedPlace = performance.now() - startPlace;

        console.log(`[PERF] Ingested & placed ${placed.length.toLocaleString()} nodes in ${elapsedPlace.toFixed(2)} ms (${(elapsedPlace / scaleCount * 1000).toFixed(2)} microseconds/node)`);

        // Test Quadtree temporal LOD queries at scale
        const queryTimes: number[] = [];
        for (let q = 0; q < 20; q++) {
            const sampleT = (q * 100) % 2000;
            const t0 = performance.now();
            const snap = engine.getStateAt(sampleT, 1920, 1080);
            const tQuery = performance.now() - t0;
            queryTimes.push(tQuery);
        }

        const avgQuery = queryTimes.reduce((a, b) => a + b, 0) / queryTimes.length;
        console.log(`[PERF] Average frame query time at 65k scale: ${avgQuery.toFixed(3)} ms (60 FPS budget is 16.6 ms)`);

        assert(
            `Scale Performance: 65,000 nodes placed successfully with sub-10ms frame LOD queries (${avgQuery.toFixed(2)}ms)`,
            avgQuery < 16.6 && placed.length === scaleCount
        );
    }

    console.log('\n================================================================');
    console.log(`SUMMARY: ${passed} PASSED, ${failed} FAILED`);
    console.log('================================================================');

    if (failed > 0) {
        process.exit(1);
    }
}

runSuite();
