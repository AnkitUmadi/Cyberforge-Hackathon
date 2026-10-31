import os
import glob
import time
import yaml
from pathlib import Path
from ..db import get_connection

def load_rules(rules_dir: str):
    """Load and validate all YAML detection rules from the rules directory."""
    rules = []
    required_keys = ["id", "technique_id", "technique_name", "stage", "severity", "sql"]
    
    for filepath in sorted(glob.glob(os.path.join(rules_dir, "*.yml"))):
        with open(filepath, "r", encoding="utf-8") as f:
            r = yaml.safe_load(f)
            # Validate rule structure
            missing = [k for k in required_keys if k not in r]
            if missing:
                raise ValueError(f"Rule file {filepath} missing required fields: {missing}")
            r["filepath"] = filepath
            rules.append(r)
    return rules

def run_detection_rules(conn, rules_dir: str):
    """Compile and execute all YAML rules against DuckDB, populating the alerts table."""
    rules = load_rules(rules_dir)
    print("=" * 75)
    print(f"  EXECUTING DETECTION RULES ({len(rules)} rules loaded from {rules_dir})")
    print("=" * 75)
    
    # Reset alerts table before running
    conn.execute("DELETE FROM alerts;")
    conn.execute("DELETE FROM alert_evidence;")
    
    alert_offset = 1
    total_alerts = 0
    start_total_time = time.time()
    
    summary = []
    
    for r in rules:
        start_rule_time = time.time()
        sql = r["sql"]
        params = r.get("params") or {}
        
        # Substitute parameters
        for k, v in params.items():
            sql = sql.replace(f"{{{{{k}}}}}", str(v))
            
        temp_view = f"rule_res_{r['id'].replace('-', '_')}"
        conn.execute(f"CREATE OR REPLACE TEMP TABLE {temp_view} AS {sql};")
        
        count = conn.execute(f"SELECT count(*) FROM {temp_view};").fetchone()[0]
        duration_ms = (time.time() - start_rule_time) * 1000
        
        if count > 0:
            conn.execute(f"""
            INSERT INTO alerts
            SELECT 
                {alert_offset} + row_number() OVER (ORDER BY ts_start, usr, src_host, dest_host, src_ip, dest_ip) as alert_id,
                '{r['id']}' as rule_id,
                '{r['technique_id']}' as technique_id,
                '{r['technique_name']}' as technique_name,
                '{r['stage']}' as stage,
                '{r['severity']}' as severity,
                ts_start,
                ts_end,
                usr,
                src_host,
                dest_host,
                src_ip,
                dest_ip,
                event_count,
                extra
            FROM {temp_view};
            """)
            alert_offset += count
            total_alerts += count
            status_flag = "[HIT]"
        else:
            status_flag = "[MISS]"
            
        summary.append({
            "id": r["id"],
            "technique": r["technique_name"],
            "stage": r["stage"],
            "severity": r["severity"],
            "count": count,
            "duration_ms": duration_ms,
            "status": status_flag
        })
        
        conn.execute(f"DROP TABLE IF EXISTS {temp_view};")
        
    total_duration = time.time() - start_total_time
    
    # Print clean summary table
    print(f"\n{'ID':<10} {'STAGE':<22} {'SEVERITY':<10} {'ALERTS':<8} {'TIME (ms)':<10} {'TECHNIQUE'}")
    print("-" * 75)
    for s in summary:
        print(f"{s['id']:<10} {s['stage']:<22} {s['severity']:<10} {s['count']:<8} {s['duration_ms']:<10.1f} {s['technique']}")
    print("-" * 75)
    print(f"Total Alerts Flagged: {total_alerts:,} in {total_duration:.2f}s")
    print("=" * 75)
    
    return total_alerts

if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent.parent.parent
    db_file = str(ROOT / "out" / "killchain.duckdb")
    rules_dir = str(ROOT / "config" / "rules")
    conn = get_connection(db_file)
    run_detection_rules(conn, rules_dir)
    conn.close()
