/**
 * Unified Causal Territorial & Stochastic Adversary Replay Engine
 *
 * Integrates:
 * 1. Heterogeneous Subnet Morphologies (morphology.ts):
 *    - Curvilinear Ribbon DMZ fence
 *    - Anisotropic Directed Cone workstation scatter
 *    - Quantized Server Rack / Blade grids
 *    - Concentric Bastion Rings + Moat for Crown Jewels / Active Directory
 * 2. Stochastic Temporal Cadence (stochastic.ts):
 *    - Bounded Lomax / Pareto Type II dwell dormancy gaps
 *    - Marked Hawkes self-exciting cascade bursts (Ogata's thinning)
 *    - Bimodal Zero-Truncated Negative Binomial branching
 * 3. Exploratory Probing Tethers & Decoy Tendrils (tether_exploratory.ts):
 *    - 3-phase emergence with vanishing curl-noise perturbation
 *    - Ephemeral decoy tendrils that flash blocked and retract
 * 4. Presenter-Centric Adaptive Playback Engine (presenter.ts):
 *    - Continuous Asymmetric Narrative Salience Field S(t)
 *    - Auto-deceleration on critical MITRE milestones
 *    - Milestone Hop Stepper API ("Next Critical Hop" / "Previous Critical Hop")
 *    - Forensic Briefing Cards with presenter talking points
 * 5. Interactive Inspection & Anti-Collision Badging:
 *    - High-contrast anti-collision pill badges
 *    - Settled causal infection edges with directional attack flow
 *    - Smooth panning and zooming with interactive entity hit-testing
 */

import type {
    ClusterSeed,
    NodeEvent,
    PlacedNode,
    Point2D
} from './lattice.ts';
import {
    getVogelSlot,
    SpatialHashGrid,
    mulberry32
} from './lattice.ts';
import {
    CausalTerritoryEngine,
    TerritoryCluster,
    DEFAULT_CONFIG
} from './territory.ts';
import type { TerritoryConfig } from './territory.ts';
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
import {
    computeArchetypePosition
} from './morphology.ts';
import type {
    SubnetArchetype,
    EntryVector
} from './morphology.ts';
import {
    sampleLomaxDwell,
    generateHawkesCascade,
    sampleBranchingDegree
} from './stochastic.ts';
import {
    getExploratoryTether
} from './tether_exploratory.ts';
import type {
    ExploratoryTetherState
} from './tether_exploratory.ts';
import {
    PresenterPlaybackEngine
} from './presenter.ts';
import type {
    CausalAttackEvent,
    ForensicBriefingCard,
    StepHopOptions,
    StepHopResult
} from './presenter.ts';

export type { SubnetArchetype, EntryVector } from './morphology.ts';
export { computeArchetypePosition } from './morphology.ts';
export { sampleLomaxDwell, generateHawkesCascade, sampleBranchingDegree } from './stochastic.ts';
export { getExploratoryTether } from './tether_exploratory.ts';
export { PresenterPlaybackEngine } from './presenter.ts';
export { mulberry32 } from './lattice.ts';
export type { CausalAttackEvent, ForensicBriefingCard, StepHopOptions, StepHopResult } from './presenter.ts';

export interface RenderedNode extends PlacedNode {
    currentX: number;
    currentY: number;
    scale: number;
    progress: number;
    isSettling: boolean;
    alpha: number;
    archetype?: SubnetArchetype;
}

export interface SettledEdge {
    sourceId: string;
    targetId: string;
    fromX: number;
    fromY: number;
    toX: number;
    toY: number;
    color: string;
    isCrossSubnet: boolean;
    criticality: number;
    progress: number;
    label?: string;
}

export interface FrameSnapshot {
    t: number;
    camera: CameraState;
    viewportBounds: BoundingBox;
    aggregates: CellAggregate[];
    nodes: RenderedNode[];
    tethers: TetherCurve[];
    exploratoryTethers: ExploratoryTetherState[];
    settledEdges: SettledEdge[];
    wavefront: WavefrontArc;
    totalActive: number;
    totalEstate: number;
}

