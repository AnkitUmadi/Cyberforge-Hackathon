import sys
sys.path.insert(0, ".")
from src.killchain.db import get_connection

conn = get_connection('out/killchain.duckdb')
inc = conn.execute("SELECT incident_id, alert_count, root_entity, adversary_ip, duration_minutes FROM incidents WHERE root_entity = '10.10.20.11' OR target_entity = '10.10.20.11'").fetchall()
print('Incidents matching 10.10.20.11:', inc)

if inc:
    inc_id = inc[0][0]
    hops = conn.execute(f"""
        SELECT ia.hop_order, a.stage, a.technique_name, a.technique_id, a.src_ip, a.dest_ip, a.ts_start
        FROM incident_alerts ia
        JOIN alerts a ON ia.alert_id = a.alert_id
        WHERE ia.incident_id = {inc_id}
        ORDER BY ia.hop_order ASC
    """).fetchall()
    print(f"\nTotal hops for Incident #{inc_id}: {len(hops)}")
    for h in hops[:8]:
        print(f"  Hop {h[0]}: [{h[1]}] {h[2]} ({h[3]}) {h[4]} -> {h[5]} @ {h[6]}")
    print("  ...")
    for h in hops[-5:]:
        print(f"  Hop {h[0]}: [{h[1]}] {h[2]} ({h[3]}) {h[4]} -> {h[5]} @ {h[6]}")
