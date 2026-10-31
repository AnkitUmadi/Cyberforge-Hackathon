/**
 * Step 1: Causal Vogel (Phyllotaxis) Slot Lattice & Spatial Hash Grid
 *
 * Implements deterministic time-invariant slot generation where adding slot k+1
 * never moves slots 0..k, guaranteeing the prefix property and zero displacement.
 */

export const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5)); // ~2.3999632 rad (137.507764 deg)

export interface Point2D {
    x: number;
    y: number;
}

export interface ClusterSeed extends Point2D {
    id: string;
    phase: number;
    pitch: number;
    reservedRadius: number;
}

export interface NodeEvent {
    id: string;
    cluster: string;
    parent: string | null;
    t: number;
    criticality?: number;
    type?: string;
}

export interface PlacedNode extends Point2D {
    id: string;
    cluster: string;
    parent: string | null;
    budX: number;
    budY: number;
    birthTime: number;
    slotIndex: number;
    criticality: number;
}

/**
 * Deterministic PRNG: Mulberry32
 */
export function mulberry32(a: number): () => number {
    return function() {
        let t = (a += 0x6D2B79F5);
        t = Math.imul(t ^ (t >>> 15), t | 1);
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
}

/**
 * Generates the deterministic Vogel phyllotaxis slot position for index k within a cluster territory.
 */
export function getVogelSlot(seed: ClusterSeed, k: number, pitch?: number): [number, number] {
    const p = pitch ?? seed.pitch;
    const r = p * Math.sqrt(k + 0.5);
    const theta = k * GOLDEN_ANGLE + seed.phase;
    return [
        seed.x + r * Math.cos(theta),
        seed.y + r * Math.sin(theta)
    ];
}

/**
 * 2D Spatial Hash Grid for O(1) overlap checking and neighbor queries.
 */
export class SpatialHashGrid {
    private cellSize: number;
    private grid: Map<number, Array<{ x: number; y: number; id: string }>> = new Map();

    constructor(cellSize: number = 32) {
        this.cellSize = cellSize;
    }

    private hash(cx: number, cy: number): number {
        return (cx * 73856093) ^ (cy * 19349663);
    }

    insert(id: string, x: number, y: number): void {
        const cx = Math.floor(x / this.cellSize);
        const cy = Math.floor(y / this.cellSize);
        const key = this.hash(cx, cy);
        let cell = this.grid.get(key);
        if (!cell) {
            cell = [];
            this.grid.set(key, cell);
        }
        cell.push({ x, y, id });
    }

    hasOverlap(x: number, y: number, minDistance: number): boolean {
        const cx = Math.floor(x / this.cellSize);
        const cy = Math.floor(y / this.cellSize);
        const minSq = minDistance * minDistance;

        // Check 3x3 neighboring cells
        for (let dx = -1; dx <= 1; dx++) {
            for (let dy = -1; dy <= 1; dy++) {
                const key = this.hash(cx + dx, cy + dy);
                const cell = this.grid.get(key);
                if (cell) {
                    for (let i = 0; i < cell.length; i++) {
                        const pt = cell[i];
                        const distSq = (pt.x - x) * (pt.x - x) + (pt.y - y) * (pt.y - y);
                        if (distSq < minSq) {
                            return true;
                        }
                    }
                }
            }
        }
        return false;
    }

    clear(): void {
        this.grid.clear();
    }
}
