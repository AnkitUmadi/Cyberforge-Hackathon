import os
import json
import time
from datetime import datetime, timezone
import jinja2
from ..db import get_connection
from ..correlate.narrative import generate_plain_english_narrative
from ..correlate.temporal import compute_temporal_dynamics

def generate_report(db_path: str = "out/killchain.duckdb", template_path: str = "templates/incident_report.j2", out_path: str = "out/incident_report.html", top_n: int = 5):
    """
    Generate the official Executive Incident Report using Jinja2:
    - Attack Path as a Timeline
    - Attack Path as a Host & User Graph
    - Predictive 2-Hop Lookahead (What could the attacker reach next?)
    - Mathematical Risk Score (0 - 100)
    """
    print("=" * 75)
    print("  GENERATING EXECUTIVE INCIDENT REPORT (Jinja2 HTML Generator)")
    print("=" * 75)
    start_time = time.time()

    conn = get_connection(db_path)

    # 1. Query KPI metrics
    total_events = conn.execute("SELECT count(1) FROM events;").fetchone()[0]
    total_alerts = conn.execute("SELECT count(1) FROM alerts;").fetchone()[0]
    total_incidents = conn.execute("SELECT count(1) FROM incidents;").fetchone()[0]
    peak_risk_score = conn.execute("SELECT coalesce(max(risk_score), 0) FROM incidents;").fetchone()[0]

    # 2. Query Top Incidents
    inc_rows = conn.execute(f"""
        SELECT 
            incident_id, title, severity, risk_score, root_entity, adversary_ip,
            usr, target_entity, ts_start, ts_end, duration_minutes, alert_count,
            stages_covered, path_summary, lookahead_2hop
        FROM incidents
        ORDER BY risk_score DESC, alert_count DESC, incident_id ASC
        LIMIT {top_n}
    """).fetchall()

    top_incidents = []
    for inc in inc_rows:
        inc_id = inc[0]
        # Query ordered hops for timeline
        hop_rows = conn.execute(f"""
            SELECT 
                ia.hop_order, a.ts_start, a.stage, a.technique_name,
                a.technique_id, a.src_ip, a.dest_ip, a.extra
            FROM incident_alerts ia
            JOIN alerts a ON ia.alert_id = a.alert_id
            WHERE ia.incident_id = {inc_id}
            ORDER BY ia.hop_order ASC
        """).fetchall()

        timeline_hops = []
        for h in hop_rows:
            timeline_hops.append({
                "order": h[0],
                "timestamp": str(h[1]),
                "stage": h[2],
                "tech_name": h[3],
                "tech_id": h[4],
                "src_ip": h[5],
                "dest_ip": h[6],
                "evidence": h[7] or "Direct signature hit"
            })

        blast_radius = json.loads(inc[14]) if inc[14] else {}

        inc_dict = {
            "incident_id": inc[0],
            "title": inc[1],
            "severity": inc[2],
            "risk_score": inc[3],
            "root_entity": inc[4],
            "adversary_ip": inc[5],
            "usr": inc[6],
            "target_entity": inc[7],
            "ts_start": str(inc[8]),
            "ts_end": str(inc[9]),
            "duration_minutes": inc[10],
            "alert_count": inc[11],
            "stages_covered": inc[12],
            "path_summary": inc[13],
            "blast_radius": blast_radius,
            "timeline_hops": timeline_hops
        }
        inc_dict["narrative"] = generate_plain_english_narrative(inc_dict)
        inc_dict["temporal"] = compute_temporal_dynamics(
            timeline_hops, inc[10], blast_radius,
            root_entity=inc[4], adversary_ip=inc[5], usr=inc[6]
        )
        top_incidents.append(inc_dict)

    conn.close()

    # 3. Render Jinja2 Template
    template_dir = os.path.dirname(os.path.abspath(template_path))
    template_file = os.path.basename(template_path)

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)
    template = env.get_template(template_file)

    rendered_html = template.render(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        total_events=total_events,
        total_alerts=total_alerts,
        total_incidents=total_incidents,
        peak_risk_score=peak_risk_score,
        top_incidents=top_incidents,
        incidents_json=json.dumps(top_incidents)
    )

    # 4. Save to output path
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    duration = time.time() - start_time
    print(f"Report Successfully Rendered: {out_path} ({duration:.2f}s)")
    print(f"Dossiers Included: {len(top_incidents)} Critical Incidents")
    print(f"Peak Threat Risk Score: {peak_risk_score} / 100")
    print("=" * 75)
    return out_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cyberforge Incident Report Generator")
    parser.add_argument("--db", type=str, default="out/killchain.duckdb", help="Path to DuckDB database")
    parser.add_argument("--template", type=str, default="templates/incident_report.j2", help="Path to Jinja2 template")
    parser.add_argument("--out", type=str, default="out/incident_report.html", help="Output HTML file path")
    parser.add_argument("--top", type=int, default=5, help="Number of top incidents to detail")
    args = parser.parse_args()

    generate_report(args.db, args.template, args.out, top_n=args.top)
