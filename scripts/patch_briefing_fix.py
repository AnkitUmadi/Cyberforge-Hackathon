import re
from pathlib import Path

tmpl_path = Path("templates/incident_report.j2")
content = tmpl_path.read_text(encoding="utf-8")

# 1. Update customBriefings construction
old_briefing_target = """                // Generate structured briefing cards from real timeline hops
                const customBriefings = hops.map((h, idx) => {
                    const tVal = h.t_min !== undefined ? h.t_min : idx * 15;
                    const prevT = idx > 0 ? (hops[idx - 1].t_min || 0) : 0;
                    const dwell = idx === 0 ? "Perimeter Ingress" : `+${Math.max(1, Math.round(tVal - prevT))}m dwell`;
                    const isCrown = (h.dest_ip && h.dest_ip.includes('99.')) || (h.stage && h.stage.includes('Impact'));

                    return {
                        hopIndex: idx + 1,
                        totalCriticalHops: hops.length,
                        eventId: `ev_${h.dest_ip || idx}`,
                        timestampFormatted: `T+${Math.floor(tVal / 60)}h ${Math.floor(tVal % 60)}m`,
                        dwellSincePreviousHop: dwell,
                        headline: `${h.stage || 'Lateral Movement'}: ${h.tech_name || 'Exploitation'}`,
                        mitreBadge: {
                            tactic: h.stage || 'LATERAL_MOVEMENT',
                            techniqueId: h.tech_id || 'T1021.002',
                            techniqueName: h.tech_name || 'Lateral Hop'
                        },
                        causalLineage: {
                            sourceHostname: h.src_ip || 'Gateway',
                            sourceIp: h.src_ip || '198.51.100.23',
                            targetHostname: h.dest_ip || 'TargetHost',
                            targetIp: h.dest_ip || '10.10.1.5',
                            compromisedCredential: isCrown ? 'DomainAdmin' : 'LocalAdmin'
                        },
                        blastRadiusStats: {
                            downstreamNodesExposed: isCrown ? 250 : 8,
                            cascadeRatePerMin: isCrown ? 4.5 : 1.8
                        },
                        presenterTalkingPoints: [
                            h.evidence || `Attacker executed ${h.tech_name} (${h.tech_id}) from ${h.src_ip} into ${h.dest_ip}.`,
                            isCrown ? "CRITICAL: Tier-0 Domain Controller reachable - immediate forest isolation required." : "Lateral spread across subnet boundary.",
                            "Containment: Revoke authentication tickets and quarantine host interface."
                        ]
                    };
                });"""

new_briefing_code = """                // Generate structured briefing cards from real timeline hops
                const customBriefings = hops.map((h, idx) => {
                    const tVal = h.t_min !== undefined ? h.t_min : idx * 15;
                    const prevT = idx > 0 ? (hops[idx - 1].t_min || 0) : 0;
                    const dwell = idx === 0 ? "Perimeter Ingress" : `+${Math.max(1, Math.round(tVal - prevT))}m dwell`;
                    const isCrown = (h.dest_ip && h.dest_ip.includes('99.')) || (h.stage && h.stage.includes('Impact'));
                    const isSrcPrivate = h.src_ip && (h.src_ip.startsWith('10.') || h.src_ip.startsWith('192.168.') || h.src_ip.startsWith('172.'));

                    let stageDisplay = h.stage || 'Lateral Movement';
                    let headlineDisplay = `${stageDisplay}: ${h.tech_name || 'Exploitation'}`;

                    if (!isSrcPrivate && stageDisplay.toLowerCase().includes('lateral')) {
                        stageDisplay = 'Initial Access';
                        headlineDisplay = `Initial Access: Inbound Remote Services (${h.tech_name || 'RDP/SSH'})`;
                    } else if (isCrown) {
                        headlineDisplay = `Crown Jewel Impact: ${h.tech_name || 'Tier-0 Compromise'}`;
                    }

                    const talkingPoint = !isSrcPrivate
                        ? `Adversary connected from external WAN IP ${h.src_ip} into internal server ${h.dest_ip} via ${h.tech_name || 'remote service'}.`
                        : (isCrown
                            ? "CRITICAL: Attack breached Tier-0 Domain Controller. Immediate forest isolation required."
                            : (h.evidence || `Attacker pivoted laterally from internal host ${h.src_ip} into ${h.dest_ip} via ${h.tech_name || 'remote service'}.`));

                    return {
                        hopIndex: idx + 1,
                        totalCriticalHops: hops.length,
                        eventId: `ev_${h.dest_ip || idx}`,
                        simTime: tVal,
                        timestampFormatted: `T+${Math.floor(tVal / 60)}h ${Math.floor(tVal % 60)}m`,
                        dwellSincePreviousHop: dwell,
                        headline: headlineDisplay,
                        mitreBadge: {
                            tactic: stageDisplay.toUpperCase().replace(/\\s+/g, '_'),
                            techniqueId: h.tech_id || (stageDisplay === 'Initial Access' ? 'T1133' : 'T1021.002'),
                            techniqueName: h.tech_name || (stageDisplay === 'Initial Access' ? 'External Remote Services' : 'Lateral Hop')
                        },
                        causalLineage: {
                            sourceHostname: h.src_ip || 'Gateway',
                            sourceIp: h.src_ip || '198.51.100.23',
                            targetHostname: h.dest_ip || 'TargetHost',
                            targetIp: h.dest_ip || '10.10.1.5',
                            compromisedCredential: isCrown ? 'DomainAdmin' : 'LocalAdmin'
                        },
                        blastRadiusStats: {
                            downstreamNodesExposed: isCrown ? 250 : 8,
                            cascadeRatePerMin: isCrown ? 4.5 : 1.8
                        },
                        presenterTalkingPoints: [
                            talkingPoint,
                            isCrown ? "Tier-0 Domain Controller reachable - immediate forest isolation required." : "Lateral spread across subnet boundary.",
                            "Containment: Revoke authentication tickets and quarantine host interface."
                        ]
                    };
                });

                this.customBriefings = customBriefings;"""

