/**
 * Exploratory Probing Tethers & Ephemeral Decoy Tendrils
 *
 * Replaces telegraphing straight-line Hermite splines with a 3-phase adversarial emergence:
 * - Phase I: Blind Recon Feeler (u in [0, 0.45])
 * - Phase II: Exploit Lock-On (u in [0.45, 0.85])
 * - Phase III: Breach Snap (u in [0.85, 1.0])
 *
 * Superimposes vanishing curl-noise perturbation W(u) = 16 * u^2 * (1 - u)^3 and
 * ephemeral decoy tendrils that probe neighbor hosts and retract before impact.
 */

import type { Point2D } from './lattice.ts';

export interface DecoyTendril {
    targetX: number;
    targetY: number;
    currentX: number;
    currentY: number;
    reach: number;
    isBlocked: boolean;
    opacity: number;
}

export interface ExploratoryTetherState {
    headX: number;
    headY: number;
    phase: 'RECON' | 'LOCK_ON' | 'SNAP';
    normalizedU: number;
    curvePoints: Point2D[];
    decoys: DecoyTendril[];
    opacity: number;
}

/**
 * Non-linear phase pacing phi(u): Hesitates during recon, snaps on exploit.
 */
export function pacingPhi(u: number): number {
    return 0.25 * u + 0.75 * Math.pow(u, 4);
}

/**
 * Boundary-Safe Envelope W(u): Peaks at u = 0.35, vanishes at u = 0 and u = 1.
 */
export function envelopeW(u: number): number {
    const cl = Math.min(1.0, Math.max(0.0, u));
    return 16.0 * Math.pow(cl, 2) * Math.pow(1.0 - cl, 3);
}

/**
 * Computes 3-octave sinusoidal exploratory curl offset orthogonal to chord.
 */
export function computePerpOffset(u: number, chordLen: number, seed: number = 42): number {
    const w1 = 6.28;
    const w2 = 12.56;
    const w3 = 18.84;
    const p1 = (seed * 0.17) % 6.28;
    const p2 = (seed * 0.43) % 6.28;

    const osc = 0.08 * Math.sin(w1 * u + p1) + 0.04 * Math.sin(w2 * u + p2) + 0.02 * Math.sin(w3 * u);
    return chordLen * osc;
}

/**
 * Computes complete exploratory tether state at campaign timestamp t.
 */
export function getExploratoryTether(
    parentPos: Point2D,
    targetPos: Point2D,
    t: number,
    tSpawn: number,
    duration: number = 8.0,
    seed: number = 1337,
    neighborDecoyTargets: Point2D[] = []
): ExploratoryTetherState | null {
    if (t < tSpawn) return null;

    const elapsed = t - tSpawn;
    const u = Math.min(1.0, Math.max(0.0, elapsed / duration));

    const dx = targetPos.x - parentPos.x;
    const dy = targetPos.y - parentPos.y;
    const chordLen = Math.hypot(dx, dy);

    // Unit tangent and normal vectors
    const tangX = chordLen > 1e-4 ? dx / chordLen : 1;
    const tangY = chordLen > 1e-4 ? dy / chordLen : 0;
    const normX = -tangY;
    const normY = tangX;

    const phi = pacingPhi(u);
    const env = envelopeW(u);
    const dPerp = computePerpOffset(u, chordLen, seed);

    // Base point along chord + vanishing curl
    const baseX = parentPos.x + dx * phi;
    const baseY = parentPos.y + dy * phi;

    const headX = baseX + env * (dPerp * normX);
    const headY = baseY + env * (dPerp * normY);

    let phase: 'RECON' | 'LOCK_ON' | 'SNAP' = 'RECON';
    if (u >= 0.85) phase = 'SNAP';
    else if (u >= 0.45) phase = 'LOCK_ON';

    // Sample path trajectory points for smooth Bezier rendering
    const curvePoints: Point2D[] = [];
    const samples = 16;
    const currentMaxStep = Math.max(2, Math.floor(samples * u));

    for (let i = 0; i <= currentMaxStep; i++) {
        const stepU = (i / samples) * u;
        const stepPhi = pacingPhi(stepU);
        const stepEnv = envelopeW(stepU);
        const stepPerp = computePerpOffset(stepU, chordLen, seed);

        curvePoints.push({
            x: parentPos.x + dx * stepPhi + stepEnv * (stepPerp * normX),
            y: parentPos.y + dy * stepPhi + stepEnv * (stepPerp * normY)
        });
    }

    // Ephemeral Decoy Tendrils during Phase I and early Phase II (u < 0.65)
    const decoys: DecoyTendril[] = [];
    if (u < 0.65 && neighborDecoyTargets.length > 0) {
        const reachProfile = Math.sin(Math.PI * (u / 0.65)) * 0.62;

        for (let m = 0; m < Math.min(3, neighborDecoyTargets.length); m++) {
            const tgt = neighborDecoyTargets[m];
            const decoyCurX = parentPos.x + (tgt.x - parentPos.x) * reachProfile;
            const decoyCurY = parentPos.y + (tgt.y - parentPos.y) * reachProfile;
            const isBlocked = u > 0.35; // flashes blocked before retracting

            decoys.push({
                targetX: tgt.x,
                targetY: tgt.y,
                currentX: decoyCurX,
                currentY: decoyCurY,
                reach: reachProfile,
                isBlocked,
                opacity: (1.0 - u / 0.65) * (isBlocked ? 0.9 : 0.45)
            });
        }
    }

    return {
        headX,
        headY,
        phase,
        normalizedU: u,
        curvePoints,
        decoys,
        opacity: Math.max(0.1, 1.0 - u * 0.85)
    };
}
