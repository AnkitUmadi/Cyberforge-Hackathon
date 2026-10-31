/**
 * Stochastic Temporal Cadence: Hawkes & Lomax/Pareto Burst Engine
 *
 * Models realistic adversary behavior:
 * - Heavy-tailed Lomax / Pareto Type II dwell dormancy (reconnaissance gaps)
 * - Self-exciting cascades via Ogata's thinning algorithm on Marked Hawkes processes
 * - Bimodal Zero-Truncated Negative Binomial branching (surgical stealth vs mass sweep)
 * - 100% deterministic reproducibility via seeded mulberry32 state forking
 */

import { mulberry32 } from './lattice.ts';

export type OperationalMode = 'STEALTH' | 'SWEEP';

export interface HawkesEventMark {
    t: number;
    alpha: number;
    beta: number;
}

/**
 * 32-bit FNV-1a hash function for deterministic seed derivation.
 */
export function hash32(str: string, seed: number = 0x811c9dc5): number {
    let hval = seed;
    for (let i = 0; i < str.length; i++) {
        hval ^= str.charCodeAt(i);
        hval = Math.imul(hval, 0x01000193);
    }
    return hval >>> 0;
}

/**
 * Samples inter-arrival dwell time from a Lomax / Pareto Type II distribution.
 * Models long-tailed human adversary dormancy between major kill chain phases.
 * Delta t = delta_min + sigma * ((1 - u)^(-1 / alpha) - 1)
 */
export function sampleLomaxDwell(
    u: number,
    alpha: number = 1.6,      // Tail heaviness (1.2 to 2.2)
    sigma: number = 35.0,     // Scale parameter in campaign minutes
    deltaMin: number = 2.0    // Minimum tactical setup gap
): number {
    const safeU = Math.min(0.995, Math.max(0.001, u));
    const dwell = deltaMin + sigma * (Math.pow(1.0 - safeU, -1.0 / alpha) - 1.0);
    return Math.min(180.0, dwell); // Bounded max dwell window (3 hours)
}

/**
 * Deterministic Ogata's Thinning Algorithm for Marked Hawkes Self-Exciting Point Process.
 * Evaluates conditional intensity lambda(t) = mu_0 + sum(alpha_i * beta_i * exp(-beta_i * (t - t_i))).
 */
export function generateHawkesCascade(
    tStart: number,
    tHorizon: number,
    mu0: number,
    activeEvents: HawkesEventMark[],
    prng: () => number,
    maxEvents: number = 40
): number[] {
    const timestamps: number[] = [];
    let t = tStart;

    const evaluateLambda = (time: number): number => {
        let intensity = mu0;
        for (const ev of activeEvents) {
            if (ev.t < time) {
                intensity += ev.alpha * ev.beta * Math.exp(-ev.beta * (time - ev.t));
            }
        }
        return intensity;
    };

    while (t < tHorizon && timestamps.length < maxEvents) {
        // Upper bound M on lambda(s) for s >= t
        const M = Math.max(0.005, evaluateLambda(t));

        const u1 = Math.max(1e-7, prng());
        const dt = -Math.log(u1) / M;
        t += dt;

        if (t >= tHorizon) break;

        const u2 = prng();
        const lambdaCurrent = evaluateLambda(t);

        // Acceptance-rejection thinning step
        if (u2 <= lambdaCurrent / M) {
            timestamps.push(t);
            // Self-excitation mark: newly accepted lateral movement excites future arrivals
            const childAlpha = 1.2 * prng();
            const childBeta = 0.15 + 0.3 * prng();
            activeEvents.push({ t, alpha: childAlpha, beta: childBeta });
        }
    }

    return timestamps;
}

/**
 * Bimodal Zero-Truncated Negative Binomial Branching Factor
 * Decides whether a compromised asset pivots 1-to-1 (stealth) or 1-to-N (spray).
 */
export function sampleBranchingDegree(
    privilegeLevel: number,
    subnetDensity: number,
    prng: () => number
): { degree: number; mode: OperationalMode } {
    // Sigmoid probability of sweep mode
    const logit = 0.8 * privilegeLevel + 0.5 * subnetDensity - 1.8;
    const pSweep = 1.0 / (1.0 + Math.exp(-logit));

    const isSweep = prng() < pSweep;

    if (!isSweep) {
        // STEALTH: surgical 1-to-1 pivot with 15% chance of fork
        const degree = 1 + (prng() < 0.15 ? 1 : 0);
        return { degree, mode: 'STEALTH' };
    } else {
        // SWEEP: automated spray (1-to-N)
        // Approximate negative binomial (r=2, p=0.35)
        const u = prng();
        let degree = 2;
        if (u < 0.4) degree = 2;
        else if (u < 0.7) degree = 3;
        else if (u < 0.9) degree = 4;
        else degree = 5 + Math.floor(prng() * 3);
        return { degree, mode: 'SWEEP' };
    }
}
