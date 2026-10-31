/**
 * Step 6: Causal Territorial Layout Engine Orchestrator
 *
 * Unifies:
 * - Deterministic Vogel phyllotaxis lattice (lattice.ts)
 * - Outward causal territory spawner & discrete slot optimizer (territory.ts)
 * - Closed-form bud & tether trajectory + shockwave wavefront (bud.ts)
 * - Multi-scale temporal aggregate quadtree & pure LOD crossfade (quadtree.ts)
 * - Dynamic gravity well camera with crown-jewel targeting (camera.ts)
 *
 * Guarantees by construction:
 * 1. Prefix property: layout(events[0..k]) === layout(all)[0..k]
 * 2. Zero displacement: Delta x_i(t) = 0 for all t >= t_birth
 * 3. Pairwise no-overlap: min ||x_i - x_j|| >= R_min
 * 4. Territorial clearance: ||s_a - s_b|| >= R_a + R_b
 * 5. Reversibility: scrubber backward produces 100% bit-exact state
 * 6. Massive scale: 65,000+ nodes without performance cliffs
 */

import type {
    ClusterSeed,
    NodeEvent,
    PlacedNode,
    Point2D
} from './lattice.ts';
import {
    getVogelSlot
} from './lattice.ts';
import {
    CausalTerritoryEngine,
    TerritoryCluster,
    DEFAULT_CONFIG
} from './territory.ts';
import type {
    TerritoryConfig
} from './territory.ts';
import {
    getBudState,
    getTetherCurve,
    getInfectionWavefront
} from './bud.ts';
import type {
    BudState,
    TetherCurve,
    WavefrontArc
} from './bud.ts';
import {
    TemporalAggregateQuadtree
} from './quadtree.ts';
import type {
    BoundingBox,
    CellAggregate,
    LODQueryResult,
    VisibleNode
} from './quadtree.ts';
import {
    GravityWellCamera,
    DEFAULT_CAMERA_CONFIG
} from './camera.ts';
import type {
    CameraConfig,
    CameraState
} from './camera.ts';

export interface RenderedNode extends PlacedNode {
    currentX: number;
    currentY: number;
    scale: number;
    progress: number;
    isSettling: boolean;
    alpha: number;
}

export interface FrameSnapshot {
    t: number;
    camera: CameraState;
    viewportBounds: BoundingBox;
    aggregates: CellAggregate[];
    nodes: RenderedNode[];
    tethers: TetherCurve[];
    wavefront: WavefrontArc;
    totalActive: number;
    totalEstate: number;
}

export interface EngineOptions {
    territory?: Partial<TerritoryConfig>;
    camera?: Partial<CameraConfig>;
    seed?: number;
    patientZero?: Point2D;
}

export class CausalTerritorialEngine {
    public territoryEngine: CausalTerritoryEngine;
    public camera: GravityWellCamera;
    public quadtree: TemporalAggregateQuadtree | null = null;
    public nodes: PlacedNode[] = [];
    public nodeMap: Map<string, PlacedNode> = new Map();
    public events: NodeEvent[] = [];

    constructor(options: EngineOptions = {}) {
        this.territoryEngine = new CausalTerritoryEngine(options.territory, options.seed ?? 1337);
        if (options.patientZero) {
            this.territoryEngine.patientZeroPos = options.patientZero;
        }
        this.camera = new GravityWellCamera(options.camera);
    }

    /**
     * Ingests chronological events and calculates deterministic positions.
     */
    public ingest(events: NodeEvent[]): PlacedNode[] {
        // Sort chronologically to preserve causality
        this.events = [...events].sort((a, b) => a.t - b.t);

        this.nodes = [];
        this.nodeMap.clear();

        for (const ev of this.events) {
            const placed = this.territoryEngine.placeNode(ev);
            this.nodes.push(placed);
            this.nodeMap.set(placed.id, placed);
        }

        // Build temporal aggregate quadtree over final node positions
        this.quadtree = new TemporalAggregateQuadtree(this.nodes);

        return this.nodes;
    }

    /**
     * Computes the complete pure frame snapshot at campaign time t.
     */
    public getStateAt(t: number, viewportWidth: number, viewportHeight: number): FrameSnapshot {
        // 1. Dynamic Gravity Well Camera
        const cameraState = this.camera.getCameraState(
            this.nodes,
            t,
            viewportWidth,
            viewportHeight,
            this.nodes
        );

        // 2. Viewport in world space
        const halfW = (viewportWidth / 2) / cameraState.zoom;
        const halfH = (viewportHeight / 2) / cameraState.zoom;
        const viewportBounds: BoundingBox = {
            minX: cameraState.focusX - halfW,
            minY: cameraState.focusY - halfH,
            maxX: cameraState.focusX + halfW,
            maxY: cameraState.focusY + halfH
        };

        // 3. Multi-scale LOD Quadtree Query
        const lodResult: LODQueryResult = this.quadtree
            ? this.quadtree.query(viewportBounds, t, cameraState.zoom)
            : { aggregates: [], nodes: [], totalActive: 0 };

        // 4. Closed-form Bud & Tether Calculation for visible nodes
        const renderedNodes: RenderedNode[] = [];
        const tethers: TetherCurve[] = [];

        for (const vn of lodResult.nodes) {
            const budState = getBudState(vn.node, t);
            if (budState.isBorn) {
                renderedNodes.push({
                    ...vn.node,
                    currentX: budState.x,
                    currentY: budState.y,
                    scale: budState.scale,
                    progress: budState.progress,
                    isSettling: budState.isSettling,
                    alpha: vn.alpha
                });

                if (budState.isSettling) {
                    const tether = getTetherCurve(vn.node, t);
                    if (tether) {
                        tethers.push(tether);
                    }
                }
            }
        }

        // 5. Causal Wavefront Shockwave Arc
        const wavefront = getInfectionWavefront(
            this.nodes,
            t,
            this.territoryEngine.patientZeroPos
        );

        return {
            t,
            camera: cameraState,
            viewportBounds,
            aggregates: lodResult.aggregates,
            nodes: renderedNodes,
            tethers,
            wavefront,
            totalActive: lodResult.totalActive,
            totalEstate: this.nodes.length
        };
    }

