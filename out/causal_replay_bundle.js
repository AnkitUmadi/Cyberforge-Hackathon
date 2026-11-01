var CausalReplay = (() => {
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __export = (target, all) => {
    for (var name in all)
      __defProp(target, name, { get: all[name], enumerable: true });
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

  // src/vis/engine.ts
  var engine_exports = {};
  __export(engine_exports, {
    CausalTerritorialEngine: () => CausalTerritorialEngine,
    PresenterPlaybackEngine: () => PresenterPlaybackEngine,
    computeArchetypePosition: () => computeArchetypePosition,
    generateHawkesCascade: () => generateHawkesCascade,
    getExploratoryTether: () => getExploratoryTether,
    mulberry32: () => mulberry32,
    sampleBranchingDegree: () => sampleBranchingDegree,
    sampleLomaxDwell: () => sampleLomaxDwell
  });

  // src/vis/lattice.ts
  var GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));
  function mulberry32(a) {
    return function() {
      let t = a += 1831565813;
      t = Math.imul(t ^ t >>> 15, t | 1);
      t ^= t + Math.imul(t ^ t >>> 7, t | 61);
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  function getVogelSlot(seed, k, pitch) {
    const p = pitch ?? seed.pitch;
    const r = p * Math.sqrt(k + 0.5);
    const theta = k * GOLDEN_ANGLE + seed.phase;
    return [
      seed.x + r * Math.cos(theta),
      seed.y + r * Math.sin(theta)
    ];
  }
  var SpatialHashGrid = class {
    cellSize;
    grid = /* @__PURE__ */ new Map();
    constructor(cellSize = 32) {
      this.cellSize = cellSize;
    }
    hash(cx, cy) {
      return cx * 73856093 ^ cy * 19349663;
    }
    insert(id, x, y) {
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
    hasOverlap(x, y, minDistance) {
      const cx = Math.floor(x / this.cellSize);
      const cy = Math.floor(y / this.cellSize);
      const minSq = minDistance * minDistance;
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
    clear() {
      this.grid.clear();
    }
  };

  // src/vis/territory.ts
  var DEFAULT_CONFIG = {
    defaultPitch: 26,
    nodeRadius: 10,
    minNodeDistance: 22,
    idealSpringLength: 38,
    betaFlow: 1.8,
    gammaOverlap: 1e3,
    candidateScanWindow: 48,
    territoryPadding: 40
  };
  var TerritoryCluster = class {
    id;
    seed;
    usedSlots = /* @__PURE__ */ new Set();
    skippedSlots = /* @__PURE__ */ new Set();
    nextSlot = 0;
    memberCount = 0;
    constructor(seed) {
      this.id = seed.id;
      this.seed = seed;
    }
  };
  var CausalTerritoryEngine = class {
    clusters = /* @__PURE__ */ new Map();
    nodes = /* @__PURE__ */ new Map();
    spatialHash;
    config;
    patientZeroPos = { x: 120, y: 280 };
    rng;
    constructor(config = {}, seedValue = 1337) {
      this.config = { ...DEFAULT_CONFIG, ...config };
      this.spatialHash = new SpatialHashGrid(this.config.minNodeDistance * 1.5);
      this.rng = mulberry32(seedValue);
    }
    /**
     * Compute unit vector from patient zero through point p (causal outward ray).
     */
    getOutwardVector(p) {
      const dx = p.x - this.patientZeroPos.x;
      const dy = p.y - this.patientZeroPos.y;
      const len = Math.hypot(dx, dy);
      if (len < 1e-4) return { x: 1, y: 0 };
      return { x: dx / len, y: dy / len };
    }
    /**
     * Calculate clearance between candidate point and all existing cluster territories.
     */
    getTerritoryClearance(pt) {
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
    spawnTerritory(clusterId, parentClusterId, expectedSize = 32) {
      const R = Math.max(
        80,
        1.15 * this.config.defaultPitch * Math.sqrt(Math.max(16, expectedSize))
      );
      let seedX = this.patientZeroPos.x;
      let seedY = this.patientZeroPos.y;
      if (this.clusters.size === 0) {
        seedX = this.patientZeroPos.x + 80;
        seedY = this.patientZeroPos.y;
      } else {
        const parentCluster = parentClusterId ? this.clusters.get(parentClusterId) : null;
        const refSeed = parentCluster ? parentCluster.seed : Array.from(this.clusters.values())[0].seed;
        const outward = this.getOutwardVector(refSeed);
        const candidates = [];
        const ringDist = refSeed.reservedRadius + R + this.config.territoryPadding;
        const refAngle = Math.atan2(outward.y, outward.x);
        for (let i = -4; i <= 4; i++) {
          const angle = refAngle + i * Math.PI / 6;
          candidates.push({
            x: refSeed.x + ringDist * Math.cos(angle),
            y: refSeed.y + ringDist * Math.sin(angle)
          });
        }
        let bestCand = candidates[0];
        let bestScore = Infinity;
        for (const c of candidates) {
          const clear = this.getTerritoryClearance(c);
          if (clear < R + this.config.territoryPadding * 0.5) continue;
          const distToParent = Math.hypot(c.x - refSeed.x, c.y - refSeed.y);
          const backflow = Math.max(0, -((c.x - refSeed.x) * outward.x + (c.y - refSeed.y) * outward.y));
          const score = distToParent + 3 * backflow;
          if (score < bestScore) {
            bestScore = score;
            bestCand = c;
          }
        }
        seedX = bestCand.x;
        seedY = bestCand.y;
      }
      const seed = {
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
    placeNode(event) {
      const existing = this.nodes.get(event.id);
      if (existing) return existing;
      let cluster = this.clusters.get(event.cluster);
      if (!cluster) {
        const parentNode = event.parent ? this.nodes.get(event.parent) : null;
        cluster = this.spawnTerritory(event.cluster, parentNode ? parentNode.cluster : null);
      }
      const parent = event.parent ? this.nodes.get(event.parent) : null;
      const budPos = parent ? { x: parent.x, y: parent.y } : { x: cluster.seed.x, y: cluster.seed.y };
      const outward = this.getOutwardVector(budPos);
      let bestSlot = -1;
      let bestEnergy = Infinity;
      const evaluateSlot = (slotIdx) => {
        if (cluster.usedSlots.has(slotIdx)) return false;
        const [sx, sy] = getVogelSlot(cluster.seed, slotIdx, cluster.seed.pitch);
        if (this.spatialHash.hasOverlap(sx, sy, this.config.minNodeDistance)) {
          return false;
        }
        const d = Math.hypot(sx - budPos.x, sy - budPos.y);
        const topoStress = Math.pow(d - this.config.idealSpringLength, 2);
        const proj = (sx - budPos.x) * outward.x + (sy - budPos.y) * outward.y;
        const flowPenalty = Math.pow(Math.max(0, 10 - proj), 2);
        const energy = topoStress + this.config.betaFlow * flowPenalty;
        if (energy < bestEnergy) {
          bestEnergy = energy;
          bestSlot = slotIdx;
        }
        return true;
      };
      let skippedChecked = 0;
      for (const s of cluster.skippedSlots) {
        if (skippedChecked++ >= 6) break;
        evaluateSlot(s);
      }
      let validCandidates = 0;
      let k = cluster.nextSlot;
      while (validCandidates < this.config.candidateScanWindow || bestSlot === -1) {
        if (evaluateSlot(k)) {
          validCandidates++;
        }
        k++;
      }
      cluster.usedSlots.add(bestSlot);
      if (cluster.skippedSlots.has(bestSlot)) {
        cluster.skippedSlots.delete(bestSlot);
      } else {
        for (let s = cluster.nextSlot; s < bestSlot; s++) {
          if (!cluster.usedSlots.has(s) && cluster.skippedSlots.size < 64) {
            cluster.skippedSlots.add(s);
          }
        }
        cluster.nextSlot = Math.max(cluster.nextSlot, bestSlot + 1);
      }
      cluster.memberCount++;
      const [finalX, finalY] = getVogelSlot(cluster.seed, bestSlot, cluster.seed.pitch);
      const placed = {
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
  };

  // src/vis/bud.ts
  var DEFAULT_BUD_DURATION = 8;
  function getBudState(node, t, duration = DEFAULT_BUD_DURATION) {
    if (t < node.birthTime) {
      return {
        x: node.budX,
        y: node.budY,
        scale: 0,
        progress: 0,
        isBorn: false,
        isSettling: false,
        tetherOpacity: 0
      };
    }
    const elapsed = t - node.birthTime;
    const s = Math.min(1, Math.max(0, elapsed / duration));
    const ease = 1 - Math.pow(1 - s, 3);
    const currentX = node.budX + (node.x - node.budX) * ease;
    const currentY = node.budY + (node.y - node.budY) * ease;
    const isSettling = s < 1;
    const tetherOpacity = Math.max(0, 1 - s);
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
  function getTetherCurve(node, t, duration = DEFAULT_BUD_DURATION, curvatureOffset = 0.14) {
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
    const controlX = (startX + endX) / 2 - dy * curvatureOffset;
    const controlY = (startY + endY) / 2 + dx * curvatureOffset;
    return {
      startX,
      startY,
      controlX,
      controlY,
      endX,
      endY,
      width: Math.max(0.5, (1 - state.progress) * 2.5),
      opacity: state.tetherOpacity
    };
  }
  function getInfectionWavefront(nodes, t, origin) {
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

  // src/vis/quadtree.ts
  function intersects(a, b) {
    return !(a.maxX < b.minX || a.minX > b.maxX || a.maxY < b.minY || a.minY > b.maxY);
  }
  function smoothstep(edge0, edge1, x) {
    const t = Math.min(1, Math.max(0, (x - edge0) / (edge1 - edge0)));
    return t * t * (3 - 2 * t);
  }
  function countActiveBefore(sortedTimestamps, t) {
    let l = 0;
    let r = sortedTimestamps.length;
    while (l < r) {
      const mid = l + r >> 1;
      if (sortedTimestamps[mid] <= t) {
        l = mid + 1;
      } else {
        r = mid;
      }
    }
    return l;
  }
  var QuadTreeNode = class {
    bounds;
    nodes = [];
    births = [];
    centerOfMass = { x: 0, y: 0 };
    criticalityMass = 0;
    crownJewels = [];
    children = null;
    isLeaf = true;
    constructor(bounds) {
      this.bounds = bounds;
    }
    get width() {
      return this.bounds.maxX - this.bounds.minX;
    }
    get height() {
      return this.bounds.maxY - this.bounds.minY;
    }
  };
  var TemporalAggregateQuadtree = class {
    root;
    maxPerLeaf;
    maxDepth;
    constructor(nodes, maxPerLeaf = 16, maxDepth = 8) {
      this.maxPerLeaf = maxPerLeaf;
      this.maxDepth = maxDepth;
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      for (const n of nodes) {
        if (n.x < minX) minX = n.x;
        if (n.y < minY) minY = n.y;
        if (n.x > maxX) maxX = n.x;
        if (n.y > maxY) maxY = n.y;
      }
      const pad = 64;
      minX = isFinite(minX) ? minX - pad : 0;
      minY = isFinite(minY) ? minY - pad : 0;
      maxX = isFinite(maxX) ? maxX + pad : 800;
      maxY = isFinite(maxY) ? maxY + pad : 600;
      const size = Math.max(maxX - minX, maxY - minY);
      this.root = new QuadTreeNode({
        minX,
        minY,
        maxX: minX + size,
        maxY: minY + size
      });
      for (const node of nodes) {
        this.insert(this.root, node, 0);
      }
      this.finalizeMetrics(this.root);
    }
    insert(cell, node, depth) {
      cell.nodes.push(node);
      if (cell.isLeaf && (cell.nodes.length <= this.maxPerLeaf || depth >= this.maxDepth)) {
        return;
      }
      if (cell.isLeaf) {
        cell.isLeaf = false;
        const midX = (cell.bounds.minX + cell.bounds.maxX) / 2;
        const midY = (cell.bounds.minY + cell.bounds.maxY) / 2;
        cell.children = [
          new QuadTreeNode({ minX: cell.bounds.minX, minY: cell.bounds.minY, maxX: midX, maxY: midY }),
          // NW
          new QuadTreeNode({ minX: midX, minY: cell.bounds.minY, maxX: cell.bounds.maxX, maxY: midY }),
          // NE
          new QuadTreeNode({ minX: cell.bounds.minX, minY: midY, maxX: midX, maxY: cell.bounds.maxY }),
          // SW
          new QuadTreeNode({ minX: midX, minY: midY, maxX: cell.bounds.maxX, maxY: cell.bounds.maxY })
          // SE
        ];
        const existingNodes = cell.nodes;
        cell.nodes = [];
        for (const n of existingNodes) {
          this.distributeToChild(cell, n, depth);
        }
      } else {
        this.distributeToChild(cell, node, depth);
      }
    }
    distributeToChild(cell, node, depth) {
      if (!cell.children) return;
      const midX = (cell.bounds.minX + cell.bounds.maxX) / 2;
      const midY = (cell.bounds.minY + cell.bounds.maxY) / 2;
      const isEast = node.x >= midX;
      const isSouth = node.y >= midY;
      const idx = (isSouth ? 2 : 0) + (isEast ? 1 : 0);
      this.insert(cell.children[idx], node, depth + 1);
    }
    finalizeMetrics(cell) {
      if (cell.children) {
        let totalMass = 0;
        let weightedX = 0;
        let weightedY = 0;
        const allBirths = [];
        const allNodes = [];
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
        cell.centerOfMass = totalMass > 0 ? { x: weightedX / totalMass, y: weightedY / totalMass } : { x: (cell.bounds.minX + cell.bounds.maxX) / 2, y: (cell.bounds.minY + cell.bounds.maxY) / 2 };
        allNodes.sort((a, b) => b.criticality - a.criticality);
        cell.crownJewels = allNodes.slice(0, 3);
      } else {
        cell.births = cell.nodes.map((n) => n.birthTime).sort((a, b) => a - b);
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
        cell.centerOfMass = totalMass > 0 ? { x: weightedX / totalMass, y: weightedY / totalMass } : { x: (cell.bounds.minX + cell.bounds.maxX) / 2, y: (cell.bounds.minY + cell.bounds.maxY) / 2 };
        const sortedJewels = [...cell.nodes].sort((a, b) => b.criticality - a.criticality);
        cell.crownJewels = sortedJewels.slice(0, 3);
      }
    }
    /**
     * Queries active nodes & aggregates at campaign time t within visible viewport.
     */
    query(viewport, t, zoom) {
      const aggregates = [];
      const visibleNodes = /* @__PURE__ */ new Map();
      let totalActive = 0;
      const traverse = (cell) => {
        if (!intersects(cell.bounds, viewport)) {
          return;
        }
        const activeCount = countActiveBefore(cell.births, t);
        if (activeCount === 0) {
          return;
        }
        totalActive += cell.isLeaf ? activeCount : 0;
        const cellWidth = cell.width;
        const pxPitch = cellWidth / Math.sqrt(activeCount) * zoom;
        if (pxPitch < 3 && !cell.isLeaf) {
          aggregates.push({
            bounds: cell.bounds,
            centerOfMass: cell.centerOfMass,
            activeCount,
            totalCount: cell.births.length,
            alpha: 1,
            pxPitch,
            radius: Math.min(60, Math.max(12, Math.sqrt(activeCount) * 4)),
            crownJewels: cell.crownJewels.filter((n) => n.birthTime <= t),
            latestBirthTime: cell.births[activeCount - 1]
          });
          return;
        }
        if (pxPitch < 8 && !cell.isLeaf) {
          const alphaDetail = smoothstep(3, 8, pxPitch);
          const alphaAgg = 1 - alphaDetail;
          if (alphaAgg > 0.05) {
            aggregates.push({
              bounds: cell.bounds,
              centerOfMass: cell.centerOfMass,
              activeCount,
              totalCount: cell.births.length,
              alpha: alphaAgg,
              pxPitch,
              radius: Math.min(60, Math.max(12, Math.sqrt(activeCount) * 4)),
              crownJewels: cell.crownJewels.filter((n) => n.birthTime <= t),
              latestBirthTime: cell.births[activeCount - 1]
            });
          }
          if (cell.children) {
            for (const child of cell.children) {
              traverse(child);
            }
          }
          return;
        }
        if (cell.children) {
          for (const child of cell.children) {
            traverse(child);
          }
        } else {
          for (const n of cell.nodes) {
            if (n.birthTime <= t) {
              visibleNodes.set(n.id, {
                node: n,
                alpha: 1
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
  };

  // src/vis/camera.ts
  var DEFAULT_CAMERA_CONFIG = {
    tau: 35,
    baselineWeight: 0.08,
    margin: 40,
    minRadius: 80,
    crownJewelBias: 0.1,
    minZoom: 0.95,
    maxZoom: 2.2
  };
  var GravityWellCamera = class {
    config;
    constructor(config = {}) {
      this.config = { ...DEFAULT_CAMERA_CONFIG, ...config };
    }
    /**
     * Computes the pure closed-form camera position & zoom at time t.
     */
    getCameraState(nodes, t, viewportWidth, viewportHeight, projectedTargets) {
      const activeNodes = [];
      const weights = [];
      let totalWeight = 0;
      let weightedX = 0;
      let weightedY = 0;
      for (const node of nodes) {
        if (node.birthTime <= t) {
          activeNodes.push(node);
          const deltaT = t - node.birthTime;
          const decay = Math.exp(-deltaT / this.config.tau);
          const w = (decay + this.config.baselineWeight) * (1 + node.criticality);
          weights.push(w);
          totalWeight += w;
          weightedX += node.x * w;
          weightedY += node.y * w;
        }
      }
      if (activeNodes.length === 0) {
        const defaultX = nodes.length > 0 ? nodes[0].budX : viewportWidth / 2;
        const defaultY = nodes.length > 0 ? nodes[0].budY : viewportHeight / 2;
        return {
          focusX: defaultX,
          focusY: defaultY,
          zoom: 1,
          r90: this.config.minRadius,
          activeCount: 0
        };
      }
      let focusX = weightedX / totalWeight;
      let focusY = weightedY / totalWeight;
      if (projectedTargets && projectedTargets.length > 0) {
        let topTarget = null;
        let maxCrit = -1;
        for (const tgt of projectedTargets) {
          if (tgt.birthTime > t && tgt.criticality > maxCrit) {
            maxCrit = tgt.criticality;
            topTarget = tgt;
          }
        }
        if (topTarget && maxCrit >= 0.7) {
          const alpha = this.config.crownJewelBias;
          focusX = (1 - alpha) * focusX + alpha * topTarget.x;
          focusY = (1 - alpha) * focusY + alpha * topTarget.y;
        }
      }
      const distances = [];
      for (const node of activeNodes) {
        distances.push(Math.hypot(node.x - focusX, node.y - focusY));
      }
      distances.sort((a, b) => a - b);
      const p90Index = Math.floor(distances.length * 0.9);
      const rawR90 = distances[Math.min(distances.length - 1, p90Index)];
      const r90 = Math.max(this.config.minRadius, rawR90);
      const minViewportDim = Math.min(viewportWidth, viewportHeight);
      const rawZoom = minViewportDim / (2 * r90 + this.config.margin);
      const zoom = Math.min(this.config.maxZoom, Math.max(this.config.minZoom, rawZoom));
      return {
        focusX,
        focusY,
        zoom,
        r90,
        activeCount: activeNodes.length
      };
    }
  };

  // src/vis/morphology.ts
  function halton(index, base) {
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
  function sampleWrappedCauchy(gamma, u) {
    const v = Math.PI * (2 * u - 1);
    const sinhG = Math.sinh(gamma);
    const coshG = Math.cosh(gamma);
    return 2 * Math.atan(sinhG * Math.tan(v / 2) / (coshG + 1));
  }
  function generateDMZPosition(k, center, entryVec, length = 320, width = 55) {
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
  function generateWorkstationPosition(k, parentPos, entryVec, minDist = 22) {
    const u1 = halton(k + 1, 2);
    const u2 = halton(k + 1, 3);
    const dist = minDist * (2.2 + 2.8 * Math.sqrt(u1));
    const deltaTheta = sampleWrappedCauchy(0.42, u2);
    const angle = entryVec.directionRad + deltaTheta;
    return {
      x: parentPos.x + dist * Math.cos(angle),
      y: parentPos.y + dist * Math.sin(angle)
    };
  }
  function generateServerRackPosition(k, origin, bladesPerRack = 4, racksPerAisle = 3, dxRack = 36, dyAisle = 48) {
    const rackCapacity = bladesPerRack * racksPerAisle;
    const aisle = Math.floor(k / rackCapacity);
    const rackInAisle = Math.floor(k % rackCapacity / bladesPerRack);
    const blade = k % bladesPerRack;
    const subX = blade % 2 * 14;
    const subY = Math.floor(blade / 2) * 16;
    const jitterX = (halton(k + 1, 5) - 0.5) * 4;
    const jitterY = (halton(k + 1, 7) - 0.5) * 4;
    return {
      x: origin.x + rackInAisle * dxRack + subX + jitterX,
      y: origin.y + aisle * dyAisle + subY + jitterY
    };
  }
  function generateCrownJewelPosition(k, center, innerLimit = 3, coreRadius = 42, moatRadius = 95, spokesPerRing = 6, ringGap = 38) {
    if (k < innerLimit) {
      const r = coreRadius * Math.sqrt((k + 0.5) / innerLimit);
      const theta = k * 2 * Math.PI / innerLimit;
      return {
        x: center.x + r * Math.cos(theta),
        y: center.y + r * Math.sin(theta)
      };
    } else {
      const outerK = k - innerLimit;
      const ringIndex = Math.floor(outerK / spokesPerRing);
      const spokeIndex = outerK % spokesPerRing;
      const r = moatRadius + ringIndex * ringGap;
      const phaseOffset = ringIndex * 0.45;
      const theta = spokeIndex * 2 * Math.PI / spokesPerRing + phaseOffset;
      return {
        x: center.x + r * Math.cos(theta),
        y: center.y + r * Math.sin(theta)
      };
    }
  }
  function computeArchetypePosition(archetype, nodeIndexInSubnet, territoryCenter, parentPos, entryVec, spatialHash, minClearance = 20) {
    let probe = 0;
    const maxProbes = 32;
    while (probe < maxProbes) {
      const k = nodeIndexInSubnet + probe;
      let candidate;
      switch (archetype) {
        case "PERIMETER_DMZ":
          candidate = generateDMZPosition(k, territoryCenter, entryVec);
          break;
        case "WORKSTATION_POOL":
          candidate = generateWorkstationPosition(k, parentPos, entryVec, minClearance);
          break;
        case "SERVER_CLUSTER":
          candidate = generateServerRackPosition(k, territoryCenter);
          break;
        case "CROWN_JEWELS_AD":
          candidate = generateCrownJewelPosition(k, territoryCenter);
          break;
        default:
          candidate = generateWorkstationPosition(k, parentPos, entryVec, minClearance);
      }
      if (!spatialHash.hasOverlap(candidate.x, candidate.y, minClearance)) {
        return candidate;
      }
      probe++;
    }
    const fallbackDist = minClearance * 2.5 + probe * 8;
    const fallbackAngle = probe * 1.618;
    return {
      x: territoryCenter.x + fallbackDist * Math.cos(fallbackAngle),
      y: territoryCenter.y + fallbackDist * Math.sin(fallbackAngle)
    };
  }

  // src/vis/tether_exploratory.ts
  function pacingPhi(u) {
    return 0.25 * u + 0.75 * Math.pow(u, 4);
  }
  function envelopeW(u) {
    const cl = Math.min(1, Math.max(0, u));
    return 16 * Math.pow(cl, 2) * Math.pow(1 - cl, 3);
  }
  function computePerpOffset(u, chordLen, seed = 42) {
    const w1 = 6.28;
    const w2 = 12.56;
    const w3 = 18.84;
    const p1 = seed * 0.17 % 6.28;
    const p2 = seed * 0.43 % 6.28;
    const osc = 0.08 * Math.sin(w1 * u + p1) + 0.04 * Math.sin(w2 * u + p2) + 0.02 * Math.sin(w3 * u);
    return chordLen * osc;
  }
  function getExploratoryTether(parentPos, targetPos, t, tSpawn, duration = 8, seed = 1337, neighborDecoyTargets = []) {
    if (t < tSpawn) return null;
    const elapsed = t - tSpawn;
    const u = Math.min(1, Math.max(0, elapsed / duration));
    const dx = targetPos.x - parentPos.x;
    const dy = targetPos.y - parentPos.y;
    const chordLen = Math.hypot(dx, dy);
    const tangX = chordLen > 1e-4 ? dx / chordLen : 1;
    const tangY = chordLen > 1e-4 ? dy / chordLen : 0;
    const normX = -tangY;
    const normY = tangX;
    const phi = pacingPhi(u);
    const env = envelopeW(u);
    const dPerp = computePerpOffset(u, chordLen, seed);
    const baseX = parentPos.x + dx * phi;
    const baseY = parentPos.y + dy * phi;
    const headX = baseX + env * (dPerp * normX);
    const headY = baseY + env * (dPerp * normY);
    let phase = "RECON";
    if (u >= 0.85) phase = "SNAP";
    else if (u >= 0.45) phase = "LOCK_ON";
    const curvePoints = [];
    const samples = 16;
    const currentMaxStep = Math.max(2, Math.floor(samples * u));
    for (let i = 0; i <= currentMaxStep; i++) {
      const stepU = i / samples * u;
      const stepPhi = pacingPhi(stepU);
      const stepEnv = envelopeW(stepU);
      const stepPerp = computePerpOffset(stepU, chordLen, seed);
      curvePoints.push({
        x: parentPos.x + dx * stepPhi + stepEnv * (stepPerp * normX),
        y: parentPos.y + dy * stepPhi + stepEnv * (stepPerp * normY)
      });
    }
    const decoys = [];
    if (u < 0.65 && neighborDecoyTargets.length > 0) {
      const reachProfile = Math.sin(Math.PI * (u / 0.65)) * 0.62;
      for (let m = 0; m < Math.min(3, neighborDecoyTargets.length); m++) {
        const tgt = neighborDecoyTargets[m];
        const decoyCurX = parentPos.x + (tgt.x - parentPos.x) * reachProfile;
        const decoyCurY = parentPos.y + (tgt.y - parentPos.y) * reachProfile;
        const isBlocked = u > 0.35;
        decoys.push({
          targetX: tgt.x,
          targetY: tgt.y,
          currentX: decoyCurX,
          currentY: decoyCurY,
          reach: reachProfile,
          isBlocked,
          opacity: (1 - u / 0.65) * (isBlocked ? 0.9 : 0.45)
        });
      }
    }
    return {
      headX,
      headY,
      phase,
      normalizedU: u,
      curvePoints,
      decoys,
      opacity: Math.max(0.1, 1 - u * 0.85)
    };
  }

  // src/vis/presenter.ts
  var PresenterPlaybackEngine = class {
    constructor(allEvents, briefings = []) {
      this.allEvents = allEvents;
      this.milestones = allEvents.filter((e) => e.isCriticalMilestone);
      this.generateDefaultBriefings();
      if (briefings.length > 0) {
        for (let i = 0; i < briefings.length; i++) {
          const card = briefings[i];
          if (card.eventId) this.briefingMap.set(card.eventId, card);
          if (i < this.milestones.length) {
            this.briefingMap.set(this.milestones[i].eventId, card);
          }
        }
      }
    }
    allEvents;
    currentSimTime = 0;
    mode = "ADAPTIVE_NARRATIVE";
    vMin = 0.6;
    // 0.6 sim-sec / wall-sec during critical milestones
    vMax = 120;
    // 120 sim-sec / wall-sec during dwell gaps
    gamma = 2.2;
    // Deceleration sharpness
    sigmaLead = 12;
    // Decelerate 12s before milestone impact
    sigmaTrail = 35;
    // Hold slower speed 35s after milestone impact
    milestones;
    briefingMap = /* @__PURE__ */ new Map();
    generateDefaultBriefings() {
      this.milestones.forEach((m, idx) => {
        const card = {
          hopIndex: idx + 1,
          totalCriticalHops: this.milestones.length,
          eventId: m.eventId,
          timestampFormatted: `T+${Math.floor(m.tSimImpact / 60)}h ${Math.floor(m.tSimImpact % 60)}m`,
          dwellSincePreviousHop: idx === 0 ? "Initial intrusion" : `+${Math.max(1, Math.round(m.tSimStart - this.milestones[idx - 1].tSimImpact))}m dwell gap`,
          headline: `${m.tactic.replace("_", " ")}: ${m.targetNodeId} Compromised`,
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
            `Elevated privilege to ${m.criticality >= 0.8 ? "Domain Admin" : "Local Admin"} - unlocks lateral credential reuse.`,
            `Immediate countermeasure: Isolate ${m.targetNodeId} and revoke kerberos session tickets.`
          ]
        };
        this.briefingMap.set(m.eventId, card);
      });
    }
    /**
     * Evaluates continuous Asymmetric Narrative Salience Field S(t) in [0, 1]
     */
    evaluateSalience(t) {
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
    tick(deltaWallSeconds) {
      if (this.mode === "STEP_HOLD") {
        return {
          currentSimTime: this.currentSimTime,
          instantaneousWarpRatio: 0,
          salienceLevel: this.evaluateSalience(this.currentSimTime),
          activeBriefing: this.findActiveBriefingAt(this.currentSimTime)
        };
      }
      const salience = this.evaluateSalience(this.currentSimTime);
      const exponent = Math.pow(1 - salience, this.gamma);
      const vt = this.mode === "ADAPTIVE_NARRATIVE" ? this.vMin * Math.pow(this.vMax / this.vMin, exponent) : this.vMin * 10;
      const tMid = this.currentSimTime + 0.5 * deltaWallSeconds * vt;
      const salienceMid = this.evaluateSalience(tMid);
      const vtMid = this.mode === "ADAPTIVE_NARRATIVE" ? this.vMin * Math.pow(this.vMax / this.vMin, Math.pow(1 - salienceMid, this.gamma)) : vt;
      this.currentSimTime += deltaWallSeconds * vtMid;
      return {
        currentSimTime: this.currentSimTime,
        instantaneousWarpRatio: vtMid,
        salienceLevel: salienceMid,
        activeBriefing: this.findActiveBriefingAt(this.currentSimTime)
      };
    }
    stepToNextCriticalHop(options = { arrivalStyle: "ANIMATE_IMPACT", cameraTransitionDurationMs: 650 }) {
      let nextHop = this.milestones.find((m) => m.tSimImpact > this.currentSimTime + 0.05);
      if (!nextHop && this.milestones.length > 0) {
        nextHop = this.milestones[0];
      }
      if (!nextHop) return null;
      return this.executeHopTransition(nextHop, options);
    }
    stepToPreviousCriticalHop(options = { arrivalStyle: "SNAP_COMPLETE", cameraTransitionDurationMs: 650 }) {
      for (let i = this.milestones.length - 1; i >= 0; i--) {
        if (this.milestones[i].tSimStart < this.currentSimTime - 0.5) {
          return this.executeHopTransition(this.milestones[i], options);
        }
      }
      if (this.milestones.length > 0) {
        return this.executeHopTransition(this.milestones[this.milestones.length - 1], options);
      }
      return null;
    }
    jumpToMilestoneByIndex(hopIndex, options) {
      const clamped = Math.max(0, Math.min(this.milestones.length - 1, hopIndex));
      return this.executeHopTransition(
        this.milestones[clamped],
        options ?? { arrivalStyle: "ANIMATE_IMPACT", cameraTransitionDurationMs: 650 }
      );
    }
    executeHopTransition(target, options) {
      this.currentSimTime = options.arrivalStyle === "ANIMATE_IMPACT" ? target.tSimStart : target.tSimImpact;
      this.mode = options.arrivalStyle === "SNAP_COMPLETE" ? "STEP_HOLD" : "ADAPTIVE_NARRATIVE";
      const minX = Math.min(target.sourcePos.x, target.targetPos.x);
      const maxX = Math.max(target.sourcePos.x, target.targetPos.x);
      const minY = Math.min(target.sourcePos.y, target.targetPos.y);
      const maxY = Math.max(target.sourcePos.y, target.targetPos.y);
      const span = Math.max(maxX - minX, maxY - minY, 140);
      const optimalCameraPose = {
        center: {
          x: 0.35 * target.sourcePos.x + 0.65 * target.targetPos.x,
          y: 0.35 * target.sourcePos.y + 0.65 * target.targetPos.y
        },
        zoom: Math.min(2.4, Math.max(0.65, 800 / (span * 1.4))),
        framingBounds: { min: { x: minX, y: minY }, max: { x: maxX, y: maxY } }
      };
      const briefingCard = this.briefingMap.get(target.eventId) || (this.milestones.length > 0 ? this.briefingMap.get(this.milestones[0].eventId) : null);
      return {
        targetEvent: target,
        briefingCard,
        optimalCameraPose,
        simTimeSetTo: this.currentSimTime
      };
    }
    findActiveBriefingAt(t) {
      for (let i = this.milestones.length - 1; i >= 0; i--) {
        const m = this.milestones[i];
        if (t >= m.tSimStart && t <= m.tSimImpact + this.sigmaTrail) {
          return this.briefingMap.get(m.eventId) ?? null;
        }
      }
      if (this.milestones.length > 0 && t >= this.milestones[this.milestones.length - 1].tSimStart) {
        return this.briefingMap.get(this.milestones[this.milestones.length - 1].eventId) ?? null;
      }
      return null;
    }
    seekToSimTime(tSim) {
      this.currentSimTime = Math.max(0, tSim);
    }
    getAllCriticalMilestones() {
      return this.milestones.map((m) => this.briefingMap.get(m.eventId));
    }
    setPlaybackMode(mode) {
      this.mode = mode;
    }
    setAdaptiveSpeedBounds(vMin, vMax) {
      this.vMin = vMin;
      this.vMax = vMax;
    }
  };

  // src/vis/stochastic.ts
  function sampleLomaxDwell(u, alpha = 1.6, sigma = 35, deltaMin = 2) {
    const safeU = Math.min(0.995, Math.max(1e-3, u));
    const dwell = deltaMin + sigma * (Math.pow(1 - safeU, -1 / alpha) - 1);
    return Math.min(180, dwell);
  }
  function generateHawkesCascade(tStart, tHorizon, mu0, activeEvents, prng, maxEvents = 40) {
    const timestamps = [];
    let t = tStart;
    const evaluateLambda = (time) => {
      let intensity = mu0;
      for (const ev of activeEvents) {
        if (ev.t < time) {
          intensity += ev.alpha * ev.beta * Math.exp(-ev.beta * (time - ev.t));
        }
      }
      return intensity;
    };
    while (t < tHorizon && timestamps.length < maxEvents) {
      const M = Math.max(5e-3, evaluateLambda(t));
      const u1 = Math.max(1e-7, prng());
      const dt = -Math.log(u1) / M;
      t += dt;
      if (t >= tHorizon) break;
      const u2 = prng();
      const lambdaCurrent = evaluateLambda(t);
      if (u2 <= lambdaCurrent / M) {
        timestamps.push(t);
        const childAlpha = 1.2 * prng();
        const childBeta = 0.15 + 0.3 * prng();
        activeEvents.push({ t, alpha: childAlpha, beta: childBeta });
      }
    }
    return timestamps;
  }
  function sampleBranchingDegree(privilegeLevel, subnetDensity, prng) {
    const logit = 0.8 * privilegeLevel + 0.5 * subnetDensity - 1.8;
    const pSweep = 1 / (1 + Math.exp(-logit));
    const isSweep = prng() < pSweep;
    if (!isSweep) {
      const degree = 1 + (prng() < 0.15 ? 1 : 0);
      return { degree, mode: "STEALTH" };
    } else {
      const u = prng();
      let degree = 2;
      if (u < 0.4) degree = 2;
      else if (u < 0.7) degree = 3;
      else if (u < 0.9) degree = 4;
      else degree = 5 + Math.floor(prng() * 3);
      return { degree, mode: "SWEEP" };
    }
  }

  // src/vis/engine.ts
  var CausalTerritorialEngine = class {
    territoryEngine;
    camera;
    quadtree = null;
    nodes = [];
    nodeMap = /* @__PURE__ */ new Map();
    events = [];
    subnetArchetypes = /* @__PURE__ */ new Map();
    playbackEngine = null;
    isCausalReplay = false;
    // Interactive Camera Transform Overrides
    panX = 0;
    panY = 0;
    userZoom = 1;
    hoverNodeId = null;
    selectedNodeId = null;
    constructor(options = {}) {
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
    assignSubnetArchetype(clusterId) {
      const lower = clusterId.toLowerCase();
      if (lower.includes("dmz") || lower.includes("ingress") || lower.includes("edge") || lower.includes("wan") || lower.includes("perimeter")) {
        return "PERIMETER_DMZ";
      }
      if (lower.includes("dc") || lower.includes("domain") || lower.includes("auth") || lower.includes("jewel") || lower.includes("vault") || lower.includes("99.") || lower.includes("identity")) {
        return "CROWN_JEWELS_AD";
      }
      if (lower.includes("server") || lower.includes("data") || lower.includes("db") || lower.includes("cluster") || lower.includes("k8s") || lower.includes("prod") || lower.includes("rack")) {
        return "SERVER_CLUSTER";
      }
      return "WORKSTATION_POOL";
    }
    /**
     * Ingests chronological events with heterogeneous archetype placement.
     */
    ingest(events, customBriefings) {
      this.events = [...events].sort((a, b) => a.t - b.t);
      this.nodes = [];
      this.nodeMap.clear();
      const subnetCounts = /* @__PURE__ */ new Map();
      for (const ev of this.events) {
        let arch = this.subnetArchetypes.get(ev.cluster);
        if (!arch) {
          arch = this.assignSubnetArchetype(ev.cluster);
          this.subnetArchetypes.set(ev.cluster, arch);
        }
        const currentIdx = subnetCounts.get(ev.cluster) || 0;
        subnetCounts.set(ev.cluster, currentIdx + 1);
        let cluster = this.territoryEngine.clusters.get(ev.cluster);
        if (!cluster) {
          const parentNode = ev.parent ? this.nodeMap.get(ev.parent) : null;
          cluster = this.territoryEngine.spawnTerritory(ev.cluster, parentNode ? parentNode.cluster : null);
        }
        const parent = ev.parent ? this.nodeMap.get(ev.parent) : null;
        const parentPos = parent ? { x: parent.x, y: parent.y } : { x: cluster.seed.x, y: cluster.seed.y };
        const outward = this.territoryEngine.getOutwardVector(parentPos);
        const entryVec = {
          origin: parentPos,
          directionRad: Math.atan2(outward.y, outward.x)
        };
        const pos = computeArchetypePosition(
          arch,
          currentIdx,
          { x: cluster.seed.x, y: cluster.seed.y },
          parentPos,
          entryVec,
          this.territoryEngine.spatialHash,
          this.territoryEngine.config.minNodeDistance
        );
        const placed = {
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
      this.quadtree = new TemporalAggregateQuadtree(this.nodes);
      this.initPresenterEngine(customBriefings);
      return this.nodes;
    }
    initPresenterEngine(customBriefings) {
      const attackEvents = this.nodes.map((n, i) => {
        const arch = this.subnetArchetypes.get(n.cluster) || "WORKSTATION_POOL";
        const isCritical = n.criticality >= 0.75 || i === 0 || i === this.nodes.length - 1;
        let tactic = n.mitreTactic || "LATERAL_MOVEMENT";
        let techId = n.mitreTechId || "T1021.002";
        let techName = n.mitreTechName || "SMB/Windows Admin Shares";
        if (!n.mitreTechName) {
          if (i === 0 || n.type === "WAN") {
            tactic = "INITIAL_ACCESS";
            techId = "T1566.001";
            techName = "Spearphishing Attachment";
          } else if (arch === "CROWN_JEWELS_AD" || n.type === "DC") {
            tactic = "IMPACT";
            techId = "T1003.006";
            techName = "DCSync / Active Directory Shadow";
          } else if (n.type === "C2") {
            tactic = "COMMAND_AND_CONTROL";
            techId = "T1071.001";
            techName = "Web Protocols (C2 Beacon)";
          } else if (n.type === "USER" || n.criticality >= 0.8) {
            tactic = "CREDENTIAL_ACCESS";
            techId = "T1003";
            techName = "OS Credential Dumping";
          }
        }
        const parentNode = n.parent ? this.nodeMap.get(n.parent) : null;
        const srcPos = parentNode ? { x: parentNode.x, y: parentNode.y } : { x: n.budX, y: n.budY };
        return {
          eventId: `ev_${n.id}`,
          index: i + 1,
          tSimStart: Math.max(0, n.birthTime - 1.5),
          tSimImpact: n.birthTime,
          sourceNodeId: n.parent || "PatientZero",
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
    screenToWorld(sx, sy, width, height, t) {
      const cameraState = this.camera.getCameraState(this.nodes, t, width, height, this.nodes);
      const effZoom = cameraState.zoom * this.userZoom;
      const effFocusX = cameraState.focusX + this.panX;
      const effFocusY = cameraState.focusY + this.panY;
      return {
        x: (sx - width / 2) / effZoom + effFocusX,
        y: (sy - height / 2) / effZoom + effFocusY
      };
    }
    getNodeAt(sx, sy, width, height, t) {
      const wPos = this.screenToWorld(sx, sy, width, height, t);
      const snapshot = this.getStateAt(t, width, height);
      for (let i = snapshot.nodes.length - 1; i >= 0; i--) {
        const n = snapshot.nodes[i];
        const r = (n.archetype === "CROWN_JEWELS_AD" || n.type === "DC" ? 14 : 10) * n.scale + 8;
        const dist = Math.hypot(wPos.x - n.currentX, wPos.y - n.currentY);
        if (dist <= r) {
          return n;
        }
      }
      return null;
    }
    pan(dx, dy, width, height, t) {
      const cameraState = this.camera.getCameraState(this.nodes, t, width, height, this.nodes);
      const effZoom = cameraState.zoom * this.userZoom;
      this.panX -= dx / effZoom;
      this.panY -= dy / effZoom;
    }
    zoom(factor) {
      this.userZoom = Math.max(0.2, Math.min(6, this.userZoom * factor));
    }
    resetView() {
      this.panX = 0;
      this.panY = 0;
      this.userZoom = 1;
      this.hoverNodeId = null;
      this.selectedNodeId = null;
    }
    /**
     * Pure frame snapshot at campaign timestamp t.
     */
    getStateAt(t, viewportWidth, viewportHeight) {
      const cameraState = this.camera.getCameraState(
        this.nodes,
        t,
        viewportWidth,
        viewportHeight,
        this.nodes
      );
      const effZoom = cameraState.zoom * this.userZoom;
      const halfW = viewportWidth / 2 / effZoom;
      const halfH = viewportHeight / 2 / effZoom;
      const viewportBounds = {
        minX: cameraState.focusX + this.panX - halfW,
        minY: cameraState.focusY + this.panY - halfH,
        maxX: cameraState.focusX + this.panX + halfW,
        maxY: cameraState.focusY + this.panY + halfH
      };
      const lodResult = this.quadtree ? this.quadtree.query(viewportBounds, t, effZoom) : { aggregates: [], nodes: [], totalActive: 0 };
      const renderedNodes = [];
      const tethers = [];
      const exploratoryTethers = [];
      const settledEdges = [];
      const currentPosMap = /* @__PURE__ */ new Map();
      for (const vn of lodResult.nodes) {
        const budState = getBudState(vn.node, t);
        if (budState.isBorn) {
          const arch = this.subnetArchetypes.get(vn.node.cluster);
          const rNode = {
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
            const expTether = getExploratoryTether(
              { x: vn.node.budX, y: vn.node.budY },
              { x: vn.node.x, y: vn.node.y },
              t,
              vn.node.birthTime,
              8,
              vn.node.slotIndex * 137
            );
            if (expTether) exploratoryTethers.push(expTether);
          }
          if (vn.node.parent) {
            const parentNode = this.nodeMap.get(vn.node.parent);
            const isDcTarget = vn.node.archetype === "CROWN_JEWELS_AD" || vn.node.type === "DC" || vn.node.cluster.includes("DC");
            if (parentNode && (t >= parentNode.birthTime || this.isCausalReplay && isDcTarget)) {
              const parentBud = getBudState(parentNode, t);
              let edgeColor = "#38bdf8";
              if (this.isCausalReplay && isDcTarget) {
                if (t < vn.node.birthTime) {
                  edgeColor = "#f59e0b";
                } else if (t < vn.node.birthTime + 22) {
                  edgeColor = "#ef4444";
                } else {
                  edgeColor = "#38bdf8";
                }
              } else if (vn.node.archetype === "CROWN_JEWELS_AD" || vn.node.type === "DC") edgeColor = "#f43f5e";
              else if (vn.node.type === "C2") edgeColor = "#a855f7";
              else if (vn.node.type === "USER") edgeColor = "#f59e0b";
              else if (vn.node.criticality >= 0.75) edgeColor = "#f59e0b";
              const toX = budState.isBorn ? budState.x : vn.node.x;
              const toY = budState.isBorn ? budState.y : vn.node.y;
              settledEdges.push({
                sourceId: vn.node.parent,
                targetId: vn.node.id,
                fromX: parentBud.x,
                fromY: parentBud.y,
                toX,
                toY,
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
    render(ctx, t, width, height) {
      const snapshot = this.getStateAt(t, width, height);
      const effZoom = snapshot.camera.zoom * this.userZoom;
      const effFocusX = snapshot.camera.focusX + this.panX;
      const effFocusY = snapshot.camera.focusY + this.panY;
      ctx.fillStyle = "#070b14";
      ctx.fillRect(0, 0, width, height);
      ctx.save();
      ctx.translate(width / 2, height / 2);
      ctx.scale(effZoom, effZoom);
      ctx.translate(-effFocusX, -effFocusY);
      for (const [clusterId, territory] of this.territoryEngine.clusters.entries()) {
        const arch = this.subnetArchetypes.get(clusterId) || "WORKSTATION_POOL";
        const seed = territory.seed;
        ctx.save();
        ctx.setLineDash([4, 6]);
        if (arch === "PERIMETER_DMZ") {
          ctx.strokeStyle = "rgba(56, 189, 248, 0.28)";
          ctx.lineWidth = 1.2 / effZoom;
          ctx.strokeRect(seed.x - 180, seed.y - 50, 360, 100);
          ctx.fillStyle = "#38bdf8";
          ctx.font = "bold 9px monospace";
          ctx.fillText(`PERIMETER DMZ FENCE: ${clusterId.toUpperCase()}`, seed.x - 170, seed.y - 58);
        } else if (arch === "CROWN_JEWELS_AD") {
          ctx.strokeStyle = "rgba(244, 63, 94, 0.4)";
          ctx.lineWidth = 1.5 / effZoom;
          ctx.beginPath();
          ctx.arc(seed.x, seed.y, 45, 0, Math.PI * 2);
          ctx.stroke();
          ctx.beginPath();
          ctx.arc(seed.x, seed.y, 110, 0, Math.PI * 2);
          ctx.stroke();
          ctx.fillStyle = "#f43f5e";
          ctx.font = "bold 9px monospace";
          ctx.fillText(`TIER-0 CROWN MOAT: ${clusterId.toUpperCase()}`, seed.x, seed.y - 120);
        } else if (arch === "SERVER_CLUSTER") {
          ctx.strokeStyle = "rgba(168, 85, 247, 0.25)";
          ctx.lineWidth = 1 / effZoom;
          ctx.strokeRect(seed.x - 10, seed.y - 10, 160, 180);
          ctx.fillStyle = "#a855f7";
          ctx.font = "bold 9px monospace";
          ctx.fillText(`DATACENTER RACK: ${clusterId.toUpperCase()}`, seed.x, seed.y - 18);
        } else {
          ctx.strokeStyle = "rgba(148, 163, 184, 0.2)";
          ctx.lineWidth = 1 / effZoom;
          ctx.beginPath();
          ctx.arc(seed.x, seed.y, seed.reservedRadius, 0, Math.PI * 2);
          ctx.stroke();
          ctx.fillStyle = "#64748b";
          ctx.font = "bold 9px monospace";
          ctx.fillText(`WORKSTATION POOL: ${clusterId.toUpperCase()}`, seed.x, seed.y - seed.reservedRadius - 6);
        }
        ctx.restore();
      }
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
        ctx.strokeStyle = "rgba(239, 68, 68, 0.25)";
        ctx.lineWidth = 2 / effZoom;
        ctx.setLineDash([6, 8]);
        ctx.stroke();
        ctx.restore();
      }
      for (const edge of snapshot.settledEdges) {
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(edge.fromX, edge.fromY);
        if (edge.isCrossSubnet) {
          const midX = (edge.fromX + edge.toX) / 2;
          const midY = (edge.fromY + edge.toY) / 2 - 25;
          ctx.quadraticCurveTo(midX, midY, edge.toX, edge.toY);
        } else {
          ctx.lineTo(edge.toX, edge.toY);
        }
        ctx.strokeStyle = edge.color;
        ctx.globalAlpha = Math.min(0.85, 0.25 + 0.6 * edge.progress);
        const isThreatEdge = edge.color === "#f59e0b" || edge.color === "#ef4444";
        ctx.lineWidth = (isThreatEdge ? 2.8 : edge.criticality >= 0.75 ? 2.2 : 1.4) / effZoom;
        if (edge.isCrossSubnet || isThreatEdge) {
          ctx.setLineDash([6, 4]);
          if (isThreatEdge) {
            ctx.lineDashOffset = -(t * 18 % 24);
          }
        }
        ctx.stroke();
        const dx = edge.toX - edge.fromX;
        const dy = edge.toY - edge.fromY;
        const len = Math.hypot(dx, dy);
        if (len > 25) {
          const angle = Math.atan2(dy, dx);
          const arrowDist = 18;
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
      for (const exp of snapshot.exploratoryTethers) {
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
        if (exp.curvePoints.length > 1) {
          ctx.save();
          ctx.beginPath();
          ctx.moveTo(exp.curvePoints[0].x, exp.curvePoints[0].y);
          for (let i = 1; i < exp.curvePoints.length; i++) {
            ctx.lineTo(exp.curvePoints[i].x, exp.curvePoints[i].y);
          }
          const color = exp.phase === "SNAP" ? "#ef4444" : exp.phase === "LOCK_ON" ? "#f59e0b" : "#38bdf8";
          ctx.strokeStyle = color;
          ctx.globalAlpha = exp.opacity;
          ctx.lineWidth = (exp.phase === "SNAP" ? 2.5 : 1.5) / effZoom;
          ctx.stroke();
          ctx.restore();
        }
      }
      for (const agg of snapshot.aggregates) {
        ctx.save();
        ctx.globalAlpha = agg.alpha;
        const age = t - agg.latestBirthTime;
        const pulse = age < 15 ? 1 + 0.15 * Math.sin(age * 2) : 1;
        const radius = agg.radius * pulse;
        ctx.beginPath();
        ctx.arc(agg.centerOfMass.x, agg.centerOfMass.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = "#1e1b4b";
        ctx.strokeStyle = "#ef4444";
        ctx.lineWidth = 2.5 / effZoom;
        ctx.fill();
        ctx.stroke();
        ctx.fillStyle = "#f8fafc";
        ctx.font = `bold ${Math.max(10, 12 / effZoom)}px monospace`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(`${agg.activeCount}`, agg.centerOfMass.x, agg.centerOfMass.y);
        ctx.restore();
      }
      for (const n of snapshot.nodes) {
        ctx.save();
        ctx.globalAlpha = n.alpha;
        const isCrown = n.archetype === "CROWN_JEWELS_AD" || n.type === "DC" || n.cluster.includes("DC");
        const r = (isCrown ? 16 : 12) * n.scale;
        if (r > 0.5) {
          let color = "#38bdf8";
          let typeCode = "HOST";
          if (isCrown) {
            if (this.isCausalReplay && t >= n.birthTime + 10) {
              color = "#f59e0b";
              typeCode = "HOST";
            } else if (this.isCausalReplay && t >= n.birthTime) {
              color = "#ef4444";
              typeCode = "DC";
            } else if (this.isCausalReplay) {
              color = "#f59e0b";
              typeCode = "DC";
            } else {
              color = "#f43f5e";
              typeCode = "DC";
            }
          } else if (n.type === "C2") {
            color = "#a855f7";
            typeCode = "C2";
          } else if (n.type === "WAN") {
            color = "#ef4444";
            typeCode = "WAN";
          } else if (n.type === "USER") {
            color = "#f59e0b";
            typeCode = "USER";
          } else if (n.type === "PEER") {
            color = "#64748b";
            typeCode = "PEER";
          } else if (n.criticality >= 0.75) {
            color = "#f59e0b";
            typeCode = "HOST";
          }
          const isHovered = n.id === this.hoverNodeId;
          const isSelected = n.id === this.selectedNodeId;
          const nx = Math.round(n.currentX);
          const ny = Math.round(n.currentY);
          if (isHovered || isSelected) {
            ctx.beginPath();
            ctx.arc(nx, ny, r + 6, 0, Math.PI * 2);
            ctx.strokeStyle = isSelected ? "#38bdf8" : "#f59e0b";
            ctx.lineWidth = 2 / effZoom;
            ctx.stroke();
          }
          ctx.beginPath();
          ctx.arc(nx, ny, r, 0, Math.PI * 2);
          ctx.fillStyle = color;
          ctx.fill();
          ctx.strokeStyle = "#ffffff";
          ctx.lineWidth = 1.6 / effZoom;
          ctx.stroke();
          if (isCrown) {
            ctx.beginPath();
            ctx.arc(nx, ny, r * 0.6, 0, Math.PI * 2);
            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = 1.2 / effZoom;
            ctx.stroke();
          }
          if (n.isSettling) {
            ctx.beginPath();
            ctx.arc(nx, ny, r * (1.2 + 0.8 * (1 - n.progress)), 0, Math.PI * 2);
            ctx.strokeStyle = `rgba(245, 158, 11, ${1 - n.progress})`;
            ctx.lineWidth = 1.2 / effZoom;
            ctx.stroke();
          }
          if (r >= 8) {
            ctx.fillStyle = "#ffffff";
            ctx.font = `bold ${Math.max(8, Math.min(11, 9.5 / effZoom))}px monospace`;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(typeCode, nx, ny);
          }
          const isDcCompromisedHost = this.isCausalReplay && isCrown && t >= n.birthTime + 10;
          const labelStr = isDcCompromisedHost ? "10.10.99.1 [HOST COMPROMISED]" : n.label || n.id;
          const timeStr = `T+${Math.round(n.birthTime)}m`;
          const displayStr = `${labelStr} [${timeStr}]`;
          ctx.font = "bold 10px monospace";
          const strW = ctx.measureText(displayStr).width;
          const badgeW = Math.round(strW + 14);
          const badgeH = 18;
          const badgeX = Math.round(nx - badgeW / 2);
          const badgeY = Math.round(ny + r + 5);
          ctx.fillStyle = "rgba(9, 14, 26, 0.96)";
          ctx.strokeStyle = isSelected ? "#38bdf8" : isDcCompromisedHost ? "#f59e0b" : isCrown ? "rgba(244, 63, 94, 0.7)" : "rgba(51, 65, 85, 0.9)";
          ctx.lineWidth = 1.2 / effZoom;
          if (typeof ctx.roundRect === "function") {
            ctx.beginPath();
            ctx.roundRect(badgeX, badgeY, badgeW, badgeH, 4);
            ctx.fill();
            ctx.stroke();
          } else {
            ctx.fillRect(badgeX, badgeY, badgeW, badgeH);
            ctx.strokeRect(badgeX, badgeY, badgeW, badgeH);
          }
          ctx.fillStyle = isDcCompromisedHost ? "#fde047" : isCrown ? "#fca5a5" : "#ffffff";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(displayStr, nx, badgeY + badgeH / 2);
        }
        ctx.restore();
      }
      ctx.restore();
      return snapshot;
    }
  };
  return __toCommonJS(engine_exports);
})();
