from typing import List, Dict, Any

def calculate_risk_score(stages: List[str], max_severity: str, host_ip: str, blast_radius: Dict[str, Any]) -> int:
    """
    Calculate deterministic Incident Risk Score (0 to 100).
    
    Formula:
      Score = Stage_Score (up to 50) 
            + Severity_Score (up to 25) 
            + Asset_Score (up to 15) 
            + Blast_Score (up to 10)
    """
    # 1. Kill Chain Stage Depth (Max 50 points)
    num_stages = len(stages)
    if num_stages >= 7:
        stage_score = 50
    elif num_stages >= 5:
        stage_score = 40
    elif num_stages >= 3:
        stage_score = 28
    elif num_stages >= 2:
        stage_score = 18
    else:
        stage_score = 10

    # 2. Maximum Technique Severity (Max 25 points)
    sev_upper = max_severity.upper()
    if sev_upper == "CRITICAL":
        sev_score = 25
    elif sev_upper == "HIGH":
        sev_score = 18
    elif sev_upper == "MEDIUM":
        sev_score = 10
    else:
        sev_score = 5

    # 3. Targeted Asset Criticality (Max 15 points)
    if host_ip.startswith("10.10.99."):
        # Management / Domain Controller / Active Directory
        asset_score = 15
    elif host_ip.startswith("10.10.20."):
        # Public-facing DMZ Web / App Server
        asset_score = 12
    elif host_ip.startswith("10.10."):
        # Corporate LAN workstation
        asset_score = 8
    else:
        asset_score = 5

    # 4. Predictive Blast Radius & Lookahead Exposure (Max 10 points)
    # Check if core Domain Controllers or database vaults are reachable at Hop 2
    critical_exposed = blast_radius.get("hop2_critical_assets_exposed", [])
    if any(a.get("criticality") == "CRITICAL" for a in critical_exposed):
        blast_score = 10
    elif critical_exposed:
        blast_score = 6
    else:
        blast_score = 3

    total_score = stage_score + sev_score + asset_score + blast_score
    return max(0, min(100, total_score))

def get_risk_level(score: int) -> str:
    """Map numeric risk score to categorical alert tier."""
    if score >= 85:
        return "CRITICAL"
    elif score >= 65:
        return "HIGH"
    elif score >= 45:
        return "MEDIUM"
    else:
        return "LOW"
