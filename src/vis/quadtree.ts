/**
 * Step 4: Temporal Aggregate Quadtree & Pure LOD Crossfade
 *
 * Implements a spatial tree that precomputes sorted birth timelines and criticality mass.
 * At query time, active node counts n_c(t) are resolved via O(log N) binary search.
 * Level of Detail (LOD) crossfades purely as a function of screen-space pxPitch:
 * pxPitch = (cell_width / sqrt(n_c(t))) * zoom
 * alpha = smoothstep(3, 8, pxPitch)
 * No hysteresis, completely pure and reversible.
 */

import type { PlacedNode, Point2D } from './lattice.ts';

export interface BoundingBox {
    minX: number;
    minY: number;
    maxX: number;
    maxY: number;
}

export function intersects(a: BoundingBox, b: BoundingBox): boolean {
    return !(a.maxX < b.minX || a.minX > b.maxX || a.maxY < b.minY || a.minY > b.maxY);
}

export function smoothstep(edge0: number, edge1: number, x: number): number {
    const t = Math.min(1.0, Math.max(0.0, (x - edge0) / (edge1 - edge0)));
    return t * t * (3.0 - 2.0 * t);
}

/**
 * Binary search for count of events in sorted array with timestamp <= t
 */
export function countActiveBefore(sortedTimestamps: number[], t: number): number {
    let l = 0;
    let r = sortedTimestamps.length;
    while (l < r) {
        const mid = (l + r) >> 1;
        if (sortedTimestamps[mid] <= t) {
            l = mid + 1;
        } else {
            r = mid;
        }
    }
    return l;
}

export interface CellAggregate {
    bounds: BoundingBox;
    centerOfMass: Point2D;
    activeCount: number;
    totalCount: number;
    alpha: number;
    pxPitch: number;
    radius: number;
    crownJewels: PlacedNode[];
    latestBirthTime: number;
}

export interface VisibleNode {
    node: PlacedNode;
    alpha: number;
}

export interface LODQueryResult {
    aggregates: CellAggregate[];
    nodes: VisibleNode[];
    totalActive: number;
}

export class QuadTreeNode {
    public bounds: BoundingBox;
    public nodes: PlacedNode[] = [];
    public births: number[] = [];
    public centerOfMass: Point2D = { x: 0, y: 0 };
    public criticalityMass: number = 0;
    public crownJewels: PlacedNode[] = [];
    public children: QuadTreeNode[] | null = null;
    public isLeaf: boolean = true;

    constructor(bounds: BoundingBox) {
        this.bounds = bounds;
    }

    get width(): number {
        return this.bounds.maxX - this.bounds.minX;
    }

    get height(): number {
        return this.bounds.maxY - this.bounds.minY;
    }
}

export class TemporalAggregateQuadtree {
    public root: QuadTreeNode;
    public maxPerLeaf: number;
    public maxDepth: number;

    constructor(nodes: PlacedNode[], maxPerLeaf: number = 16, maxDepth: number = 8) {
        this.maxPerLeaf = maxPerLeaf;
        this.maxDepth = maxDepth;

        // Compute global bounding box
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        for (const n of nodes) {
            if (n.x < minX) minX = n.x;
            if (n.y < minY) minY = n.y;
            if (n.x > maxX) maxX = n.x;
            if (n.y > maxY) maxY = n.y;
        }

        // Add padding
        const pad = 64;
        minX = isFinite(minX) ? minX - pad : 0;
        minY = isFinite(minY) ? minY - pad : 0;
        maxX = isFinite(maxX) ? maxX + pad : 800;
        maxY = isFinite(maxY) ? maxY + pad : 600;

        // Square the aspect ratio for quadtree stability
        const size = Math.max(maxX - minX, maxY - minY);
        this.root = new QuadTreeNode({
            minX,
            minY,
            maxX: minX + size,
            maxY: minY + size
        });

        // Insert all nodes
        for (const node of nodes) {
            this.insert(this.root, node, 0);
        }

        // Post-process aggregate metrics bottom-up
        this.finalizeMetrics(this.root);
    }

    private insert(cell: QuadTreeNode, node: PlacedNode, depth: number): void {
        cell.nodes.push(node);

        if (cell.isLeaf && (cell.nodes.length <= this.maxPerLeaf || depth >= this.maxDepth)) {
            return;
        }

        if (cell.isLeaf) {
            // Split into 4 quadrants
            cell.isLeaf = false;
            const midX = (cell.bounds.minX + cell.bounds.maxX) / 2;
            const midY = (cell.bounds.minY + cell.bounds.maxY) / 2;

            cell.children = [
                new QuadTreeNode({ minX: cell.bounds.minX, minY: cell.bounds.minY, maxX: midX, maxY: midY }), // NW
                new QuadTreeNode({ minX: midX, minY: cell.bounds.minY, maxX: cell.bounds.maxX, maxY: midY }), // NE
                new QuadTreeNode({ minX: cell.bounds.minX, minY: midY, maxX: midX, maxY: cell.bounds.maxY }), // SW
                new QuadTreeNode({ minX: midX, minY: midY, maxX: cell.bounds.maxX, maxY: cell.bounds.maxY })  // SE
            ];

            // Re-distribute existing nodes to children
            const existingNodes = cell.nodes;
            cell.nodes = [];
            for (const n of existingNodes) {
                this.distributeToChild(cell, n, depth);
            }
        } else {
            this.distributeToChild(cell, node, depth);
        }
    }