export interface EngineOptions {
    territory?: Partial<TerritoryConfig>;
    camera?: Partial<CameraConfig>;
    seed?: number;
    patientZero?: Point2D;
    isCausalReplay?: boolean;
}

export class CausalTerritorialEngine {
    public territoryEngine: CausalTerritoryEngine;
    public camera: GravityWellCamera;
    public quadtree: TemporalAggregateQuadtree | null = null;
    public nodes: PlacedNode[] = [];
    public nodeMap: Map<string, PlacedNode> = new Map();
    public events: NodeEvent[] = [];
    public subnetArchetypes: Map<string, SubnetArchetype> = new Map();
    public playbackEngine: PresenterPlaybackEngine | null = null;
    public isCausalReplay: boolean = false;

    // Interactive Camera Transform Overrides
    public panX: number = 0;
    public panY: number = 0;
    public userZoom: number = 1.0;
    public hoverNodeId: string | null = null;
    public selectedNodeId: string | null = null;

    constructor(options: EngineOptions = {}) {
        this.isCausalReplay = options.isCausalReplay ?? false;
        this.territoryEngine = new CausalTerritoryEngine(options.territory, options.seed ?? 1337);
        if (options.patientZero) {
            this.territoryEngine.patientZeroPos = options.patientZero;
        }
        this.camera = new GravityWellCamera(options.camera);
    }

    /**
     * Maps cluster IDs to appropriate subnet archetypes
     */
    public assignSubnetArchetype(clusterId: string): SubnetArchetype {
        const lower = clusterId.toLowerCase();
        if (lower.includes('dmz') || lower.includes('ingress') || lower.includes('edge') || lower.includes('wan') || lower.includes('perimeter')) {
            return 'PERIMETER_DMZ';
        }
        if (lower.includes('dc') || lower.includes('domain') || lower.includes('auth') || lower.includes('jewel') || lower.includes('vault') || lower.includes('99.') || lower.includes('identity')) {
            return 'CROWN_JEWELS_AD';
        }
        if (lower.includes('server') || lower.includes('data') || lower.includes('db') || lower.includes('cluster') || lower.includes('k8s') || lower.includes('prod') || lower.includes('rack')) {
            return 'SERVER_CLUSTER';
        }
        return 'WORKSTATION_POOL';
    }

    /**
     * Ingests chronological events with heterogeneous archetype placement.
     */
    public ingest(events: NodeEvent[], customBriefings?: ForensicBriefingCard[]): PlacedNode[] {
        this.events = [...events].sort((a, b) => a.t - b.t);
        this.nodes = [];
        this.nodeMap.clear();

        const subnetCounts = new Map<string, number>();

        for (const ev of this.events) {
            let arch = this.subnetArchetypes.get(ev.cluster);
            if (!arch) {
                arch = this.assignSubnetArchetype(ev.cluster);
                this.subnetArchetypes.set(ev.cluster, arch);
            }

            const currentIdx = subnetCounts.get(ev.cluster) || 0;
            subnetCounts.set(ev.cluster, currentIdx + 1);

            // Let territory engine spawn cluster if not present
            let cluster = this.territoryEngine.clusters.get(ev.cluster);
            if (!cluster) {
                const parentNode = ev.parent ? this.nodeMap.get(ev.parent) : null;
                cluster = this.territoryEngine.spawnTerritory(ev.cluster, parentNode ? parentNode.cluster : null);
            }

            const parent = ev.parent ? this.nodeMap.get(ev.parent) : null;
            const parentPos: Point2D = parent ? { x: parent.x, y: parent.y } : { x: cluster.seed.x, y: cluster.seed.y };

            const outward = this.territoryEngine.getOutwardVector(parentPos);
            const entryVec: EntryVector = {
                origin: parentPos,
                directionRad: Math.atan2(outward.y, outward.x)
            };

            // Compute coordinate via heterogeneous archetype generator
            const pos = computeArchetypePosition(
                arch,
                currentIdx,
                { x: cluster.seed.x, y: cluster.seed.y },
                parentPos,
                entryVec,
                this.territoryEngine.spatialHash,
                this.territoryEngine.config.minNodeDistance
            );

            const placed: PlacedNode = {
                id: ev.id,
                cluster: ev.cluster,
                parent: ev.parent,
                x: pos.x,
                y: pos.y,
                budX: parentPos.x,
                budY: parentPos.y,
                birthTime: ev.t,
                slotIndex: currentIdx,
                criticality: ev.criticality ?? 0.5,
                type: ev.type,
                label: ev.label,
                mitreTactic: ev.mitreTactic,
                mitreTechId: ev.mitreTechId,
                mitreTechName: ev.mitreTechName,
                evidence: ev.evidence
            };

            this.nodes.push(placed);
            this.nodeMap.set(placed.id, placed);
            this.territoryEngine.spatialHash.insert(placed.id, placed.x, placed.y);
            this.territoryEngine.nodes.set(placed.id, placed);
        }

        // Build temporal aggregate quadtree
        this.quadtree = new TemporalAggregateQuadtree(this.nodes);

        // Build Presenter Playback Engine & Forensic Briefings
        this.initPresenterEngine(customBriefings);

        return this.nodes;
    }