# Replace customBriefings
normalized_content = content.replace("\r\n", "\n")
normalized_target = old_briefing_target.replace("\r\n", "\n")

if normalized_target in normalized_content:
    normalized_content = normalized_content.replace(normalized_target, new_briefing_code)
    print("Successfully replaced customBriefings logic.")
else:
    print("Warning: old_briefing_target not found.")

# 2. Add showCompletedBriefing and updateBriefingForTime methods
new_methods = """
            showCompletedBriefing() {
                if (!this.customBriefings || !this.customBriefings.length || !this.hudBriefing) return;
                const finalHop = this.customBriefings[this.customBriefings.length - 1];
                this.hudBriefing.style.display = 'block';
                if (this.briefBadge) this.briefBadge.innerText = `COMPLETED (${finalHop.totalCriticalHops} / ${finalHop.totalCriticalHops} HOPS)`;
                if (this.briefDwell) this.briefDwell.innerText = 'Campaign Terminal Impact';
                if (this.briefHeadline) this.briefHeadline.innerText = `Final Objective: ${finalHop.headline}`;
                if (this.briefLineage) this.briefLineage.innerText = `${finalHop.causalLineage.sourceHostname} → ${finalHop.causalLineage.targetHostname}`;
                if (this.briefTalkingPoint) this.briefTalkingPoint.innerText = `All ${finalHop.totalCriticalHops} critical causal hops correlated. Containment perimeter identified.`;
            }

            updateBriefingForTime(t) {
                if (!this.customBriefings || !this.customBriefings.length || !this.hudBriefing) return;
                if (t >= this.totalDuration) {
                    this.showCompletedBriefing();
                    return;
                }
                let activeHop = null;
                for (let i = 0; i < this.customBriefings.length; i++) {
                    const bh = this.customBriefings[i];
                    if (bh.simTime <= t) {
                        activeHop = bh;
                    } else {
                        break;
                    }
                }
                if (activeHop) {
                    this.hudBriefing.style.display = 'block';
                    if (this.briefBadge) this.briefBadge.innerText = `HOP ${activeHop.hopIndex} / ${activeHop.totalCriticalHops}`;
                    if (this.briefDwell) this.briefDwell.innerText = activeHop.dwellSincePreviousHop;
                    if (this.briefHeadline) this.briefHeadline.innerText = activeHop.headline;
                    if (this.briefLineage) this.briefLineage.innerText = `${activeHop.causalLineage.sourceHostname} → ${activeHop.causalLineage.targetHostname}`;
                    if (this.briefTalkingPoint) this.briefTalkingPoint.innerText = activeHop.presenterTalkingPoints[0] || '';
                }
            }

            toggleAdaptivePacing() {"""

old_methods_target = """            toggleAdaptivePacing() {"""
normalized_content = normalized_content.replace(old_methods_target, new_methods)

# 3. Call showCompletedBriefing when tNow >= totalDuration
old_completion = """                    if (this.tNow >= this.totalDuration) {
                        this.tNow = this.totalDuration;
                        this.isPlaying = false;
                        this.updatePlayState();
                    }"""

new_completion = """                    if (this.tNow >= this.totalDuration) {
                        this.tNow = this.totalDuration;
                        this.isPlaying = false;
                        this.updatePlayState();
                        this.showCompletedBriefing();
                    }"""

normalized_content = normalized_content.replace(old_completion, new_completion)

# 4. In seek(t), call updateBriefingForTime
old_seek = """            seek(t) {
                this.tNow = Math.max(0, Math.min(this.totalDuration, t));
                if (this.engine && this.engine.playbackEngine) this.engine.playbackEngine.seekToSimTime(this.tNow);
                this.lastTimestamp = performance.now();
                if (this.scrubber) this.scrubber.value = Math.round(this.tNow);
            }"""

new_seek = """            seek(t) {
                this.tNow = Math.max(0, Math.min(this.totalDuration, t));
                if (this.engine && this.engine.playbackEngine) this.engine.playbackEngine.seekToSimTime(this.tNow);
                this.lastTimestamp = performance.now();
                if (this.scrubber) this.scrubber.value = Math.round(this.tNow);
                this.updateBriefingForTime(this.tNow);
            }"""

normalized_content = normalized_content.replace(old_seek, new_seek)

tmpl_path.write_text(normalized_content, encoding="utf-8")
print("Template updated successfully!")
