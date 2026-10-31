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

export interface FrameSnapshot {
    t: number;
    camera: CameraState;
    viewportBounds: BoundingBox;
    aggregates: CellAggregate[];
    nodes: RenderedNode[];
    tethers: TetherCurve[];
    exploratoryTethers: ExploratoryTetherState[];
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
    public subnetArchetypes: Map<string, SubnetArchetype> = new Map();
    public playbackEngine: PresenterPlaybackEngine | null = null;

    constructor(options: EngineOptions = {}) {
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
        if (lower.includes('dmz') || lower.includes('ingress') || lower.includes('edge') || lower.includes('wan')) {
            return 'PERIMETER_DMZ';
        }
        if (lower.includes('dc') || lower.includes('domain') || lower.includes('auth') || lower.includes('jewel') || lower.includes('vault')) {
            return 'CROWN_JEWELS_AD';
        }
        if (lower.includes('server') || lower.includes('data') || lower.includes('db') || lower.includes('cluster') || lower.includes('k8s') || lower.includes('prod')) {
            return 'SERVER_CLUSTER';
        }
        return 'WORKSTATION_POOL';
    }

    /**
     * Ingests chronological events with heterogeneous archetype placement.
     */
    public ingest(events: NodeEvent[]): PlacedNode[] {
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
                criticality: ev.criticality ?? 0.5
            };