    public initPresenterEngine(customBriefings?: ForensicBriefingCard[]): void {
        const attackEvents: CausalAttackEvent[] = this.nodes.map((n, i) => {
            const arch = this.subnetArchetypes.get(n.cluster) || 'WORKSTATION_POOL';
            const isCritical = n.criticality >= 0.75 || i === 0 || i === this.nodes.length - 1;

            let tactic: any = n.mitreTactic || 'LATERAL_MOVEMENT';
            let techId = n.mitreTechId || 'T1021.002';
            let techName = n.mitreTechName || 'SMB/Windows Admin Shares';

            if (!n.mitreTechName) {
                if (i === 0 || n.type === 'WAN') {
                    tactic = 'INITIAL_ACCESS';
                    techId = 'T1566.001';
                    techName = 'Spearphishing Attachment';
                } else if (arch === 'CROWN_JEWELS_AD' || n.type === 'DC') {
                    tactic = 'IMPACT';
                    techId = 'T1003.006';
                    techName = 'DCSync / Active Directory Shadow';
                } else if (n.type === 'C2') {
                    tactic = 'COMMAND_AND_CONTROL';
                    techId = 'T1071.001';
                    techName = 'Web Protocols (C2 Beacon)';
                } else if (n.type === 'USER' || n.criticality >= 0.8) {
                    tactic = 'CREDENTIAL_ACCESS';
                    techId = 'T1003';
                    techName = 'OS Credential Dumping';
                }
            }

            const parentNode = n.parent ? this.nodeMap.get(n.parent) : null;
            const srcPos = parentNode ? { x: parentNode.x, y: parentNode.y } : { x: n.budX, y: n.budY };

            return {
                eventId: `ev_${n.id}`,
                index: i + 1,
                tSimStart: Math.max(0, n.birthTime - 1.5),
                tSimImpact: n.birthTime,
                sourceNodeId: n.parent || 'PatientZero',
                targetNodeId: n.id,
                subnetId: n.cluster,
                archetype: arch,
                tactic,
                techniqueId: techId,
                techniqueName: techName,
                criticality: n.criticality,
                isCriticalMilestone: isCritical,
                sourcePos: srcPos,
                targetPos: { x: n.x, y: n.y },
                trajectorySeed: 1337 + i * 37,
                decoyTendrils: []
            };
        });

        this.playbackEngine = new PresenterPlaybackEngine(attackEvents, customBriefings);
    }

    /**
     * Coordinate conversions for user interaction
     */
    public screenToWorld(sx: number, sy: number, width: number, height: number, t: number): Point2D {
        const cameraState = this.camera.getCameraState(this.nodes, t, width, height, this.nodes);
        const effZoom = cameraState.zoom * this.userZoom;
        const effFocusX = cameraState.focusX + this.panX;
        const effFocusY = cameraState.focusY + this.panY;

        return {
            x: (sx - width / 2) / effZoom + effFocusX,
            y: (sy - height / 2) / effZoom + effFocusY
        };
    }

