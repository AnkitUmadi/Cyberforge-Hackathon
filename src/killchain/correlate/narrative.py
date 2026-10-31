"""
Plain-English Narrative & Executive Threat Summary Generator.
Translates technical 4D correlation alerts and graph lookaheads
into human-readable executive incident briefings.
"""

from typing import Dict, Any, List

def generate_plain_english_narrative(incident: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms raw incident metadata, ordered hops, and lookahead blast radius
    into an auto-written plain English executive briefing.
    """
    inc_id = incident.get("incident_id", 0)
    score = incident.get("risk_score", 0)
    sev = incident.get("severity", "HIGH")
    host = incident.get("root_entity", "Unknown Host")
    attacker = incident.get("adversary_ip", "Unknown External IP")
    user = incident.get("usr", "system")
    duration = incident.get("duration_minutes", 0)
    alerts = incident.get("alert_count", 0)
    ts_start = incident.get("ts_start", "")
    
    stages = incident.get("stages_covered", "")
    if isinstance(stages, str):
        stages_list = [s.strip() for s in stages.split(",") if s.strip()]
    else:
        stages_list = list(stages)
    
    blast = incident.get("blast_radius", {})
    hop1_count = blast.get("hop1_subnet_peers_at_risk_count", 0)
    hop2_assets = blast.get("hop2_critical_assets_exposed", [])
    
    # 1. Executive Summary Paragraph
    target_names = [a.get("role", a.get("asset", "Critical Server")) for a in hop2_assets]
    targets_str = ", ".join(target_names) if target_names else "internal enterprise assets"
    
    summary = (
        f"On {ts_start}, external threat actor {attacker} launched a sophisticated multi-stage intrusion "
        f"targeting perimeter server {host}. Over an active campaign window of {duration:.1f} minutes, "
        f"the adversary executed {alerts} distinct malicious operations spanning {len(stages_list)} Kill Chain stages. "
        f"Using compromised domain credentials for user '{user}', the attacker established persistent Command & Control "
        f"and initiated lateral reconnaissance. The threat poses an immediate Risk Score of {score}/100 ({sev}), "
        f"threatening {hop1_count} local subnet hosts and directly exposing high-value crown jewels ({targets_str})."
    )
    
    # 2. Sequential Story Steps (Kill Chain narrative)
    steps = []
    
    # Check for initial access / exploit
    has_init = any("Initial Access" in s or "Exploit" in s for s in stages_list)
    if has_init or attacker:
        steps.append({
            "stage": "1. Perimeter Breach (Initial Access)",
            "narrative": (
                f"The attacker initiated inbound targeting from external IP {attacker} against {host}, "
                f"exploiting edge-facing services to bypass boundary inspection and gain initial foothold."
            )
        })
        
    # Check for execution / privilege escalation
    has_exec = any("Execution" in s or "Privilege" in s for s in stages_list)
    if has_exec or user != "system":
        steps.append({
            "stage": "2. Credential Hijack & Privilege Escalation",
            "narrative": (
                f"Upon penetrating {host}, the adversary harvested internal authentication tokens and assumed "
                f"the security context of user account '{user}', allowing evasion of perimeter identity controls."
            )
        })
        
    # Check for lateral movement / discovery
    has_lat = any("Lateral" in s or "Discovery" in s for s in stages_list)
    if has_lat or hop1_count > 0:
        steps.append({
            "stage": "3. Internal Network Reconnaissance & Expansion",
            "narrative": (
                f"The adversary conducted automated port and host sweeps across subnet 10.10.1.0/24, discovering "
                f"{hop1_count} adjacent peer systems and mapping reachable internal routes."
            )
        })
        
    # Check for C2 / Exfiltration
    has_c2 = any("Command" in s or "Exfil" in s for s in stages_list)
    if has_c2:
        steps.append({
            "stage": "4. Command & Control (C2) and Data Staging",
            "narrative": (
                f"Adversary established encrypted bidirectional beaconing channels out to remote infrastructure, "
                f"staging sensitive perimeter logs and establishing persistent reverse interactive control."
            )
        })
        
    # Predictive Lookahead Threat
    if hop2_assets:
        asset_details = "; ".join([f"{a.get('asset')} ({a.get('role')} via {a.get('exposure_vector')})" for a in hop2_assets])
        steps.append({
            "stage": "5. Predictive Blast Vector (Next 2-Hops)",
            "narrative": (
                f"Lookahead graph projection reveals the adversary is within 2 hops of complete domain takeover: "
                f"{asset_details}. If unmitigated, full enterprise credential domain dominance is imminent."
            )
        })

    # 3. Business Impact
    impact = (
        f"Critical Threat: High probability of lateral domain takeover. Exposure of Domain Controller (10.10.99.1) "
        f"risks enterprise-wide identity compromise, unauthorized data exfiltration from Database Vault (10.10.99.10), "
        f"and enterprise-scale ransomware deployment."
    )
    
    # 4. Immediate Recommended Action
    actions = [
        f"Immediately null-route / drop perimeter inbound traffic from adversary IP: {attacker}",
        f"Sever network connection for compromised host {host} and migrate to isolated quarantine VLAN",
        f"Force an immediate enterprise password reset and Kerberos ticket invalidation for user '{user}'",
        f"Apply strict firewall egress rules to block external beaconing to unauthorized C2 endpoints"
    ]
    
    return {
        "summary": summary,
        "story_steps": steps,
        "business_impact": impact,
        "actions": actions
    }
