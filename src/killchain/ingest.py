import re
import json
import time
import os
import pyarrow as pa
from typing import List, Dict, Any
from .db import get_connection, init_db

KV_REGEX = re.compile(r'([a-zA-Z0-9_]+)=(?:"([^"]*)"|(\S+))')

def normalize_log_record(raw: Dict[str, str], file_idx: int, row_idx: int) -> Dict[str, Any]:
    event_id = file_idx * 4294967296 + row_idx
    
    # Timestamp
    d_str = raw.get('date', '1970-01-01')
    t_str = raw.get('time', '00:00:00')
    ts = f"{d_str} {t_str}"
    
    # Event type mapping
    t = raw.get('type', '')
    st = raw.get('subtype', '')
    action = raw.get('action', '')
    status_raw = raw.get('status', '')
    
    if st == 'system' and (action == 'login' or 'login' in raw.get('logdesc', '').lower()):
        event_type = 'login'
    elif t == 'traffic' and st == 'forward':
        event_type = 'network_connection'
    elif st == 'ips':
        event_type = 'ips_alert'
    elif st == 'virus':
        event_type = 'virus_alert'
    elif st == 'webfilter':
        event_type = 'webfilter'
    elif st == 'dns':
        event_type = 'dns_query'
    else:
        event_type = st if st else t or 'unknown'

    # User
    usr = raw.get('user')
    
    # Hosts
    src_host = raw.get('srcintf') or raw.get('devname')
    dest_host = raw.get('hostname') or raw.get('dstintf')
    
    # IPs
    src_ip = raw.get('srcip')
    dest_ip = raw.get('dstip')
    
    # Status
    if status_raw == 'failed' or 'fail' in raw.get('logdesc', '').lower():
        status = 'FAILURE'
    elif action in ('accept', 'pass', 'success'):
        status = 'SUCCESS'
    elif action in ('blocked', 'deny', 'dropped'):
        status = 'BLOCKED'
    else:
        status = status_raw.upper() if status_raw else action.upper() if action else 'UNKNOWN'
        
    # Process / Threat name
    process_name = raw.get('attack') or raw.get('virus') or raw.get('app') or raw.get('service')
    
    # Command / Message / URL
    command = raw.get('url') or raw.get('msg') or raw.get('logdesc')
    
    # Remaining fields into details JSON
    standard_keys = {'date', 'time', 'eventtime', 'tz', 'devname', 'devid', 'type', 'subtype', 
                     'user', 'srcintf', 'dstintf', 'srcip', 'dstip', 'status', 'action', 
                     'attack', 'virus', 'app', 'service', 'url', 'msg', 'logdesc', 'hostname'}
    details_dict = {k: v for k, v in raw.items() if k not in standard_keys}
    details = json.dumps(details_dict) if details_dict else None
    
    return {
        'event_id': event_id,
        'src_file': file_idx,
        'row_in_file': row_idx,
        'timestamp': ts,
        'event_type': event_type,
        'usr': usr,
        'src_host': src_host,
        'dest_host': dest_host,
        'src_ip': src_ip,
        'dest_ip': dest_ip,
        'status': status,
        'process_name': process_name,
        'command': command,
        'details': details
    }

def ingest_file(file_path: str, conn, file_idx: int = 0, batch_size: int = 100000, max_lines: int = None):
    print(f"Ingesting {file_path} (File index {file_idx})...")
    start_time = time.time()
    
    batch = []
    total_rows = 0
    skipped_rows = 0
    
    schema = pa.schema([
        ('event_id', pa.int64()),
        ('src_file', pa.int32()),
        ('row_in_file', pa.int64()),
        ('timestamp', pa.string()),
        ('event_type', pa.string()),
        ('usr', pa.string()),
        ('src_host', pa.string()),
        ('dest_host', pa.string()),
        ('src_ip', pa.string()),
        ('dest_ip', pa.string()),
        ('status', pa.string()),
        ('process_name', pa.string()),
        ('command', pa.string()),
        ('details', pa.string()),
    ])
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            matches = KV_REGEX.findall(line)
            if not matches:
                skipped_rows += 1
                continue
            raw = {k: v1 if v1 else v2 for k, v1, v2 in matches}
            
            try:
                rec = normalize_log_record(raw, file_idx, total_rows)
                batch.append(rec)
                total_rows += 1
            except Exception as e:
                skipped_rows += 1
                continue
                
            if len(batch) >= batch_size:
                _flush_batch(conn, batch, schema)
                batch = []
                print(f"  Ingested {total_rows:,} rows so far... ({total_rows / (time.time() - start_time):,.0f} rows/s)")

            if max_lines and total_rows >= max_lines:
                print(f"Reached maximum line limit of {max_lines:,}.")
                break
                
    if batch:
        _flush_batch(conn, batch, schema)
        
    duration = time.time() - start_time
    print(f"Completed ingest of {total_rows:,} rows ({skipped_rows} skipped) in {duration:.2f}s ({total_rows/duration:,.0f} rows/s)")

def _flush_batch(conn, batch: List[Dict[str, Any]], schema: pa.Schema):
    pydict = {col: [row[col] for row in batch] for col in schema.names}
    arrow_table = pa.Table.from_pydict(pydict, schema=schema)
    conn.register('temp_arrow_batch', arrow_table)
    conn.execute("""
    INSERT INTO events 
    SELECT 
        event_id, 
        src_file, 
        row_in_file, 
        try_cast(timestamp AS TIMESTAMP) as timestamp, 
        event_type, 
        usr, 
        src_host, 
        dest_host, 
        src_ip, 
        dest_ip, 
        status, 
        process_name, 
        command, 
        details 
    FROM temp_arrow_batch;
    """)
    conn.unregister('temp_arrow_batch')

if __name__ == "__main__":
    import argparse
    from pathlib import Path
    ROOT = Path(__file__).resolve().parent.parent.parent

    parser = argparse.ArgumentParser(description="Cyberforge Fast Log Ingest Engine")
    parser.add_argument("--log", type=str, default=str(ROOT / "data" / "sample_100MB.log"), help="Path to log file")
    parser.add_argument("--db", type=str, default=str(ROOT / "out" / "killchain.duckdb"), help="Path to DuckDB")
    parser.add_argument("--batch-size", type=int, default=100000, help="Ingestion batch size")
    parser.add_argument("--max-lines", type=int, default=None, help="Maximum lines to ingest")
    parser.add_argument("--clean", action="store_true", help="Clean events table before ingestion")
    args = parser.parse_args()

    conn = get_connection(args.db)
    init_db(conn)
    if args.clean:
        print("Clearing events table for fresh ingestion...")
        conn.execute("DELETE FROM events;")

    ingest_file(args.log, conn, file_idx=0, batch_size=args.batch_size, max_lines=args.max_lines)
    
    count = conn.execute("SELECT count(*) FROM events;").fetchone()[0]
    print(f"Total rows in DuckDB events table: {count:,}")
