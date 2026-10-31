/**
 * Step 2: Territory Spawner & Causal Slot Optimizer
 *
 * Implements deterministic territory placement biased outward from patient zero,
 * clearance verification, and discrete slot energy optimization.
 */

import type {
    ClusterSeed,
    NodeEvent,
    PlacedNode,
    Point2D,
} from './lattice.ts';
import {
    SpatialHashGrid,
    getVogelSlot,
    mulberry32
} from './lattice.ts';

export interface TerritoryConfig {
    defaultPitch: number;      // Distance between adjacent sunflower lattice slots (default: 26px)
    nodeRadius: number;        // Physical radius of host node (default: 10px)
    minNodeDistance: number;   // Hard no-overlap threshold (default: 22px)
    idealSpringLength: number; // L0: preferred edge distance from parent (default: 38px)
    betaFlow: number;          // Outward causality alignment weight (default: 1.8)
    gammaOverlap: number;      // Overlap penalty weight (default: 1000.0)
    candidateScanWindow: number; // Scan next W unused slots (default: 48)
    territoryPadding: number;  // Spacing between cluster territories (default: 40px)
}

export const DEFAULT_CONFIG: TerritoryConfig = {
    defaultPitch: 26,
    nodeRadius: 10,
    minNodeDistance: 22,
    idealSpringLength: 38,
    betaFlow: 1.8,
    gammaOverlap: 1000.0,
    candidateScanWindow: 48,
    territoryPadding: 40
};

export class TerritoryCluster {
    public id: string;
    public seed: ClusterSeed;
    public usedSlots: Set<number> = new Set();
    public skippedSlots: Set<number> = new Set();
    public nextSlot: number = 0;
    public memberCount: number = 0;

    constructor(seed: ClusterSeed) {
        this.id = seed.id;
        this.seed = seed;
    }
}

export class CausalTerritoryEngine {
    public clusters: Map<string, TerritoryCluster> = new Map();
    public nodes: Map<string, PlacedNode> = new Map();
    public spatialHash: SpatialHashGrid;
    public config: TerritoryConfig;
    public patientZeroPos: Point2D = { x: 120, y: 280 };
    private rng: () => number;

    constructor(config: Partial<TerritoryConfig> = {}, seedValue: number = 1337) {
        this.config = { ...DEFAULT_CONFIG, ...config };
        this.spatialHash = new SpatialHashGrid(this.config.minNodeDistance * 1.5);
        this.rng = mulberry32(seedValue);
    }

    /**
     * Compute unit vector from patient zero through point p (causal outward ray).
     */
    public getOutwardVector(p: Point2D): Point2D {
        const dx = p.x - this.patientZeroPos.x;
        const dy = p.y - this.patientZeroPos.y;
        const len = Math.hypot(dx, dy);
        if (len < 1e-4) return { x: 1.0, y: 0.0 }; // Default pointing right
        return { x: dx / len, y: dy / len };
    }

    /**
     * Calculate clearance between candidate point and all existing cluster territories.
     */
    public getTerritoryClearance(pt: Point2D): number {
        if (this.clusters.size === 0) return 999999;
        let minClearance = Infinity;
        for (const cl of this.clusters.values()) {
            const d = Math.hypot(pt.x - cl.seed.x, pt.y - cl.seed.y);
            const clear = d - cl.seed.reservedRadius;
            if (clear < minClearance) minClearance = clear;
        }
        return minClearance;
    }

    /**
     * Spawns a new territory for a newly observed cluster (subnet/VPC/domain).
     */
    public spawnTerritory(clusterId: string, parentClusterId?: string | null, expectedSize: number = 32): TerritoryCluster {
        const R = Math.max(
            80,
            1.15 * this.config.defaultPitch * Math.sqrt(Math.max(16, expectedSize))
        );

        let seedX = this.patientZeroPos.x;
        let seedY = this.patientZeroPos.y;

        if (this.clusters.size === 0) {
            // First cluster: root cluster (patient zero origin)
            seedX = this.patientZeroPos.x + 80;
            seedY = this.patientZeroPos.y;
        } else {
            // Determine parent territory reference
            const parentCluster = parentClusterId ? this.clusters.get(parentClusterId) : null;
            const refSeed = parentCluster ? parentCluster.seed : Array.from(this.clusters.values())[0].seed;
            const outward = this.getOutwardVector(refSeed);

            // Generate candidate points in expanding radial rings biased outward
            const candidates: Point2D[] = [];
            const ringDist = refSeed.reservedRadius + R + this.config.territoryPadding;

            // Generate 16 angular candidate points around reference territory
            const refAngle = Math.atan2(outward.y, outward.x);
            for (let i = -4; i <= 4; i++) {
                const angle = refAngle + (i * Math.PI) / 6; // Arc +/- 120 degrees outward
                candidates.push({
                    x: refSeed.x + ringDist * Math.cos(angle),
                    y: refSeed.y + ringDist * Math.sin(angle)
                });
            }

            // Select candidate with best clearance and minimum backflow toward patient zero
            let bestCand: Point2D = candidates[0];
            let bestScore = Infinity;

            for (const c of candidates) {
                const clear = this.getTerritoryClearance(c);
                if (clear < R + this.config.territoryPadding * 0.5) continue; // Collision

                // Score = distance to parent + penalty for pointing back toward patient zero
                const distToParent = Math.hypot(c.x - refSeed.x, c.y - refSeed.y);
                const backflow = Math.max(0, -((c.x - refSeed.x) * outward.x + (c.y - refSeed.y) * outward.y));
                const score = distToParent + 3.0 * backflow;

                if (score < bestScore) {
                    bestScore = score;
                    bestCand = c;
                }
            }

            seedX = bestCand.x;
            seedY = bestCand.y;
        }

        const seed: ClusterSeed = {
            id: clusterId,
            x: seedX,
            y: seedY,
            phase: this.rng() * Math.PI * 2,
            pitch: this.config.defaultPitch,
            reservedRadius: R
        };

        const territory = new TerritoryCluster(seed);
        this.clusters.set(clusterId, territory);
        return territory;
    }

