from src.killchain.db import get_connection

conn = get_connection('out/killchain.duckdb')

# Breakdown of Denominator (true_threats)
v_cnt = conn.execute("SELECT count(1) FROM events WHERE event_type = 'virus_alert'").fetchone()[0]
w_cnt = conn.execute("SELECT count(1) FROM events WHERE event_type = 'webfilter' AND (status = 'BLOCKED' OR details LIKE '%Phishing%')").fetchone()[0]
ips_cnt = conn.execute("""
    SELECT count(1) FROM events 
    WHERE event_type = 'ips_alert' 
    AND NOT (process_name LIKE '%.security.%' OR process_name LIKE '%.Protection%' OR process_name LIKE '%.SECURITY.%' OR process_name LIKE '%Certifications%')
""").fetchone()[0]
bf_cnt = conn.execute("""
    WITH bf AS (
        SELECT count(1) as cnt FROM events 
        WHERE event_type = 'login' AND status = 'FAILURE' 
        GROUP BY usr, src_ip 
        HAVING count(1) >= 20
    ) SELECT coalesce(sum(cnt), 0) FROM bf
""").fetchone()[0]

true_threats = v_cnt + w_cnt + ips_cnt + bf_cnt

# Breakdown of Numerator (captured_threats)
rules = conn.execute("""
    SELECT rule_id, sum(event_count) as ec, count(1) as alert_count
    FROM alerts 
    WHERE rule_id IN ('EXP-001', 'BF-001', 'BF-002', 'C2-001', 'CRED-001', 'DISC-001', 'PRV-001', 'MAL-001', 'PHISH-001')
    GROUP BY rule_id ORDER BY ec DESC
""").fetchall()

captured_threats = sum(r[1] for r in rules)

print("=" * 60)
print(f"DENOMINATOR (true_threats): {true_threats}")
print(f"  - Confirmed Virus events: {v_cnt}")
print(f"  - Blocked Web Phishing events: {w_cnt}")
print(f"  - Genuine IPS Exploits (excluding vendor noise): {ips_cnt}")
print(f"  - Automated Password Spraying / Brute-force (>=20 failed): {bf_cnt}")
print("=" * 60)
print(f"NUMERATOR (captured_threats): {captured_threats}")
for r in rules:
    print(f"  - Rule {r[0]}: {r[1]} raw events captured (grouped into {r[2]} alerts)")
print("=" * 60)
pct = (captured_threats / true_threats) * 100
print(f"SENSITIVITY / DETECTION RATE = {captured_threats} / {true_threats} * 100 = {pct:.2f}%")
