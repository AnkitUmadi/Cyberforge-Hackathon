/**
 * Presenter-Centric Adaptive Playback & Milestone Hop Stepper Engine
 *
 * Decouples Simulation Time (t) from Wall-Clock Presentation Time (tau).
 * - Continuous Asymmetric Narrative Salience Field S(t) = tanh(sum(c_i * K_asym(t - t_i)))
 * - Auto-decelerates during high-stakes MITRE milestones (privilege escalation, DC compromise)
 * - Auto-Hold on critical milestones (c_i >= 0.85) for demonstration narration
 * - Discrete Milestone Hop Stepper API ("Next Critical Hop" / "Previous Critical Hop")
 * - Generates structured Forensic Briefing Cards with talking points
 */

import type { Point2D } from './lattice.ts';
import type { SubnetArchetype } from './morphology.ts';

export type MitreTactic =
    | 'INITIAL_ACCESS'
    | 'EXECUTION'
    | 'PRIVILEGE_ESCALATION'
    | 'CREDENTIAL_ACCESS'
    | 'LATERAL_MOVEMENT'
    | 'COLLECTION'
    | 'EXFILTRATION'
    | 'IMPACT';

export interface DecoyTendrilSpec {
    targetPos: Point2D;
    phaseSeed: number;
    rejectAtNormalizedU: number;
}

export interface CausalAttackEvent {
    eventId: string;
    index: number;
    tSimStart: number;
    tSimImpact: number;
    sourceNodeId: string;
    targetNodeId: string;
    subnetId: string;
    archetype: SubnetArchetype;
    tactic: MitreTactic;
    techniqueId: string;
    techniqueName: string;
    criticality: number; // 0.0 to 1.0
    isCriticalMilestone: boolean;
    sourcePos: Point2D;
    targetPos: Point2D;
    trajectorySeed: number;
    decoyTendrils: DecoyTendrilSpec[];
}

export interface ForensicBriefingCard {
    hopIndex: number;
    totalCriticalHops: number;
    eventId: string;
    timestampFormatted: string;
    dwellSincePreviousHop: string;
    headline: string;
    mitreBadge: {
        tactic: MitreTactic;
        techniqueId: string;
        techniqueName: string;
    };
    causalLineage: {
        sourceHostname: string;
        sourceIp: string;
        targetHostname: string;
        targetIp: string;
        compromisedCredential?: string;
    };
    blastRadiusStats: {
        downstreamNodesExposed: number;
        cascadeRatePerMin: number;
    };
    presenterTalkingPoints: string[];
}

export interface CameraPose {
    center: Point2D;
    zoom: number;
    framingBounds: { min: Point2D; max: Point2D };
}

export type PlaybackMode =
    | 'ADAPTIVE_NARRATIVE' // Uses S(t) to auto-decelerate on milestones
    | 'CONSTANT_RATIO'     // Fixed ratio
    | 'STEP_HOLD';         // Paused / locked onto a specific milestone

export interface StepHopOptions {
    arrivalStyle: 'ANIMATE_IMPACT' | 'SNAP_COMPLETE';
    cameraTransitionDurationMs?: number;
}

export interface StepHopResult {
    targetEvent: CausalAttackEvent;
    briefingCard: ForensicBriefingCard;
    optimalCameraPose: CameraPose;
    simTimeSetTo: number;
}

export interface IPresenterPlaybackController {
    tick(deltaWallSeconds: number): {
        currentSimTime: number;
        instantaneousWarpRatio: number;
        salienceLevel: number;
        activeBriefing: ForensicBriefingCard | null;
    };
    seekToSimTime(tSim: number): void;
    stepToNextCriticalHop(options?: StepHopOptions): StepHopResult | null;
    stepToPreviousCriticalHop(options?: StepHopOptions): StepHopResult | null;
    jumpToMilestoneByIndex(hopIndex: number, options?: StepHopOptions): StepHopResult;
    getAllCriticalMilestones(): ReadonlyArray<ForensicBriefingCard>;
    setPlaybackMode(mode: PlaybackMode): void;
    setAdaptiveSpeedBounds(vMin: number, vMax: number): void;
}

export class PresenterPlaybackEngine implements IPresenterPlaybackController {
    public currentSimTime = 0;
    public mode: PlaybackMode = 'ADAPTIVE_NARRATIVE';
    public vMin = 0.6;    // 0.6 sim-sec / wall-sec during critical milestones
    public vMax = 120.0;  // 120 sim-sec / wall-sec during dwell gaps
    public gamma = 2.2;   // Deceleration sharpness