    private distributeToChild(cell: QuadTreeNode, node: PlacedNode, depth: number): void {
        if (!cell.children) return;
        const midX = (cell.bounds.minX + cell.bounds.maxX) / 2;
        const midY = (cell.bounds.minY + cell.bounds.maxY) / 2;

        const isEast = node.x >= midX;
        const isSouth = node.y >= midY;
        const idx = (isSouth ? 2 : 0) + (isEast ? 1 : 0);

        this.insert(cell.children[idx], node, depth + 1);
    }

    private finalizeMetrics(cell: QuadTreeNode): void {
        if (cell.children) {
            // Internal node: aggregate from children
            let totalMass = 0;
            let weightedX = 0;
            let weightedY = 0;
            const allBirths: number[] = [];
            const allNodes: PlacedNode[] = [];

            for (const child of cell.children) {
                this.finalizeMetrics(child);
                totalMass += child.criticalityMass;
                weightedX += child.centerOfMass.x * child.criticalityMass;
                weightedY += child.centerOfMass.y * child.criticalityMass;
                for (const b of child.births) allBirths.push(b);
                for (const n of child.crownJewels) allNodes.push(n);
            }

            allBirths.sort((a, b) => a - b);
            cell.births = allBirths;
            cell.criticalityMass = totalMass;
            cell.centerOfMass = totalMass > 0
                ? { x: weightedX / totalMass, y: weightedY / totalMass }
                : { x: (cell.bounds.minX + cell.bounds.maxX) / 2, y: (cell.bounds.minY + cell.bounds.maxY) / 2 };

            // Top-3 crown jewels
            allNodes.sort((a, b) => b.criticality - a.criticality);
            cell.crownJewels = allNodes.slice(0, 3);
        } else {
            // Leaf node: compute directly
            cell.births = cell.nodes.map(n => n.birthTime).sort((a, b) => a - b);
            let totalMass = 0;
            let weightedX = 0;
            let weightedY = 0;

            for (const n of cell.nodes) {
                const w = Math.max(0.1, n.criticality);
                totalMass += w;
                weightedX += n.x * w;
                weightedY += n.y * w;
            }

            cell.criticalityMass = totalMass;
            cell.centerOfMass = totalMass > 0
                ? { x: weightedX / totalMass, y: weightedY / totalMass }
                : { x: (cell.bounds.minX + cell.bounds.maxX) / 2, y: (cell.bounds.minY + cell.bounds.maxY) / 2 };

            const sortedJewels = [...cell.nodes].sort((a, b) => b.criticality - a.criticality);
            cell.crownJewels = sortedJewels.slice(0, 3);
        }
    }

    /**
     * Queries active nodes & aggregates at campaign time t within visible viewport.
     */
    public query(viewport: BoundingBox, t: number, zoom: number): LODQueryResult {
        const aggregates: CellAggregate[] = [];
        const visibleNodes: Map<string, VisibleNode> = new Map();
        let totalActive = 0;

        const traverse = (cell: QuadTreeNode): void => {
            if (!intersects(cell.bounds, viewport)) {
                return;
            }

            const activeCount = countActiveBefore(cell.births, t);
            if (activeCount === 0) {
                return;
            }

            totalActive += (cell.isLeaf ? activeCount : 0);

            // Compute screen-space pixel pitch between nodes in this cell
            const cellWidth = cell.width;
            const pxPitch = (cellWidth / Math.sqrt(activeCount)) * zoom;

            // Pure continuous LOD transition
            if (pxPitch < 3.0 && !cell.isLeaf) {
                // Low LOD: cell rendered as aggregate glyph
                aggregates.push({
                    bounds: cell.bounds,
                    centerOfMass: cell.centerOfMass,
                    activeCount,
                    totalCount: cell.births.length,
                    alpha: 1.0,
                    pxPitch,
                    radius: Math.min(60, Math.max(12, Math.sqrt(activeCount) * 4.0)),
                    crownJewels: cell.crownJewels.filter(n => n.birthTime <= t),
                    latestBirthTime: cell.births[activeCount - 1]
                });
                return;
            }

            if (pxPitch < 8.0 && !cell.isLeaf) {
                // Mid LOD: hybrid aggregate + crown jewels + recent births (< 15 min old)
                const alphaDetail = smoothstep(3.0, 8.0, pxPitch);
                const alphaAgg = 1.0 - alphaDetail;

                if (alphaAgg > 0.05) {
                    aggregates.push({
                        bounds: cell.bounds,
                        centerOfMass: cell.centerOfMass,
                        activeCount,
                        totalCount: cell.births.length,
                        alpha: alphaAgg,
                        pxPitch,
                        radius: Math.min(60, Math.max(12, Math.sqrt(activeCount) * 4.0)),
                        crownJewels: cell.crownJewels.filter(n => n.birthTime <= t),
                        latestBirthTime: cell.births[activeCount - 1]
                    });
                }

                // Recurse to render detail with alphaDetail
                if (cell.children) {
                    for (const child of cell.children) {
                        traverse(child);
                    }
                }
                return;
            }

            // High LOD or Leaf: render individual nodes
            if (cell.children) {
                for (const child of cell.children) {
                    traverse(child);
                }
            } else {
                for (const n of cell.nodes) {
                    if (n.birthTime <= t) {
                        visibleNodes.set(n.id, {
                            node: n,
                            alpha: 1.0
                        });
                    }
                }
            }
        };

        traverse(this.root);

        return {
            aggregates,
            nodes: Array.from(visibleNodes.values()),
            totalActive: countActiveBefore(this.root.births, t)
        };
    }
}