    public getNodeAt(sx: number, sy: number, width: number, height: number, t: number): RenderedNode | null {
        const wPos = this.screenToWorld(sx, sy, width, height, t);
        const snapshot = this.getStateAt(t, width, height);

        for (let i = snapshot.nodes.length - 1; i >= 0; i--) {
            const n = snapshot.nodes[i];
            const r = (n.archetype === 'CROWN_JEWELS_AD' || n.type === 'DC' ? 14 : 10) * n.scale + 8;
            const dist = Math.hypot(wPos.x - n.currentX, wPos.y - n.currentY);
            if (dist <= r) {
                return n;
            }
        }
        return null;
    }

    public pan(dx: number, dy: number, width: number, height: number, t: number): void {
        const cameraState = this.camera.getCameraState(this.nodes, t, width, height, this.nodes);
        const effZoom = cameraState.zoom * this.userZoom;
        this.panX -= dx / effZoom;
        this.panY -= dy / effZoom;
    }

    public zoom(factor: number): void {
        this.userZoom = Math.max(0.2, Math.min(6.0, this.userZoom * factor));
    }

    public resetView(): void {
        this.panX = 0;
        this.panY = 0;
        this.userZoom = 1.0;
        this.hoverNodeId = null;
        this.selectedNodeId = null;
    }