    /**
     * Pure Canvas 2D render pass
     */
    public render(
        ctx: any, // CanvasRenderingContext2D
        t: number,
        width: number,
        height: number
    ): FrameSnapshot {
        const snapshot = this.getStateAt(t, width, height);

        // Clear canvas background
        ctx.fillStyle = '#070b14';
        ctx.fillRect(0, 0, width, height);

        // Setup camera transform
        ctx.save();
        ctx.translate(width / 2, height / 2);
        ctx.scale(snapshot.camera.zoom, snapshot.camera.zoom);
        ctx.translate(-snapshot.camera.focusX, -snapshot.camera.focusY);

        // 1. Draw Causal Wavefront Shockwave Arc
        if (snapshot.wavefront.radius > 0) {
            ctx.save();
            ctx.beginPath();
            ctx.arc(
                snapshot.wavefront.origin.x,
                snapshot.wavefront.origin.y,
                snapshot.wavefront.radius,
                0,
                Math.PI * 2
            );
            ctx.strokeStyle = 'rgba(239, 68, 68, 0.22)';
            ctx.lineWidth = 2.0 / snapshot.camera.zoom;
            ctx.setLineDash([6, 8]);
            ctx.stroke();
            ctx.restore();
        }

        // 2. Draw Active Emerging Tethers
        for (const tet of snapshot.tethers) {
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(tet.startX, tet.startY);
            ctx.quadraticCurveTo(tet.controlX, tet.controlY, tet.endX, tet.endY);
            ctx.strokeStyle = `rgba(245, 158, 11, ${tet.opacity * 0.75})`;
            ctx.lineWidth = tet.width / snapshot.camera.zoom;
            ctx.stroke();
            ctx.restore();
        }

        // 3. Draw Aggregates (LOD Supernodes)
        for (const agg of snapshot.aggregates) {
            ctx.save();
            ctx.globalAlpha = agg.alpha;

            // Pulse on recent birth (< 15 min old)
            const age = t - agg.latestBirthTime;
            const pulse = age < 15 ? 1.0 + 0.15 * Math.sin(age * 2.0) : 1.0;
            const radius = agg.radius * pulse;

            // Gradient outer glow
            const grad = ctx.createRadialGradient(
                agg.centerOfMass.x,
                agg.centerOfMass.y,
                2,
                agg.centerOfMass.x,
                agg.centerOfMass.y,
                radius * 1.5
            );
            grad.addColorStop(0, 'rgba(220, 38, 38, 0.45)');
            grad.addColorStop(1, 'rgba(220, 38, 38, 0.0)');
            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.arc(agg.centerOfMass.x, agg.centerOfMass.y, radius * 1.5, 0, Math.PI * 2);
            ctx.fill();

            // Core supernode body
            ctx.beginPath();
            ctx.arc(agg.centerOfMass.x, agg.centerOfMass.y, radius, 0, Math.PI * 2);
            ctx.fillStyle = '#1e1b4b';
            ctx.strokeStyle = '#ef4444';
            ctx.lineWidth = 2.5 / snapshot.camera.zoom;
            ctx.fill();
            ctx.stroke();

            // Supernode label
            ctx.fillStyle = '#f8fafc';
            ctx.font = `bold ${Math.max(10, 12 / snapshot.camera.zoom)}px monospace`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(`${agg.activeCount}`, agg.centerOfMass.x, agg.centerOfMass.y);

            ctx.restore();
        }

        // 4. Draw Individual Nodes (High LOD)
        for (const n of snapshot.nodes) {
            ctx.save();
            ctx.globalAlpha = n.alpha;

            const r = 9 * n.scale;
            if (r > 0.5) {
                // Color by criticality: amber -> red -> purple
                let color = '#38bdf8';
                if (n.criticality >= 0.8) color = '#f43f5e';
                else if (n.criticality >= 0.5) color = '#f59e0b';

                // Core circle
                ctx.beginPath();
                ctx.arc(n.currentX, n.currentY, r, 0, Math.PI * 2);
                ctx.fillStyle = color;
                ctx.fill();
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 1.5 / snapshot.camera.zoom;
                ctx.stroke();

                // Newborn ripple ring if settling
                if (n.isSettling) {
                    ctx.beginPath();
                    ctx.arc(n.currentX, n.currentY, r * (1.2 + 0.8 * (1.0 - n.progress)), 0, Math.PI * 2);
                    ctx.strokeStyle = `rgba(245, 158, 11, ${1.0 - n.progress})`;
                    ctx.lineWidth = 1.0 / snapshot.camera.zoom;
                    ctx.stroke();
                }
            }

            ctx.restore();
        }

        ctx.restore();

        return snapshot;
    }
}
