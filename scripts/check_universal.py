import duckdb

conn = duckdb.connect('out/killchain.duckdb')

ips_total = conn.execute("SELECT count(1) FROM events WHERE event_type = 'ips_alert'").fetchone()[0]
virus_total = conn.execute("SELECT count(1) FROM events WHERE event_type = 'virus_alert'").fetchone()[0]
web_blocked = conn.execute("SELECT count(1) FROM events WHERE event_type = 'webfilter' AND status = 'BLOCKED'").fetchone()[0]
login_failures = conn.execute("SELECT count(1) FROM events WHERE event_type = 'login' AND status = 'FAILURE'").fetchone()[0]

print(f"Total IPS alerts: {ips_total:,}")
print(f"Total Virus alerts: {virus_total:,}")
print(f"Total Webfilter blocked: {web_blocked:,}")
print(f"Total Login failures: {login_failures:,}")

# How many failed logins are part of bursts >= 5 or >= 10?
burst_5 = conn.execute("""
    WITH bf AS (
        SELECT count(1) as cnt 
        FROM events 
        WHERE event_type = 'login' AND status = 'FAILURE'
        GROUP BY usr, src_ip
        HAVING count(1) >= 5
    )
    SELECT sum(cnt) FROM bf
""").fetchone()[0]
print(f"Failed logins in bursts >= 5: {burst_5:,}")

burst_20 = conn.execute("""
    WITH bf AS (
        SELECT count(1) as cnt 
        FROM events 
        WHERE event_type = 'login' AND status = 'FAILURE'
        GROUP BY usr, src_ip
        HAVING count(1) >= 20
    )
    SELECT sum(cnt) FROM bf
""").fetchone()[0]
print(f"Failed logins in bursts >= 20: {burst_20:,}")
