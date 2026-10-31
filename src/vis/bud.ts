/**
 * Step 3: Bud & Tether Closed-Form Trajectory & Wavefront Animation
 *
 * Implements deterministic closed-form node emergence:
 * x(t) = bud + (slot - bud) * (1 - (1 - s)^3), s = clamp((t - t_v) / duration)
 * Nodes emerge from parent coordinates at scale 0 and reach their lattice slot
 * along a curved tether over a fixed campaign time window.
 */

import type { PlacedNode, Point2D } from './lattice.ts';

export interface BudState {
    x: number;
    y: number;
    scale: number;       // 0.0 to 1.0
    progress: number;    // s: 0.0 to 1.0
    isBorn: boolean;
    isSettling: boolean; // true while s < 1.0
    tetherOpacity: number;
}

export interface TetherCurve {
    startX: number;
    startY: number;
    controlX: number;
    controlY: number;
    endX: number;
    endY: number;
    width: number;
    opacity: number;
}

export interface WavefrontArc {
    origin: Point2D;
    radius: number;
    activeCount: number;
    latestBirthTime: number;
}

export const DEFAULT_BUD_DURATION = 8.0; // 8 campaign minutes to settle into slot

/**
 * Computes closed-form position and animation metrics for a node at campaign timestamp t.
 */
export function getBudState(node: PlacedNode, t: number, duration: number = DEFAULT_BUD_DURATION): BudState {
    if (t < node.birthTime) {
        return {
            x: node.budX,
            y: node.budY,
            scale: 0.0,
            progress: 0.0,
            isBorn: false,
            isSettling: false,
            tetherOpacity: 0.0
        };
    }

    const elapsed = t - node.birthTime;
    const s = Math.min(1.0, Math.max(0.0, elapsed / duration));
    
    // Ease-out cubic: 1 - (1 - s)^3
    const ease = 1.0 - Math.pow(1.0 - s, 3);

    const currentX = node.budX + (node.x - node.budX) * ease;
    const currentY = node.budY + (node.y - node.budY) * ease;

    const isSettling = s < 1.0;
    const tetherOpacity = Math.max(0.0, 1.0 - s);

    return {
        x: currentX,
        y: currentY,
        scale: ease,
        progress: s,
        isBorn: true,
        isSettling,
        tetherOpacity
    };
}

/**
 * Computes quadratic Bezier tether curve between bud and current position while settling.
 */
export function getTetherCurve(
    node: PlacedNode,
    t: number,
    duration: number = DEFAULT_BUD_DURATION,
    curvatureOffset: number = 0.14
): TetherCurve | null {
    const state = getBudState(node, t, duration);
    if (!state.isBorn || !state.isSettling) {
        return null;
    }

    const startX = node.budX;
    const startY = node.budY;
    const endX = state.x;
    const endY = state.y;

    const dx = endX - startX;
    const dy = endY - startY;

    // Perpendicular offset control point
    const controlX = (startX + endX) / 2 - dy * curvatureOffset;
    const controlY = (startY + endY) / 2 + dx * curvatureOffset;

    return {
        startX,
        startY,
        controlX,
        controlY,
        endX,
        endY,
        width: Math.max(0.5, (1.0 - state.progress) * 2.5),
        opacity: state.tetherOpacity
    };
}

/**
 * Computes expanding causal wavefront arc r_front(t) = max_{t_i <= t} ||x_i - x_0||
 */
export function getInfectionWavefront(
    nodes: Iterable<PlacedNode>,
    t: number,
    origin: Point2D
): WavefrontArc {
    let maxDist = 0;
    let count = 0;
    let latestBirth = -Infinity;

    for (const node of nodes) {
        if (node.birthTime <= t) {
            count++;
            if (node.birthTime > latestBirth) {
                latestBirth = node.birthTime;
            }
            const d = Math.hypot(node.x - origin.x, node.y - origin.y);
            if (d > maxDist) {
                maxDist = d;
            }
        }
    }

    return {
        origin,
        radius: maxDist,
        activeCount: count,
        latestBirthTime: latestBirth
    };
}
