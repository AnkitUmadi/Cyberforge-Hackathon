/**
 * Step 5: Dynamic Gravity Well Camera
 *
 * Implements exponential mass kernel tracking:
 * w_i(t) = exp(-(t - t_i) / tau) * (1 + criticality_i)
 * focus(t) = sum(w_i * x_i) / sum(w_i)
 * Auto-zooms to 90% mass bounding radius with crown-jewel anticipation bias.
 */

import type { PlacedNode, Point2D } from './lattice.ts';

export interface CameraState {
    focusX: number;
    focusY: number;
    zoom: number;
    r90: number;
    activeCount: number;
}

export interface CameraConfig {
    tau: number;                // Cooling decay time constant in minutes (default: 35.0)
    baselineWeight: number;     // Floor weight for established nodes (default: 0.05)
    margin: number;             // Viewport margin in px (default: 120)
    minRadius: number;          // Minimum radius floor to avoid extreme zoom-in (default: 140)
    crownJewelBias: number;     // Bias toward anticipated crown jewel target (default: 0.25)
    minZoom: number;            // Min zoom clamp (default: 0.25)
    maxZoom: number;            // Max zoom clamp (default: 1.6)
}

export const DEFAULT_CAMERA_CONFIG: CameraConfig = {
    tau: 35.0,
    baselineWeight: 0.05,
    margin: 120,
    minRadius: 140,
    crownJewelBias: 0.25,
    minZoom: 0.25,
    maxZoom: 1.6
};

export class GravityWellCamera {
    public config: CameraConfig;

    constructor(config: Partial<CameraConfig> = {}) {
        this.config = { ...DEFAULT_CAMERA_CONFIG, ...config };
    }

    /**
     * Computes the pure closed-form camera position & zoom at time t.
     */
    public getCameraState(
        nodes: PlacedNode[],
        t: number,
        viewportWidth: number,
        viewportHeight: number,
        projectedTargets?: PlacedNode[]
    ): CameraState {
        const activeNodes: PlacedNode[] = [];
        const weights: number[] = [];
        let totalWeight = 0;
        let weightedX = 0;
        let weightedY = 0;

        for (const node of nodes) {
            if (node.birthTime <= t) {
                activeNodes.push(node);
                const deltaT = t - node.birthTime;
                const decay = Math.exp(-deltaT / this.config.tau);
                const w = (decay + this.config.baselineWeight) * (1.0 + node.criticality);
                weights.push(w);
                totalWeight += w;
                weightedX += node.x * w;
                weightedY += node.y * w;
            }
        }

        // If no nodes active yet, frame patient zero or default center
        if (activeNodes.length === 0) {
            const defaultX = nodes.length > 0 ? nodes[0].budX : viewportWidth / 2;
            const defaultY = nodes.length > 0 ? nodes[0].budY : viewportHeight / 2;
            return {
                focusX: defaultX,
                focusY: defaultY,
                zoom: 1.0,
                r90: this.config.minRadius,
                activeCount: 0
            };
        }

        let focusX = weightedX / totalWeight;
        let focusY = weightedY / totalWeight;

        // Crown jewel anticipation: pull focus toward top projected crown jewel
        if (projectedTargets && projectedTargets.length > 0) {
            // Find highest criticality target not yet compromised
            let topTarget: PlacedNode | null = null;
            let maxCrit = -1;
            for (const tgt of projectedTargets) {
                if (tgt.birthTime > t && tgt.criticality > maxCrit) {
                    maxCrit = tgt.criticality;
                    topTarget = tgt;
                }
            }

            if (topTarget && maxCrit >= 0.7) {
                const alpha = this.config.crownJewelBias;
                focusX = (1.0 - alpha) * focusX + alpha * topTarget.x;
                focusY = (1.0 - alpha) * focusY + alpha * topTarget.y;
            }
        }

        // Compute 90th percentile radius from focus
        const distances: number[] = [];
        for (const node of activeNodes) {
            distances.push(Math.hypot(node.x - focusX, node.y - focusY));
        }
        distances.sort((a, b) => a - b);

        const p90Index = Math.floor(distances.length * 0.90);
        const rawR90 = distances[Math.min(distances.length - 1, p90Index)];
        const r90 = Math.max(this.config.minRadius, rawR90);

        // Calculate zoom
        const minViewportDim = Math.min(viewportWidth, viewportHeight);
        const rawZoom = minViewportDim / (2.0 * r90 + this.config.margin);
        const zoom = Math.min(this.config.maxZoom, Math.max(this.config.minZoom, rawZoom));

        return {
            focusX,
            focusY,
            zoom,
            r90,
            activeCount: activeNodes.length
        };
    }
}