    /**
     * Pure frame snapshot at campaign timestamp t.
     */
    public getStateAt(t: number, viewportWidth: number, viewportHeight: number): FrameSnapshot {
        const cameraState = this.camera.getCameraState(
            this.nodes,
            t,
            viewportWidth,
            viewportHeight,
            this.nodes
        );

        const effZoom = cameraState.zoom * this.userZoom;
        const halfW = (viewportWidth / 2) / effZoom;
        const halfH = (viewportHeight / 2) / effZoom;
        const viewportBounds: BoundingBox = {
            minX: cameraState.focusX + this.panX - halfW,
            minY: cameraState.focusY + this.panY - halfH,
            maxX: cameraState.focusX + this.panX + halfW,
            maxY: cameraState.focusY + this.panY + halfH
        };

        const lodResult: LODQueryResult = this.quadtree
            ? this.quadtree.query(viewportBounds, t, effZoom)
            : { aggregates: [], nodes: [], totalActive: 0 };

        const renderedNodes: RenderedNode[] = [];
        const tethers: TetherCurve[] = [];
        const exploratoryTethers: ExploratoryTetherState[] = [];
        const settledEdges: SettledEdge[] = [];

        // Build active position map for fast edge endpoint resolution
        const currentPosMap = new Map<string, { x: number; y: number }>();

        for (const vn of lodResult.nodes) {
            const budState = getBudState(vn.node, t);
            if (budState.isBorn) {
                const arch = this.subnetArchetypes.get(vn.node.cluster);
                const rNode: RenderedNode = {
                    ...vn.node,
                    currentX: budState.x,
                    currentY: budState.y,
                    scale: budState.scale,
                    progress: budState.progress,
                    isSettling: budState.isSettling,
                    alpha: vn.alpha,
                    archetype: arch
                };
                renderedNodes.push(rNode);
                currentPosMap.set(vn.node.id, { x: budState.x, y: budState.y });

                if (budState.isSettling) {
                    const tether = getTetherCurve(vn.node, t);
                    if (tether) tethers.push(tether);

                    // 3-phase exploratory probing tether with vanishing curl
                    const expTether = getExploratoryTether(
                        { x: vn.node.budX, y: vn.node.budY },
                        { x: vn.node.x, y: vn.node.y },
                        t,
                        vn.node.birthTime,
                        8.0,
                        vn.node.slotIndex * 137
                    );
                    if (expTether) exploratoryTethers.push(expTether);
                }

                // If parent exists and is born, record settled causal edge
                if (vn.node.parent) {
                    const parentNode = this.nodeMap.get(vn.node.parent);
                    const isDcTarget = vn.node.archetype === 'CROWN_JEWELS_AD' || vn.node.type === 'DC' || vn.node.cluster.includes('DC');
                    if (parentNode && (t >= parentNode.birthTime || (this.isCausalReplay && isDcTarget))) {
                        const parentBud = getBudState(parentNode, t);
                        let edgeColor = '#38bdf8';
                        
                        if (this.isCausalReplay && isDcTarget) {
                            if (t < vn.node.birthTime) {
                                edgeColor = '#f59e0b'; // 1. First yellow line goes to DC (probing/staging)
                            } else if (t < vn.node.birthTime + 22.0) {
                                edgeColor = '#ef4444'; // 2. Then line changes to red (active intrusion/compromise)
                            } else {
                                edgeColor = '#38bdf8'; // 3. Finally line changes to blue (settled persistent link)
                            }
                        } else if (vn.node.archetype === 'CROWN_JEWELS_AD' || vn.node.type === 'DC') edgeColor = '#f43f5e';
                        else if (vn.node.type === 'C2') edgeColor = '#a855f7';
                        else if (vn.node.type === 'USER') edgeColor = '#f59e0b';
                        else if (vn.node.criticality >= 0.75) edgeColor = '#f59e0b';

                        const toX = budState.isBorn ? budState.x : vn.node.x;
                        const toY = budState.isBorn ? budState.y : vn.node.y;

                        settledEdges.push({
                            sourceId: vn.node.parent,
                            targetId: vn.node.id,
                            fromX: parentBud.x,
                            fromY: parentBud.y,
                            toX: toX,
                            toY: toY,
                            color: edgeColor,
                            isCrossSubnet: parentNode.cluster !== vn.node.cluster,
                            criticality: vn.node.criticality,
                            progress: budState.progress,
                            label: vn.node.mitreTechName
                        });
                    }
                }
            }
        }

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
            exploratoryTethers,
            settledEdges,
            wavefront,
            totalActive: lodResult.totalActive,
            totalEstate: this.nodes.length
        };
    }

    /**
     * Pure Canvas 2D render pass with heterogeneous archetypes, exploratory tethers,
     * settled causal edges, and anti-collision rounded pill badges.
     */
    public render(
        ctx: any,
        t: number,
        width: number,
        height: number
    ): FrameSnapshot {
        const snapshot = this.getStateAt(t, width, height);
        const effZoom = snapshot.camera.zoom * this.userZoom;
        const effFocusX = snapshot.camera.focusX + this.panX;
        const effFocusY = snapshot.camera.focusY + this.panY;

        ctx.fillStyle = '#070b14';
        ctx.fillRect(0, 0, width, height);

        ctx.save();
        ctx.translate(width / 2, height / 2);
        ctx.scale(effZoom, effZoom);
        ctx.translate(-effFocusX, -effFocusY);

        // 1. Draw Heterogeneous Territory Boundaries
        for (const [clusterId, territory] of this.territoryEngine.clusters.entries()) {
            const arch = this.subnetArchetypes.get(clusterId) || 'WORKSTATION_POOL';
            const seed = territory.seed;

            ctx.save();
            ctx.setLineDash([4, 6]);

            if (arch === 'PERIMETER_DMZ') {
                // Curvilinear ribbon / boundary fence
                ctx.strokeStyle = 'rgba(56, 189, 248, 0.28)';
                ctx.lineWidth = 1.2 / effZoom;
                ctx.strokeRect(seed.x - 180, seed.y - 50, 360, 100);
                ctx.fillStyle = '#38bdf8';
                ctx.font = 'bold 9px monospace';
                ctx.fillText(`PERIMETER DMZ FENCE: ${clusterId.toUpperCase()}`, seed.x - 170, seed.y - 58);
            } else if (arch === 'CROWN_JEWELS_AD') {
                // Concentric Bastion Rings + Moat
                ctx.strokeStyle = 'rgba(244, 63, 94, 0.4)';
                ctx.lineWidth = 1.5 / effZoom;
                ctx.beginPath();
                ctx.arc(seed.x, seed.y, 45, 0, Math.PI * 2);
                ctx.stroke();

                ctx.beginPath();
                ctx.arc(seed.x, seed.y, 110, 0, Math.PI * 2);
                ctx.stroke();

                ctx.fillStyle = '#f43f5e';
                ctx.font = 'bold 9px monospace';
                ctx.fillText(`TIER-0 CROWN MOAT: ${clusterId.toUpperCase()}`, seed.x, seed.y - 120);
            } else if (arch === 'SERVER_CLUSTER') {
                // Server rack aisle grid
                ctx.strokeStyle = 'rgba(168, 85, 247, 0.25)';
                ctx.lineWidth = 1.0 / effZoom;
                ctx.strokeRect(seed.x - 10, seed.y - 10, 160, 180);
                ctx.fillStyle = '#a855f7';
                ctx.font = 'bold 9px monospace';
                ctx.fillText(`DATACENTER RACK: ${clusterId.toUpperCase()}`, seed.x, seed.y - 18);
            } else {
                // Workstation pool fan
                ctx.strokeStyle = 'rgba(148, 163, 184, 0.2)';
                ctx.lineWidth = 1.0 / effZoom;
                ctx.beginPath();
                ctx.arc(seed.x, seed.y, seed.reservedRadius, 0, Math.PI * 2);
                ctx.stroke();
                ctx.fillStyle = '#64748b';
                ctx.font = 'bold 9px monospace';
                ctx.fillText(`WORKSTATION POOL: ${clusterId.toUpperCase()}`, seed.x, seed.y - seed.reservedRadius - 6);
            }

            ctx.restore();
        }

        // 2. Draw Causal Wavefront Shockwave Arc
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
            ctx.strokeStyle = 'rgba(239, 68, 68, 0.25)';
            ctx.lineWidth = 2.0 / effZoom;
            ctx.setLineDash([6, 8]);
            ctx.stroke();
            ctx.restore();
        }

        // 3. Draw Settled Causal Edges & Lateral Attack Links
        for (const edge of snapshot.settledEdges) {
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(edge.fromX, edge.fromY);

            // Slight curve for long cross-subnet hops to prevent straight overlaps
            if (edge.isCrossSubnet) {
                const midX = (edge.fromX + edge.toX) / 2;
                const midY = (edge.fromY + edge.toY) / 2 - 25;
                ctx.quadraticCurveTo(midX, midY, edge.toX, edge.toY);
            } else {
                ctx.lineTo(edge.toX, edge.toY);
            }

            ctx.strokeStyle = edge.color;
            ctx.globalAlpha = Math.min(0.85, 0.25 + 0.6 * edge.progress);
            const isThreatEdge = edge.color === '#f59e0b' || edge.color === '#ef4444';
            ctx.lineWidth = (isThreatEdge ? 2.8 : (edge.criticality >= 0.75 ? 2.2 : 1.4)) / effZoom;
            if (edge.isCrossSubnet || isThreatEdge) {
                ctx.setLineDash([6, 4]);
                if (isThreatEdge) {
                    ctx.lineDashOffset = -((t * 18) % 24);
                }
            }
            ctx.stroke();

            // Directional arrow pointer near destination
            const dx = edge.toX - edge.fromX;
            const dy = edge.toY - edge.fromY;
            const len = Math.hypot(dx, dy);
            if (len > 25) {
                const angle = Math.atan2(dy, dx);
                const arrowDist = 18; // offset from target node radius
                const ax = edge.toX - Math.cos(angle) * arrowDist;
                const ay = edge.toY - Math.sin(angle) * arrowDist;
                const headLen = (isThreatEdge ? 9.5 : 6) / effZoom;

                ctx.fillStyle = edge.color;
                ctx.beginPath();
                ctx.moveTo(ax, ay);
                ctx.lineTo(ax - headLen * Math.cos(angle - Math.PI / 5), ay - headLen * Math.sin(angle - Math.PI / 5));
                ctx.lineTo(ax - headLen * Math.cos(angle + Math.PI / 5), ay - headLen * Math.sin(angle + Math.PI / 5));
                ctx.closePath();
                ctx.fill();
            }

            ctx.restore();
        }

        // 4. Draw Exploratory Probing Tethers & Decoy Tendrils (Dynamic Emergence)
        for (const exp of snapshot.exploratoryTethers) {
            // Draw decoy feelers
            for (const dec of exp.decoys) {
                ctx.save();
                ctx.beginPath();
                ctx.moveTo(exp.curvePoints[0]?.x || 0, exp.curvePoints[0]?.y || 0);
                ctx.lineTo(dec.currentX, dec.currentY);
                ctx.strokeStyle = dec.isBlocked ? `rgba(239, 68, 68, ${dec.opacity})` : `rgba(148, 163, 184, ${dec.opacity})`;
                ctx.lineWidth = 0.9 / effZoom;
                ctx.setLineDash([3, 4]);
                ctx.stroke();
                ctx.restore();
            }

            // Draw primary exploratory path with vanishing curl
            if (exp.curvePoints.length > 1) {
                ctx.save();
                ctx.beginPath();
                ctx.moveTo(exp.curvePoints[0].x, exp.curvePoints[0].y);
                for (let i = 1; i < exp.curvePoints.length; i++) {
                    ctx.lineTo(exp.curvePoints[i].x, exp.curvePoints[i].y);
                }
                const color = exp.phase === 'SNAP' ? '#ef4444' : (exp.phase === 'LOCK_ON' ? '#f59e0b' : '#38bdf8');
                ctx.strokeStyle = color;
                ctx.globalAlpha = exp.opacity;
                ctx.lineWidth = (exp.phase === 'SNAP' ? 2.5 : 1.5) / effZoom;
                ctx.stroke();
                ctx.restore();
            }
        }

        // 5. Draw Aggregates (LOD Supernodes when zoomed far out)
        for (const agg of snapshot.aggregates) {
            ctx.save();
            ctx.globalAlpha = agg.alpha;
            const age = t - agg.latestBirthTime;
            const pulse = age < 15 ? 1.0 + 0.15 * Math.sin(age * 2.0) : 1.0;
            const radius = agg.radius * pulse;

            ctx.beginPath();
            ctx.arc(agg.centerOfMass.x, agg.centerOfMass.y, radius, 0, Math.PI * 2);
            ctx.fillStyle = '#1e1b4b';
            ctx.strokeStyle = '#ef4444';
            ctx.lineWidth = 2.5 / effZoom;
            ctx.fill();
            ctx.stroke();

            ctx.fillStyle = '#f8fafc';
            ctx.font = `bold ${Math.max(10, 12 / effZoom)}px monospace`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(`${agg.activeCount}`, agg.centerOfMass.x, agg.centerOfMass.y);
            ctx.restore();
        }

        // 6. Draw Individual Nodes & High-Contrast Anti-Collision Badges (High LOD)
        for (const n of snapshot.nodes) {
            ctx.save();
            ctx.globalAlpha = n.alpha;

            const isCrown = n.archetype === 'CROWN_JEWELS_AD' || n.type === 'DC' || n.cluster.includes('DC');
            const r = (isCrown ? 16 : 12) * n.scale;

            if (r > 0.5) {
                let color = '#38bdf8'; // Host / default
                let typeCode = 'HOST';

                if (isCrown) {
                    if (this.isCausalReplay && t >= n.birthTime + 10.0) {
                        // User request: "and that dc will be become yellow host"
                        color = '#f59e0b'; // Yellow host
                        typeCode = 'HOST';
                    } else if (this.isCausalReplay && t >= n.birthTime) {
                        color = '#ef4444'; // Red active compromise
                        typeCode = 'DC';
                    } else if (this.isCausalReplay) {
                        color = '#f59e0b'; // Probed
                        typeCode = 'DC';
                    } else {
                        color = '#f43f5e';
                        typeCode = 'DC';
                    }
                } else if (n.type === 'C2') {
                    color = '#a855f7';
                    typeCode = 'C2';
                } else if (n.type === 'WAN') {
                    color = '#ef4444';
                    typeCode = 'WAN';
                } else if (n.type === 'USER') {
                    color = '#f59e0b';
                    typeCode = 'USER';
                } else if (n.type === 'PEER') {
                    color = '#64748b';
                    typeCode = 'PEER';
                } else if (n.criticality >= 0.75) {
                    color = '#f59e0b';
                    typeCode = 'HOST';
                }

                const isHovered = n.id === this.hoverNodeId;
                const isSelected = n.id === this.selectedNodeId;
                const nx = Math.round(n.currentX);
                const ny = Math.round(n.currentY);

                // Pulsing highlight ring on hover / selection
                if (isHovered || isSelected) {
                    ctx.beginPath();
                    ctx.arc(nx, ny, r + 6, 0, Math.PI * 2);
                    ctx.strokeStyle = isSelected ? '#38bdf8' : '#f59e0b';
                    ctx.lineWidth = 2.0 / effZoom;
                    ctx.stroke();
                }

                // Node Circle Fill & Stroke
                ctx.beginPath();
                ctx.arc(nx, ny, r, 0, Math.PI * 2);
                ctx.fillStyle = color;
                ctx.fill();
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 1.6 / effZoom;
                ctx.stroke();

                // Concentric inner ring for crown jewels (Tier-0 Domain Controller)
                if (isCrown) {
                    ctx.beginPath();
                    ctx.arc(nx, ny, r * 0.6, 0, Math.PI * 2);
                    ctx.strokeStyle = '#ffffff';
                    ctx.lineWidth = 1.2 / effZoom;
                    ctx.stroke();
                }

                // Settling Shockwave Ripple
                if (n.isSettling) {
                    ctx.beginPath();
                    ctx.arc(nx, ny, r * (1.2 + 0.8 * (1.0 - n.progress)), 0, Math.PI * 2);
                    ctx.strokeStyle = `rgba(245, 158, 11, ${1.0 - n.progress})`;
                    ctx.lineWidth = 1.2 / effZoom;
                    ctx.stroke();
                }

                // Short Type Code Inside Circle
                if (r >= 8) {
                    ctx.fillStyle = '#ffffff';
                    ctx.font = `bold ${Math.max(8, Math.min(11, 9.5 / effZoom))}px monospace`;
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(typeCode, nx, ny);
                }

                // Anti-Collision Dark Rounded Pill Badge Underneath Node
                const isDcCompromisedHost = this.isCausalReplay && isCrown && t >= n.birthTime + 10.0;
                const labelStr = isDcCompromisedHost ? '10.10.99.1 [HOST COMPROMISED]' : (n.label || n.id);
                const timeStr = `T+${Math.round(n.birthTime)}m`;
                const displayStr = `${labelStr} [${timeStr}]`;

                ctx.font = 'bold 10px monospace';
                const strW = ctx.measureText(displayStr).width;
                const badgeW = Math.round(strW + 14);
                const badgeH = 18;
                const badgeX = Math.round(nx - badgeW / 2);
                const badgeY = Math.round(ny + r + 5);

                ctx.fillStyle = 'rgba(9, 14, 26, 0.96)';
                ctx.strokeStyle = isSelected ? '#38bdf8' : (isDcCompromisedHost ? '#f59e0b' : (isCrown ? 'rgba(244, 63, 94, 0.7)' : 'rgba(51, 65, 85, 0.9)'));
                ctx.lineWidth = 1.2 / effZoom;

                if (typeof ctx.roundRect === 'function') {
                    ctx.beginPath();
                    ctx.roundRect(badgeX, badgeY, badgeW, badgeH, 4);
                    ctx.fill();
                    ctx.stroke();
                } else {
                    ctx.fillRect(badgeX, badgeY, badgeW, badgeH);
                    ctx.strokeRect(badgeX, badgeY, badgeW, badgeH);
                }

                ctx.fillStyle = isDcCompromisedHost ? '#fde047' : (isCrown ? '#fca5a5' : '#ffffff');
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(displayStr, nx, badgeY + badgeH / 2);
            }

            ctx.restore();
        }

        ctx.restore();

        return snapshot;
    }
}