            this.nodes.push(placed);
            this.nodeMap.set(placed.id, placed);
            this.territoryEngine.spatialHash.insert(placed.id, placed.x, placed.y);
            this.territoryEngine.nodes.set(placed.id, placed);
        }

        // Build temporal aggregate quadtree
        this.quadtree = new TemporalAggregateQuadtree(this.nodes);

        // Build Presenter Playback Engine & Forensic Briefings
        this.initPresenterEngine();

        return this.nodes;
    }

    private initPresenterEngine(): void {
        const attackEvents: CausalAttackEvent[] = this.nodes.map((n, i) => {
            const arch = this.subnetArchetypes.get(n.cluster) || 'WORKSTATION_POOL';
            const isCritical = n.criticality >= 0.75 || i === 0 || i === this.nodes.length - 1;

            let tactic: any = 'LATERAL_MOVEMENT';
            let techId = 'T1021.002';
            let techName = 'SMB/Windows Admin Shares';

            if (i === 0) {
                tactic = 'INITIAL_ACCESS';
                techId = 'T1566.001';
                techName = 'Spearphishing Attachment';
            } else if (arch === 'CROWN_JEWELS_AD') {
                tactic = 'IMPACT';
                techId = 'T1003.006';
                techName = 'DCSync / Active Directory Shadow';
            } else if (n.criticality >= 0.8) {
                tactic = 'PRIVILEGE_ESCALATION';
                techId = 'T1068';
                techName = 'Token Elevation via CVE-2024-Exploit';
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

        this.playbackEngine = new PresenterPlaybackEngine(attackEvents);
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

        const halfW = (viewportWidth / 2) / cameraState.zoom;
        const halfH = (viewportHeight / 2) / cameraState.zoom;
        const viewportBounds: BoundingBox = {
            minX: cameraState.focusX - halfW,
            minY: cameraState.focusY - halfH,
            maxX: cameraState.focusX + halfW,
            maxY: cameraState.focusY + halfH
        };

        const lodResult: LODQueryResult = this.quadtree
            ? this.quadtree.query(viewportBounds, t, cameraState.zoom)
            : { aggregates: [], nodes: [], totalActive: 0 };

        const renderedNodes: RenderedNode[] = [];
        const tethers: TetherCurve[] = [];
        const exploratoryTethers: ExploratoryTetherState[] = [];

        for (const vn of lodResult.nodes) {
            const budState = getBudState(vn.node, t);
            if (budState.isBorn) {
                const arch = this.subnetArchetypes.get(vn.node.cluster);
                renderedNodes.push({
                    ...vn.node,
                    currentX: budState.x,
                    currentY: budState.y,
                    scale: budState.scale,
                    progress: budState.progress,
                    isSettling: budState.isSettling,
                    alpha: vn.alpha,
                    archetype: arch
                });

                if (budState.isSettling) {
                    const tether = getTetherCurve(vn.node, t);
                    if (tether) tethers.push(tether);

                    // Also compute 3-phase exploratory probing tether with vanishing curl
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
            wavefront,
            totalActive: lodResult.totalActive,
            totalEstate: this.nodes.length
        };
    }

    /**
     * Pure Canvas 2D render pass with heterogeneous archetypes and exploratory probing tethers.
     */
    public render(
        ctx: any,
        t: number,
        width: number,
        height: number
    ): FrameSnapshot {
        const snapshot = this.getStateAt(t, width, height);

        ctx.fillStyle = '#070b14';
        ctx.fillRect(0, 0, width, height);

        ctx.save();
        ctx.translate(width / 2, height / 2);
        ctx.scale(snapshot.camera.zoom, snapshot.camera.zoom);
        ctx.translate(-snapshot.camera.focusX, -snapshot.camera.focusY);

        // 1. Draw Heterogeneous Territory Boundaries
        for (const [clusterId, territory] of this.territoryEngine.clusters.entries()) {
            const arch = this.subnetArchetypes.get(clusterId) || 'WORKSTATION_POOL';
            const seed = territory.seed;

            ctx.save();
            ctx.setLineDash([4, 6]);

            if (arch === 'PERIMETER_DMZ') {
                // Curvilinear ribbon / boundary fence
                ctx.strokeStyle = 'rgba(56, 189, 248, 0.25)';
                ctx.lineWidth = 1.2 / snapshot.camera.zoom;
                ctx.strokeRect(seed.x - 180, seed.y - 45, 360, 90);
                ctx.fillStyle = '#38bdf8';
                ctx.font = 'bold 9px monospace';
                ctx.fillText(`PERIMETER DMZ FENCE: ${clusterId.toUpperCase()}`, seed.x - 170, seed.y - 52);
            } else if (arch === 'CROWN_JEWELS_AD') {
                // Concentric Bastion Rings + Moat
                ctx.strokeStyle = 'rgba(244, 63, 94, 0.35)';
                ctx.lineWidth = 1.5 / snapshot.camera.zoom;
                ctx.beginPath();
                ctx.arc(seed.x, seed.y, 45, 0, Math.PI * 2);
                ctx.stroke();

                ctx.beginPath();
                ctx.arc(seed.x, seed.y, 105, 0, Math.PI * 2);
                ctx.stroke();

                ctx.fillStyle = '#f43f5e';
                ctx.font = 'bold 9px monospace';
                ctx.fillText(`TIER-0 CROWN MOAT: ${clusterId.toUpperCase()}`, seed.x, seed.y - 114);
            } else if (arch === 'SERVER_CLUSTER') {
                // Server rack aisle grid
                ctx.strokeStyle = 'rgba(168, 85, 247, 0.22)';
                ctx.lineWidth = 1.0 / snapshot.camera.zoom;
                ctx.strokeRect(seed.x - 10, seed.y - 10, 160, 180);
                ctx.fillStyle = '#a855f7';
                ctx.font = 'bold 9px monospace';
                ctx.fillText(`DATACENTER RACK: ${clusterId.toUpperCase()}`, seed.x, seed.y - 18);
            } else {
                // Workstation pool fan
                ctx.strokeStyle = 'rgba(148, 163, 184, 0.18)';
                ctx.lineWidth = 1.0 / snapshot.camera.zoom;
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
            ctx.strokeStyle = 'rgba(239, 68, 68, 0.22)';
            ctx.lineWidth = 2.0 / snapshot.camera.zoom;
            ctx.setLineDash([6, 8]);
            ctx.stroke();
            ctx.restore();
        }

        // 3. Draw Exploratory Probing Tethers & Decoy Tendrils
        for (const exp of snapshot.exploratoryTethers) {
            // Draw decoy feelers
            for (const dec of exp.decoys) {
                ctx.save();
                ctx.beginPath();
                ctx.moveTo(exp.curvePoints[0]?.x || 0, exp.curvePoints[0]?.y || 0);
                ctx.lineTo(dec.currentX, dec.currentY);
                ctx.strokeStyle = dec.isBlocked ? `rgba(239, 68, 68, ${dec.opacity})` : `rgba(148, 163, 184, ${dec.opacity})`;
                ctx.lineWidth = 0.9 / snapshot.camera.zoom;
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
                ctx.lineWidth = (exp.phase === 'SNAP' ? 2.5 : 1.5) / snapshot.camera.zoom;
                ctx.stroke();
                ctx.restore();
            }
        }

        // 4. Draw Aggregates (LOD Supernodes)
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
            ctx.lineWidth = 2.5 / snapshot.camera.zoom;
            ctx.fill();
            ctx.stroke();

            ctx.fillStyle = '#f8fafc';
            ctx.font = `bold ${Math.max(10, 12 / snapshot.camera.zoom)}px monospace`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(`${agg.activeCount}`, agg.centerOfMass.x, agg.centerOfMass.y);
            ctx.restore();
        }

        // 5. Draw Individual Nodes (High LOD)
        for (const n of snapshot.nodes) {
            ctx.save();
            ctx.globalAlpha = n.alpha;

            const r = (n.archetype === 'CROWN_JEWELS_AD' ? 12 : 9) * n.scale;
            if (r > 0.5) {
                let color = '#38bdf8';
                if (n.archetype === 'CROWN_JEWELS_AD') color = '#f43f5e';
                else if (n.criticality >= 0.75) color = '#f59e0b';
                else if (n.archetype === 'SERVER_CLUSTER') color = '#a855f7';

                ctx.beginPath();
                ctx.arc(n.currentX, n.currentY, r, 0, Math.PI * 2);
                ctx.fillStyle = color;
                ctx.fill();
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 1.5 / snapshot.camera.zoom;
                ctx.stroke();

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