    public readonly sigmaLead = 12.0;  // Decelerate 12s before milestone impact
    public readonly sigmaTrail = 35.0; // Hold slower speed 35s after milestone impact

    public readonly milestones: CausalAttackEvent[];
    public readonly briefingMap = new Map<string, ForensicBriefingCard>();

    constructor(
        public readonly allEvents: CausalAttackEvent[],
        briefings: ForensicBriefingCard[] = []
    ) {
        this.milestones = allEvents.filter(e => e.isCriticalMilestone);

        if (briefings.length > 0) {
            for (const card of briefings) {
                this.briefingMap.set(card.eventId, card);
            }
        } else {
            // Auto-generate briefing cards if not provided
            this.generateDefaultBriefings();
        }
    }

    private generateDefaultBriefings(): void {
        this.milestones.forEach((m, idx) => {
            const card: ForensicBriefingCard = {
                hopIndex: idx + 1,
                totalCriticalHops: this.milestones.length,
                eventId: m.eventId,
                timestampFormatted: `T+${Math.floor(m.tSimImpact / 60)}h ${Math.floor(m.tSimImpact % 60)}m`,
                dwellSincePreviousHop: idx === 0 ? "Initial intrusion" : `+${Math.max(1, Math.round(m.tSimStart - this.milestones[idx - 1].tSimImpact))}m dwell gap`,
                headline: `${m.tactic.replace('_', ' ')}: ${m.targetNodeId} Compromised`,
                mitreBadge: {
                    tactic: m.tactic,
                    techniqueId: m.techniqueId,
                    techniqueName: m.techniqueName
                },
                causalLineage: {
                    sourceHostname: m.sourceNodeId,
                    sourceIp: `10.0.${idx + 1}.15`,
                    targetHostname: m.targetNodeId,
                    targetIp: `10.0.${idx + 2}.80`,
                    compromisedCredential: m.criticality >= 0.8 ? "SYSTEM / DomainAdmin" : "LocalAdmin"
                },
                blastRadiusStats: {
                    downstreamNodesExposed: Math.max(2, Math.round(m.criticality * 14)),
                    cascadeRatePerMin: Math.round(m.criticality * 4.2 * 10) / 10
                },
                presenterTalkingPoints: [
                    `Adversary exploited ${m.techniqueName} (${m.techniqueId}) to cross subnet boundary into ${m.subnetId}.`,
                    `Elevated privilege to ${m.criticality >= 0.8 ? 'Domain Admin' : 'Local Admin'} - unlocks lateral credential reuse.`,
                    `Immediate countermeasure: Isolate ${m.targetNodeId} and revoke kerberos session tickets.`
                ]
            };
            this.briefingMap.set(m.eventId, card);
        });
    }

    /**
     * Evaluates continuous Asymmetric Narrative Salience Field S(t) in [0, 1]
     */
    public evaluateSalience(t: number): number {
        let sum = 0;
        for (const ev of this.allEvents) {
            if (ev.criticality < 0.25) continue;
            const dt = t - ev.tSimImpact;
            const sigma = dt < 0 ? this.sigmaLead : this.sigmaTrail;
            if (Math.abs(dt) > 4 * sigma) continue;

            const kernel = Math.exp(-(dt * dt) / (2 * sigma * sigma));
            sum += ev.criticality * kernel;
        }
        return Math.tanh(sum);
    }

    public tick(deltaWallSeconds: number): {
        currentSimTime: number;
        instantaneousWarpRatio: number;
        salienceLevel: number;
        activeBriefing: ForensicBriefingCard | null;
    } {
        if (this.mode === 'STEP_HOLD') {
            return {
                currentSimTime: this.currentSimTime,
                instantaneousWarpRatio: 0,
                salienceLevel: this.evaluateSalience(this.currentSimTime),
                activeBriefing: this.findActiveBriefingAt(this.currentSimTime)
            };
        }

        const salience = this.evaluateSalience(this.currentSimTime);
        const exponent = Math.pow(1.0 - salience, this.gamma);
        const vt = (this.mode === 'ADAPTIVE_NARRATIVE')
            ? this.vMin * Math.pow(this.vMax / this.vMin, exponent)
            : this.vMin * 10.0;

        // 2nd-order Midpoint RK2 numerical integration
        const tMid = this.currentSimTime + 0.5 * deltaWallSeconds * vt;
        const salienceMid = this.evaluateSalience(tMid);
        const vtMid = (this.mode === 'ADAPTIVE_NARRATIVE')
            ? this.vMin * Math.pow(this.vMax / this.vMin, Math.pow(1.0 - salienceMid, this.gamma))
            : vt;

        this.currentSimTime += deltaWallSeconds * vtMid;

        return {
            currentSimTime: this.currentSimTime,
            instantaneousWarpRatio: vtMid,
            salienceLevel: salienceMid,
            activeBriefing: this.findActiveBriefingAt(this.currentSimTime)
        };
    }

