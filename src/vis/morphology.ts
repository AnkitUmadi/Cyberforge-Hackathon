/**
 * Heterogeneous Subnet Morphologies
 *
 * Replaces isotropic circular sunflower spirals with 4 distinct subnet archetypes
 * while strictly guaranteeing O(1) Prefix Invariance and Zero Displacement:
 * 1. Perimeter / DMZ: Curvilinear Ribbon / Boundary Fence (Halton low-discrepancy)
 * 2. Workstations: Anisotropic Directed Cone + Bridson-style forward scatter
 * 3. Server Clusters: Quantized Rack / Hex-Grid Blade Constellations
 * 4. Active Directory / Crown Jewels: Concentric Tiered Bastion Rings + Buffer Moat
 */

import type { Point2D } from './lattice.ts';
import { SpatialHashGrid } from './lattice.ts';

export type SubnetArchetype =
    | 'PERIMETER_DMZ'
    | 'WORKSTATION_POOL'
    | 'SERVER_CLUSTER'
    | 'CROWN_JEWELS_AD';

export interface EntryVector {
    origin: Point2D;
    directionRad: number;
}

export interface TerritorySeed {
    id: string;
    archetype: SubnetArchetype;
    center: Point2D;
    entry: EntryVector;
    seed: number;
    radius: number;
}

/**
 * 1D Halton low-discrepancy sequence for quasi-random space filling without clustering.
 */
export function halton(index: number, base: number): number {
    let result = 0;
    let f = 1 / base;
    let i = index;
    while (i > 0) {
        result += f * (i % base);
        i = Math.floor(i / base);
        f /= base;
    }
    return result;
}

/**
 * Generates sample from Wrapped Cauchy distribution on [-pi, pi]
 */
export function sampleWrappedCauchy(gamma: number, u: number): number {
    // Inverse CDF of Cauchy distribution wrapped to circle
    const v = Math.PI * (2 * u - 1);
    const sinhG = Math.sinh(gamma);
    const coshG = Math.cosh(gamma);
    return 2 * Math.atan((sinhG * Math.tan(v / 2)) / (coshG + 1));
}

/**
 * 1. Perimeter / DMZ: Curvilinear Ribbon / Boundary Fence
 * Aligned along ingress tangent u_hat and normal n_hat.
 */
export function generateDMZPosition(
    k: number,
    center: Point2D,
    entryVec: EntryVector,
    length: number = 320,
    width: number = 55
): Point2D {
    // Normal is orthogonal to entry direction
    const tangentX = -Math.sin(entryVec.directionRad);
    const tangentY = Math.cos(entryVec.directionRad);
    const normalX = Math.cos(entryVec.directionRad);
    const normalY = Math.sin(entryVec.directionRad);

    const s = length * (halton(k + 1, 2) - 0.5);
    const w = width * (halton(k + 1, 3) - 0.5);
    const sinOffset = 18 * Math.sin(0.02 * s);

    return {
        x: center.x + s * tangentX + (w + sinOffset) * normalX,
        y: center.y + s * tangentY + (w + sinOffset) * normalY
    };
}

/**
 * 2. Workstation / Endpoint: Anisotropic Directed Cone + Outward Scatter
 * Outward lateral propagation from gateway along entry ray.
 */
export function generateWorkstationPosition(
    k: number,
    parentPos: Point2D,
    entryVec: EntryVector,
    minDist: number = 22
): Point2D {
    // Deterministic pseudo-random seed based on index
    const u1 = halton(k + 1, 2);
    const u2 = halton(k + 1, 3);

    // Distance expanding outward from parent: 2.2 * min to 5.0 * min
    const dist = minDist * (2.2 + 2.8 * Math.sqrt(u1));
    // Angular spread centered around entry vector with Cauchy concentration
    const deltaTheta = sampleWrappedCauchy(0.42, u2);
    const angle = entryVec.directionRad + deltaTheta;

    return {
        x: parentPos.x + dist * Math.cos(angle),
        y: parentPos.y + dist * Math.sin(angle)
    };
}

/**
 * 3. Server Clusters / Datacenters: Quantized Rack / Hex-Grid Blades
 * Servers aligned in strict rack aisles with micro-jitter.
 */