    /**
     * Discrete Slot Optimizer: Places a node in an optimal unused Vogel slot without moving established nodes.
     */
    public placeNode(event: NodeEvent): PlacedNode {
        // If already placed, return existing time-invariant coordinates
        const existing = this.nodes.get(event.id);
        if (existing) return existing;

        let cluster = this.clusters.get(event.cluster);
        if (!cluster) {
            const parentNode = event.parent ? this.nodes.get(event.parent) : null;
            cluster = this.spawnTerritory(event.cluster, parentNode ? parentNode.cluster : null);
        }

        const parent = event.parent ? this.nodes.get(event.parent) : null;
        const budPos: Point2D = parent ? { x: parent.x, y: parent.y } : { x: cluster.seed.x, y: cluster.seed.y };
        const outward = this.getOutwardVector(budPos);

        let bestSlot = -1;
        let bestEnergy = Infinity;

        // Helper to evaluate a candidate slot index against physics & hard overlap constraint
        const evaluateSlot = (slotIdx: number): boolean => {
            if (cluster.usedSlots.has(slotIdx)) return false;

            const [sx, sy] = getVogelSlot(cluster.seed, slotIdx, cluster.seed.pitch);

            // Hard invariant: reject any slot that overlaps with an existing node
            if (this.spatialHash.hasOverlap(sx, sy, this.config.minNodeDistance)) {
                return false;
            }

            // 1. Topology stress: distance from parent
            const d = Math.hypot(sx - budPos.x, sy - budPos.y);
            const topoStress = Math.pow(d - this.config.idealSpringLength, 2);

            // 2. Causality flow: projection along outward ray from patient zero
            const proj = (sx - budPos.x) * outward.x + (sy - budPos.y) * outward.y;
            const flowPenalty = Math.pow(Math.max(0, 10.0 - proj), 2);

            const energy = topoStress + this.config.betaFlow * flowPenalty;

            if (energy < bestEnergy) {
                bestEnergy = energy;
                bestSlot = slotIdx;
            }
            return true;
        };

        // 1. Check a bounded number of previously skipped slots in this cluster
        let skippedChecked = 0;
        for (const s of cluster.skippedSlots) {
            if (skippedChecked++ >= 6) break;
            evaluateSlot(s);
        }

        // 2. Scan next slots starting from cluster.nextSlot
        let validCandidates = 0;
        let k = cluster.nextSlot;

        while (validCandidates < this.config.candidateScanWindow || bestSlot === -1) {
            if (evaluateSlot(k)) {
                validCandidates++;
            }
            k++;
        }

        // Commit slot
        cluster.usedSlots.add(bestSlot);
        if (cluster.skippedSlots.has(bestSlot)) {
            cluster.skippedSlots.delete(bestSlot);
        } else {
            // Any slot from nextSlot up to bestSlot that was passed over is added to skippedSlots
            for (let s = cluster.nextSlot; s < bestSlot; s++) {
                if (!cluster.usedSlots.has(s) && cluster.skippedSlots.size < 64) {
                    cluster.skippedSlots.add(s);
                }
            }
            cluster.nextSlot = Math.max(cluster.nextSlot, bestSlot + 1);
        }
        cluster.memberCount++;

        const [finalX, finalY] = getVogelSlot(cluster.seed, bestSlot, cluster.seed.pitch);

        const placed: PlacedNode = {
            id: event.id,
            cluster: event.cluster,
            parent: event.parent,
            x: finalX,
            y: finalY,
            budX: budPos.x,
            budY: budPos.y,
            birthTime: event.t,
            slotIndex: bestSlot,
            criticality: event.criticality ?? 0.5
        };

        this.nodes.set(event.id, placed);
        this.spatialHash.insert(event.id, finalX, finalY);

        return placed;
    }
}
