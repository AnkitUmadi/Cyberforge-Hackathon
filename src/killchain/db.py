import duckdb
import os

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    event_id BIGINT,
    src_file INTEGER,
    row_in_file BIGINT,
    timestamp TIMESTAMP,
    event_type VARCHAR,
    usr VARCHAR,
    src_host VARCHAR,
    dest_host VARCHAR,
    src_ip VARCHAR,
    dest_ip VARCHAR,
    status VARCHAR,
    process_name VARCHAR,
    command VARCHAR,
    details VARCHAR
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id BIGINT,
    rule_id VARCHAR,
    technique_id VARCHAR,
    technique_name VARCHAR,
    stage VARCHAR,
    severity VARCHAR,
    ts_start TIMESTAMP,
    ts_end TIMESTAMP,
    usr VARCHAR,
    src_host VARCHAR,
    dest_host VARCHAR,
    src_ip VARCHAR,
    dest_ip VARCHAR,
    event_count BIGINT,
    extra VARCHAR
);

CREATE TABLE IF NOT EXISTS alert_evidence (
    alert_id BIGINT,
    event_id BIGINT
);

CREATE TABLE IF NOT EXISTS incidents (
    incident_id BIGINT,
    title VARCHAR,
    severity VARCHAR,
    root_entity VARCHAR,
    target_entity VARCHAR,
    ts_start TIMESTAMP,
    ts_end TIMESTAMP,
    alert_count INTEGER,
    stages_covered VARCHAR,
    path_summary VARCHAR,
    lookahead_2hop VARCHAR
);

CREATE TABLE IF NOT EXISTS incident_alerts (
    incident_id BIGINT,
    alert_id BIGINT,
    hop_order INTEGER
);
"""

def get_connection(db_path: str, memory_limit: str = "4GB", threads: int = 4, temp_dir: str = None):
    conn = duckdb.connect(db_path)
    conn.execute(f"SET memory_limit='{memory_limit}';")
    conn.execute(f"SET threads={threads};")
    if temp_dir:
        os.makedirs(temp_dir, exist_ok=True)
        conn.execute(f"SET temp_directory='{temp_dir.replace(chr(92), '/')}';")
    
    # Create private IP detection macro
    conn.execute("""
    CREATE OR REPLACE MACRO is_private_ip(ip) AS (
        ip LIKE '10.%' OR 
        ip LIKE '192.168.%' OR 
        regexp_matches(ip, '^172[.](1[6-9]|2[0-9]|3[01])[.]')
    );
    """)
    return conn

def init_db(conn):
    conn.execute(DB_SCHEMA)