export function generateServerRackPosition(
    k: number,
    origin: Point2D,
    bladesPerRack: number = 4,
    racksPerAisle: number = 3,
    dxRack: number = 36,
    dyAisle: number = 48
): Point2D {
    const rackCapacity = bladesPerRack * racksPerAisle;
    const aisle = Math.floor(k / rackCapacity);
    const rackInAisle = Math.floor((k % rackCapacity) / bladesPerRack);
    const blade = k % bladesPerRack;

    const subX = (blade % 2) * 14;
    const subY = Math.floor(blade / 2) * 16;

    // Small deterministic micro-jitter (+/- 2px)
    const jitterX = (halton(k + 1, 5) - 0.5) * 4;
    const jitterY = (halton(k + 1, 7) - 0.5) * 4;

    return {
        x: origin.x + rackInAisle * dxRack + subX + jitterX,
        y: origin.y + aisle * dyAisle + subY + jitterY
    };
}

/**
 * 4. Active Directory / Crown Jewels: Concentric Tiered Bastion Rings + Moat
 * Enforces an empty protective buffer moat around Inner Sanctum Tier-0 DCs.
 */
export function generateCrownJewelPosition(
    k: number,
    center: Point2D,
    innerLimit: number = 3,
    coreRadius: number = 42,
    moatRadius: number = 95,
    spokesPerRing: number = 6,
    ringGap: number = 38
): Point2D {
    if (k < innerLimit) {
        // Inner Sanctum (Tier-0 Domain Controllers)
        const r = coreRadius * Math.sqrt((k + 0.5) / innerLimit);
        const theta = (k * 2 * Math.PI) / innerLimit;
        return {
            x: center.x + r * Math.cos(theta),
            y: center.y + r * Math.sin(theta)
        };
    } else {
        // Outer Bastion Rings (Protected servers / proxies across moat)
        const outerK = k - innerLimit;
        const ringIndex = Math.floor(outerK / spokesPerRing);
        const spokeIndex = outerK % spokesPerRing;

        const r = moatRadius + ringIndex * ringGap;
        const phaseOffset = ringIndex * 0.45; // stagger concentric rings
        const theta = (spokeIndex * 2 * Math.PI) / spokesPerRing + phaseOffset;

        return {
            x: center.x + r * Math.cos(theta),
            y: center.y + r * Math.sin(theta)
        };
    }
}

/**
 * Unified Deterministic Morphological Coordinate Generator
 * Resolves candidate coordinates and applies spatial hash collision probing sequence m = 0, 1, 2...
 */
export function computeArchetypePosition(
    archetype: SubnetArchetype,
    nodeIndexInSubnet: number,
    territoryCenter: Point2D,
    parentPos: Point2D,
    entryVec: EntryVector,
    spatialHash: SpatialHashGrid,
    minClearance: number = 20
): Point2D {
    let probe = 0;
    const maxProbes = 32;

    while (probe < maxProbes) {
        const k = nodeIndexInSubnet + probe;
        let candidate: Point2D;

        switch (archetype) {
            case 'PERIMETER_DMZ':
                candidate = generateDMZPosition(k, territoryCenter, entryVec);
                break;
            case 'WORKSTATION_POOL':
                candidate = generateWorkstationPosition(k, parentPos, entryVec, minClearance);
                break;
            case 'SERVER_CLUSTER':
                candidate = generateServerRackPosition(k, territoryCenter);
                break;
            case 'CROWN_JEWELS_AD':
                candidate = generateCrownJewelPosition(k, territoryCenter);
                break;
            default:
                candidate = generateWorkstationPosition(k, parentPos, entryVec, minClearance);
        }

        // Verify O(1) pairwise clearance
        if (!spatialHash.hasOverlap(candidate.x, candidate.y, minClearance)) {
            return candidate;
        }

        probe++;
    }

    // Fallback outward spiral if all initial probes collided
    const fallbackDist = minClearance * 2.5 + probe * 8;
    const fallbackAngle = probe * 1.618;
    return {
        x: territoryCenter.x + fallbackDist * Math.cos(fallbackAngle),
        y: territoryCenter.y + fallbackDist * Math.sin(fallbackAngle)
    };
}
