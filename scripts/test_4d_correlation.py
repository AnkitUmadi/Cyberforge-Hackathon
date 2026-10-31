import duckdb
from collections import defaultdict
from datetime import timedelta

conn = duckdb.connect('out/killchain.duckdb')

# Fetch all alerts
alerts = conn.execute("""
    SELECT 
        alert_id,
        rule_id,
        technique_id,
        technique_name,
        stage,
        severity,
        ts_start,
        ts_end,
        usr,
        src_ip,
        dest_ip,
        event_count,
        extra,
        is_private_ip(src_ip) as src_is_priv,
        is_private_ip(dest_ip) as dest_is_priv
    FROM alerts
    ORDER BY ts_start ASC
""").fetchall()

print(f"Loaded {len(alerts):,} alerts.")

# Group alerts by host
host_alerts = defaultdict(list)
for a in alerts:
    (alert_id, rule_id, tech_id, tech_name, stage, sev, ts_start, ts_end,
     usr, src_ip, dest_ip, ev_cnt, extra, src_priv, dst_priv) = a

    if src_priv:
        host_alerts[src_ip].append(a)
    if dst_priv and dest_ip != src_ip:
        host_alerts[dest_ip].append(a)

WINDOW_MINUTES = 120  # 2-hour sliding window

incidents = []
for host, alist in host_alerts.items():
    # Sort chronologically
    sorted_alerts = sorted(alist, key=lambda x: x[6])
    
    # Split into temporal sessions using sliding window
    sessions = []
    current_session = []
    
    for alt in sorted_alerts:
        if not current_session:
            current_session.append(alt)
        else:
            prev_ts = current_session[-1][6]
            curr_ts = alt[6]
            if (curr_ts - prev_ts) <= timedelta(minutes=WINDOW_MINUTES):
                current_session.append(alt)
            else:
                sessions.append(current_session)
                current_session = [alt]
    if current_session:
        sessions.append(current_session)

    # Check corroboration gating on each session
    for sess in sessions:
        stages = sorted(list(set(x[4] for x in sess)))
        rules = sorted(list(set(x[1] for x in sess)))
        if len(stages) >= 2:
            # Extract user if present
            users = set(x[8] for x in sess if x[8] is not None)
            usr = ", ".join(users) if users else "unauthenticated"
            
            # Extract external adversary IPs
            adv_ips = set()
            for x in sess:
                if not x[13] and x[9]:  # src is external
                    adv_ips.add(x[9])
                if not x[14] and x[10]: # dst is external
                    adv_ips.add(x[10])
            
            ts_start = sess[0][6]
            ts_end = sess[-1][7]
            duration_mins = (ts_end - ts_start).total_seconds() / 60.0

            incidents.append({
                "host": host,
                "usr": usr,
                "adversary_ips": list(adv_ips)[:3],
                "ts_start": ts_start,
                "ts_end": ts_end,
                "duration_mins": round(duration_mins, 1),
                "stages": stages,
                "rules": rules,
                "alerts": sess
            })

print(f"Total Corroborated 4D Incidents (Host, User, IP, Sliding Window): {len(incidents):,}")

# Sort by stages and alerts
incidents.sort(key=lambda x: (len(x["stages"]), len(x["alerts"])), reverse=True)

print("\n--- TOP 5 CORRELATED 4D INCIDENTS ---")
for i, inc in enumerate(incidents[:5], 1):
    print(f"\nIncident #{i}: Host {inc['host']} | User: {inc['usr']} | Duration: {inc['duration_mins']} mins")
    print(f"  Timeline: {inc['ts_start']} -> {inc['ts_end']}")
    print(f"  Adversary IPs: {', '.join(inc['adversary_ips'])}")
    print(f"  Stages ({len(inc['stages'])}): {', '.join(inc['stages'])}")
    print(f"  Alerts: {len(inc['alerts'])}")
    for step_idx, alt in enumerate(inc["alerts"][:6], 1):
        print(f"    Step {step_idx}: [{alt[6].strftime('%H:%M:%S')}] {alt[4]:<20} | {alt[3]} ({alt[9]} -> {alt[10]})")
