import re
from collections import Counter

KV_REGEX = re.compile(r'([a-zA-Z0-9_]+)=(?:"([^"]*)"|(\S+))')
attacks = Counter()
viruses = Counter()
phishing = Counter()
login_failed_users = Counter()
login_failed_srcips = Counter()

from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PATH = str(ROOT / "data" / "sample_100MB.log")

with open(SAMPLE_PATH, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        matches = dict([(k, v1 if v1 else v2) for k, v1, v2 in KV_REGEX.findall(line)])
        if 'attack' in matches:
            attacks[matches['attack']] += 1
        if 'virus' in matches:
            viruses[matches['virus']] += 1
        if 'catdesc' in matches and 'Phishing' in matches['catdesc']:
            phishing[matches.get('hostname', '')] += 1
        if matches.get('logdesc') == 'Admin login failed':
            login_failed_users[matches.get('user', 'unknown')] += 1
            login_failed_srcips[matches.get('srcip', 'unknown')] += 1

print("Top 10 Attacks (UTM IPS):")
for a, c in attacks.most_common(10):
    print(f"  {a}: {c}")

print("\nTop Viruses (UTM AV):")
for v, c in viruses.most_common(10):
    print(f"  {v}: {c}")

print("\nTop Phishing Domains:")
for p, c in phishing.most_common(10):
    print(f"  {p}: {c}")

print("\nTop Target Users in Failed Logins:")
for u, c in login_failed_users.most_common(10):
    print(f"  {u}: {c}")

print("\nTop Attacker Source IPs in Failed Logins:")
for ip, c in login_failed_srcips.most_common(10):
    print(f"  {ip}: {c}")
