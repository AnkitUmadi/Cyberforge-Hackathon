import re
from collections import Counter

KV_REGEX = re.compile(r'([a-zA-Z0-9_]+)=(?:"([^"]*)"|(\S+))')
attacks = Counter()
viruses = Counter()
event_types = Counter()

src = r"C:\Users\Ankit Umadi\Downloads\firex-10G.log"
count = 0

print("Scanning 2,000,000 lines across 6.5 GB file to uncover all attack vectors...")
with open(src, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        count += 1
        if "attack=" in line:
            for k, v1, v2 in KV_REGEX.findall(line):
                if k == "attack":
                    attacks[v1 or v2] += 1
        if "virus=" in line:
            for k, v1, v2 in KV_REGEX.findall(line):
                if k == "virus":
                    viruses[v1 or v2] += 1
        if count >= 2000000:
            break

print(f"Scanned {count:,} lines:")
print(f"Total Unique Attack Signatures found: {len(attacks)}")
print(f"Total Unique Virus Signatures found: {len(viruses)}")

print("\n--- ALL UNIQUE ATTACK CATEGORIES IN THE DATASET ---")
for a, c in attacks.most_common(25):
    print(f"  [{c:,}] {a}")

print("\n--- ALL UNIQUE VIRUS FAMILIES IN THE DATASET ---")
for v, c in viruses.most_common(15):
    print(f"  [{c:,}] {v}")
