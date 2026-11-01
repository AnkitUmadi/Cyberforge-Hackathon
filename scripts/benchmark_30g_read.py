import time
import re

KV_REGEX = re.compile(r'([a-zA-Z0-9_]+)=(?:"([^"]*)"|(\S+))')
path = r'C:\Users\Ankit Umadi\Downloads\firex-30G\firex-30G.log'

t0 = time.time()
count = 0
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        matches = KV_REGEX.findall(line)
        count += 1
        if count >= 100000:
            break

dt = time.time() - t0
print(f"Read & regex-parsed {count:,} lines in {dt:.2f}s ({count/dt:,.0f} lines/sec)")
