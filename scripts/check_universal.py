import duckdb

conn = duckdb.connect('out/killchain.duckdb')

exploit_query = """
SELECT process_name, count(1) 
FROM events 
WHERE event_type = 'ips_alert' 
  AND (
    process_name LIKE '%.Overflow%' 
    OR process_name LIKE '%.Traversal%' 
    OR process_name LIKE '%.Injection%' 
    OR process_name LIKE '%.Execution%' 
    OR process_name LIKE '%.RCE%' 
    OR process_name LIKE '%.Handling%' 
    OR process_name LIKE '%.Deserialization%' 
    OR process_name LIKE '%.Upload%' 
    OR process_name LIKE '%Log4j%' 
    OR process_name LIKE '%SSLVPN%' 
    OR process_name LIKE '%XSS%' 
    OR process_name LIKE '%Exploit%'
  )
GROUP BY process_name 
ORDER BY count(1) DESC
"""

rows = conn.execute(exploit_query).fetchall()
print(f"Total True Exploit Events: {sum(r[1] for r in rows):,}")
print(f"Total Unique Exploit Signatures: {len(rows)}")
print("\nBreakdown of True Exploits:")
for r in rows:
    print(f"  {r[0]:<55}: {r[1]}")