    public stepToNextCriticalHop(
        options: StepHopOptions = { arrivalStyle: 'ANIMATE_IMPACT', cameraTransitionDurationMs: 650 }
    ): StepHopResult | null {
        const nextHop = this.milestones.find(m => m.tSimImpact > this.currentSimTime + 0.05);
        if (!nextHop) return null;
        return this.executeHopTransition(nextHop, options);
    }

    public stepToPreviousCriticalHop(
        options: StepHopOptions = { arrivalStyle: 'SNAP_COMPLETE', cameraTransitionDurationMs: 650 }
    ): StepHopResult | null {
        for (let i = this.milestones.length - 1; i >= 0; i--) {
            if (this.milestones[i].tSimStart < this.currentSimTime - 0.5) {
                return this.executeHopTransition(this.milestones[i], options);
            }
        }
        return null;
    }

    public jumpToMilestoneByIndex(hopIndex: number, options?: StepHopOptions): StepHopResult {
        const clamped = Math.max(0, Math.min(this.milestones.length - 1, hopIndex));
        return this.executeHopTransition(
            this.milestones[clamped],
            options ?? { arrivalStyle: 'ANIMATE_IMPACT', cameraTransitionDurationMs: 650 }
        );
    }

    private executeHopTransition(
        target: CausalAttackEvent,
        options: StepHopOptions
    ): StepHopResult {
        this.currentSimTime = (options.arrivalStyle === 'ANIMATE_IMPACT') ? target.tSimStart : target.tSimImpact;
        this.mode = (options.arrivalStyle === 'SNAP_COMPLETE') ? 'STEP_HOLD' : 'ADAPTIVE_NARRATIVE';

        // Camera framing biased 65% toward impact target
        const minX = Math.min(target.sourcePos.x, target.targetPos.x);
        const maxX = Math.max(target.sourcePos.x, target.targetPos.x);
        const minY = Math.min(target.sourcePos.y, target.targetPos.y);
        const maxY = Math.max(target.sourcePos.y, target.targetPos.y);

        const span = Math.max(maxX - minX, maxY - minY, 140);
        const optimalCameraPose: CameraPose = {
            center: {
                x: 0.35 * target.sourcePos.x + 0.65 * target.targetPos.x,
                y: 0.35 * target.sourcePos.y + 0.65 * target.targetPos.y
            },
            zoom: Math.min(2.4, Math.max(0.65, 800 / (span * 1.4))),
            framingBounds: { min: { x: minX, y: minY }, max: { x: maxX, y: maxY } }
        };

        const briefingCard = this.briefingMap.get(target.eventId) || this.milestones[0] as any;
        return {
            targetEvent: target,
            briefingCard,
            optimalCameraPose,
            simTimeSetTo: this.currentSimTime
        };
    }

    private findActiveBriefingAt(t: number): ForensicBriefingCard | null {
        for (let i = this.milestones.length - 1; i >= 0; i--) {
            const m = this.milestones[i];
            if (t >= m.tSimStart && t <= m.tSimImpact + this.sigmaTrail) {
                return this.briefingMap.get(m.eventId) ?? null;
            }
        }
        return null;
    }

    public seekToSimTime(tSim: number): void {
        this.currentSimTime = Math.max(0, tSim);
    }

    public getAllCriticalMilestones(): ReadonlyArray<ForensicBriefingCard> {
        return this.milestones.map(m => this.briefingMap.get(m.eventId)!);
    }

    public setPlaybackMode(mode: PlaybackMode): void {
        this.mode = mode;
    }

    public setAdaptiveSpeedBounds(vMin: number, vMax: number): void {
        this.vMin = vMin;
        this.vMax = vMax;
    }
}
