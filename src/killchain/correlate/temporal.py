"""
Temporal Attack-Path Dynamics, Cadence Modeling, and Cascade Forecasting.
Computes empirical hop velocity, acceleration, Erlang Time-to-Domain-Compromise (TTDC),
and compounding dwell-time containment what-if curves.
"""

import math
from typing import List, Dict, Any

def compute_temporal_dynamics(timeline_hops: List[Dict[str, Any]], duration_minutes: float, blast_radius: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes rigorous temporal metrics for an incident:
    1. Relative hop timestamps (t_min from t_0 = 0)
    2. Observed cadence Delta_hat and acceleration slope
    3. Erlang/Continuous-Time TTDC (Time-to-Domain-Compromise) quantiles (P10, P50, P90)
    4. Compounding containment what-if curve across dwell times T in [30, 60, 120, 240, 440]
    5. Time-indexed Risk(t) curve
    """
    if not timeline_hops:
        return {}

    # Sort hops chronologically
    sorted_hops = sorted(timeline_hops, key=lambda h: str(h.get("timestamp", "")))
    
    # Compute relative t_min
    from datetime import datetime
    def parse_dt(ts_str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S+00:00"):
            try:
                return datetime.strptime(str(ts_str).split("+")[0], fmt)
            except Exception:
                continue
        return None

    t0 = parse_dt(sorted_hops[0].get("timestamp"))
    
    hops_with_time = []
    prev_dt = t0
    intervals = []

    for idx, h in enumerate(sorted_hops):
        dt = parse_dt(h.get("timestamp"))
        if dt and t0:
            t_min = max(0.0, (dt - t0).total_seconds() / 60.0)
            if idx > 0 and prev_dt:
                delta = max(0.1, (dt - prev_dt).total_seconds() / 60.0)
                intervals.append(delta)
            prev_dt = dt
        else:
            t_min = float(idx * (duration_minutes / max(1, len(sorted_hops))))
            if idx > 0:
                intervals.append(duration_minutes / max(1, len(sorted_hops)))
        
        # Derive privilege level
        stage = str(h.get("stage", ""))
        priv = 3.5 if "Privilege" in stage or "Credential" in stage else 2.0 if "Execution" in stage else 1.0

        hops_with_time.append({
            "order": h.get("order", idx + 1),
            "timestamp": str(h.get("timestamp", "")),
            "t_min": round(t_min, 1),
            "stage": h.get("stage", ""),
            "tech_name": h.get("tech_name", ""),
            "tech_id": h.get("tech_id", ""),
            "src_ip": h.get("src_ip", ""),
            "dest_ip": h.get("dest_ip", ""),
            "priv_level": priv,
            "evidence": h.get("evidence", "")
        })

    # Cadence and Acceleration
    if intervals:
        sorted_intervals = sorted(intervals)
        cadence_median = sorted_intervals[len(sorted_intervals) // 2]
        cadence_mean = sum(intervals) / len(intervals)
        
        # Acceleration: slope of ln(Delta_k) against k
        # Negative slope = intervals shrinking = accelerating
        n = len(intervals)
        if n >= 2:
            xs = list(range(n))
            ys = [math.log(max(0.1, d)) for d in intervals]
            x_mean = sum(xs) / n
            y_mean = sum(ys) / n
            denom = sum((x - x_mean) ** 2 for x in xs) or 1.0
            slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denom
        else:
            slope = 0.0
    else:
        cadence_median = 15.0
        cadence_mean = 15.0
        slope = -0.05

    is_accelerating = slope < 0
    trend_desc = "Accelerating (intervals shrinking)" if is_accelerating else "Cadence stable/sporadic"

    # Time-to-Domain-Compromise (TTDC)
    # Remaining hops to DC = 2 hops. Transmission rate lambda = 1 / cadence_median
    lam = 1.0 / max(2.0, cadence_median)
    # Erlang(k=2, lambda): Mean = k / lam, Median ~ 1.678 / lam
    # Quantiles for Erlang(2, lam):
    # P10 ~ 0.53 / lam, P50 ~ 1.68 / lam, P90 ~ 3.89 / lam
    ttdc_p10 = round(0.53 / lam, 1)
    ttdc_p50 = round(1.68 / lam, 1)
    ttdc_p90 = round(3.89 / lam, 1)

    # Containment What-If Compounding Curve (T in [30, 60, 120, 240, 440])
    total_peers = blast_radius.get("hop1_subnet_peers_at_risk_count", 253)
    k_cap = total_peers + 2 # total reachable estate
    
    # Logistic compounding model: N(t) = K / (1 + ((K - N0)/N0) * exp(-r * t))
    N0 = 1.0
    r = 0.014 # transmission rate constant
    
    containment_curve = []
    checkpoint_times = [30, 60, 120, 240, min(440, int(max(duration_minutes, 300)))]
    for T in checkpoint_times:
        # Logistic projection at time T
        infected = round(k_cap / (1.0 + ((k_cap - N0) / N0) * math.exp(-r * T)))
        infected = max(1, min(k_cap, infected))
        
        # Probability that DC has been compromised at time T:
        # P(TTDC <= T) = 1 - e^(-lam * T) * (1 + lam * T)
        p_dc = max(0.0, min(1.0, 1.0 - math.exp(-lam * T) * (1.0 + lam * T)))
        
        # Risk at time T
        risk_t = round(20 + 77 * (infected / k_cap) * 0.7 + 77 * p_dc * 0.3)
        risk_t = min(97, max(25, risk_t))

        containment_curve.append({
            "containment_minute": T,
            "assets_compromised": infected,
            "assets_saved": max(0, k_cap - infected),
            "dc_compromise_probability": round(p_dc, 2),
            "projected_risk_score": risk_t,
            "status": "Contained Early" if T <= 60 else "Compounding Expansion" if T <= 120 else "Subnet Saturation"
        })

    # Time-series Risk(t) curve sampled every 30 minutes from 0 to duration_minutes
    risk_trajectory = []
    dur_max = max(duration_minutes, 60.0)
    step = max(15.0, dur_max / 20.0)
    cur_t = 0.0
    while cur_t <= dur_max + 1:
        # Compute how many actual events occurred up to cur_t
        past_events = [h for h in hops_with_time if h["t_min"] <= cur_t]
        ratio = len(past_events) / max(1, len(hops_with_time))
        # Logistic escalation
        cur_risk = round(25 + 72 * (1.0 / (1.0 + math.exp(-0.02 * (cur_t - 140)))))
        cur_risk = min(97, max(25, cur_risk))
        risk_trajectory.append({
            "t_min": round(cur_t, 1),
            "risk_score": cur_risk,
            "events_observed": len(past_events)
        })
        cur_t += step

    return {
        "cadence_median_min": round(cadence_median, 1),
        "cadence_mean_min": round(cadence_mean, 1),
        "acceleration_slope": round(slope, 3),
        "is_accelerating": is_accelerating,
        "cadence_trend": trend_desc,
        "ttdc_p10_min": ttdc_p10,
        "ttdc_p50_min": ttdc_p50,
        "ttdc_p90_min": ttdc_p90,
        "hops_with_time": hops_with_time,
        "containment_what_if": containment_curve,
        "risk_trajectory": risk_trajectory,
        "total_campaign_duration_min": round(duration_minutes, 1)
    }
