import duckdb

conn = duckdb.connect('out/killchain.duckdb')

bf_network = conn.execute("""
    SELECT count(1) 
    FROM events 
    WHERE event_type = 'ips_alert' 
      AND (process_name LIKE '%Brute.Force%' OR process_name LIKE '%Brute%')
""").fetchone()[0]

xss_count = conn.execute("""
    SELECT count(1) 
    FROM events 
    WHERE event_type = 'ips_alert' AND process_name LIKE '%XSS%'
""").fetchone()[0]

print(f"Network Brute Force events (SSH/RDP): {bf_network}")
print(f"XSS events: {xss_count}")
