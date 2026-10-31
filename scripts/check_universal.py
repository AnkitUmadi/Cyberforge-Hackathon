import duckdb

conn = duckdb.connect('out/killchain.duckdb')

# Count all IPS alerts in the database
total_ips = conn.execute("SELECT count(1) FROM events WHERE event_type = 'ips_alert'").fetchone()[0]
print(f"Total IPS alert events in database: {total_ips:,}")

# Test universal categorization query
query = """
SELECT 
  CASE 
    WHEN process_name LIKE '%Mirai%' OR process_name LIKE '%Cobalt%' OR process_name LIKE '%Beacon%' OR process_name LIKE '%Botnet%' OR process_name LIKE '%Backdoor%' OR process_name LIKE '%C2%' THEN 'C2-001'
    WHEN process_name LIKE '%ZeroLogon%' OR process_name LIKE '%.Escalat%' OR process_name LIKE '%Privilege%' OR process_name LIKE '%Elevat%' THEN 'PRV-001'
    WHEN process_name LIKE '%Password%' OR process_name LIKE '%dump%' OR process_name LIKE '%mimikatz%' OR process_name LIKE '%Credential%' THEN 'CRED-001'
    WHEN process_name LIKE '%Zone.Transfer%' OR process_name LIKE '%Information.Disclosure%' OR process_name LIKE '%Scan%' OR process_name LIKE '%Discovery%' OR process_name LIKE '%Enumerat%' THEN 'DISC-001'
    WHEN process_name LIKE '%Brute.Force%' OR process_name LIKE '%Brute%' THEN 'BF-002'
    ELSE 'EXP-001'
  END as assigned_rule,
  count(1) as total_events,
  count(distinct process_name) as unique_attacks
FROM events
WHERE event_type = 'ips_alert'
GROUP BY 1
ORDER BY total_events DESC
"""

print("\nUniversal IPS Categorization Results:")
for r in conn.execute(query).fetchall():
    print(f"  Rule {r[0]:<10}: {r[1]:>6,} events across {r[2]:>2} unique attack signatures")

uncategorized = conn.execute("""
    SELECT count(1) 
    FROM events 
    WHERE event_type = 'ips_alert' 
      AND (process_name IS NULL OR process_name = '')
""").fetchone()[0]
print(f"\nUncategorized / Null IPS events: {uncategorized}")
