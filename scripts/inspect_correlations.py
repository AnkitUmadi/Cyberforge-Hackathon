import duckdb

conn = duckdb.connect('out/killchain.duckdb')

# Check which external IPs communicate with multiple internal hosts
multi_host_attackers = conn.execute("""
    SELECT src_ip, count(distinct dest_ip) as internal_targets, count(1) as alert_count
    FROM alerts
    WHERE NOT is_private_ip(src_ip) AND is_private_ip(dest_ip)
    GROUP BY src_ip
    HAVING count(distinct dest_ip) >= 2
    ORDER BY internal_targets DESC
    LIMIT 10
""").fetchall()

print("External IPs targeting multiple internal hosts:")
for r in multi_host_attackers:
    print(f"  Attacker {r[0]:<18} -> targets {r[1]} internal hosts ({r[2]} alerts)")

# Check C2 servers contacted by multiple internal hosts
multi_host_c2 = conn.execute("""
    SELECT dest_ip, count(distinct src_ip) as infected_hosts, count(1) as alert_count
    FROM alerts
    WHERE is_private_ip(src_ip) AND NOT is_private_ip(dest_ip) AND rule_id = 'C2-001'
    GROUP BY dest_ip
    HAVING count(distinct src_ip) >= 2
    ORDER BY infected_hosts DESC
    LIMIT 10
""").fetchall()

print("\nC2 servers contacted by multiple internal hosts:")
for r in multi_host_c2:
    print(f"  C2 IP {r[0]:<18} <- contacted by {r[1]} internal hosts ({r[2]} alerts)")
