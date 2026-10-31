import re
import json
from collections import Counter
from datetime import datetime

from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PATH = str(ROOT / "data" / "sample_100MB.log")
DOCS_PROFILE_PATH = str(ROOT / "docs" / "PROFILE.md")

# Fast regex for key=value or key="value"
KV_REGEX = re.compile(r'([a-zA-Z0-9_]+)=(?:"([^"]*)"|(\S+))')

def parse_line(line):
    matches = KV_REGEX.findall(line)
    d = {}
    for k, v_quoted, v_unquoted in matches:
        d[k] = v_quoted if v_quoted else v_unquoted
    return d

def profile():
    print(f"Profiling {SAMPLE_PATH}...")
    total_lines = 0
    all_keys = Counter()
    types = Counter()
    subtypes = Counter()
    actions = Counter()
    statuses = Counter()
    services = Counter()
    apps = Counter()
    users = Counter()
    logdescs = Counter()
    levels = Counter()
    min_time = None
    max_time = None

    sample_lines_by_type = {}

    with open(SAMPLE_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f):
            total_lines += 1
            record = parse_line(line)
            for k in record.keys():
                all_keys[k] += 1
            
            t = record.get('type', 'UNKNOWN')
            st = record.get('subtype', 'UNKNOWN')
            types[t] += 1
            subtypes[f"{t}.{st}"] += 1
            levels[record.get('level', 'UNKNOWN')] += 1

            if 'action' in record:
                actions[record['action']] += 1
            if 'status' in record:
                statuses[record['status']] += 1
            if 'service' in record:
                services[record['service']] += 1
            if 'app' in record:
                apps[record['app']] += 1
            if 'user' in record:
                users[record['user']] += 1
            if 'logdesc' in record:
                logdescs[record['logdesc']] += 1

            # Timestamp check
            d_str = record.get('date')
            t_str = record.get('time')
            if d_str and t_str:
                dt_str = f"{d_str} {t_str}"
                if min_time is None or dt_str < min_time:
                    min_time = dt_str
                if max_time is None or dt_str > max_time:
                    max_time = dt_str

            if t not in sample_lines_by_type:
                sample_lines_by_type[t] = line.strip()

    print(f"Completed! Total lines: {total_lines:,}")
    print(f"Time Range: {min_time} to {max_time}")
    print(f"Event Types: {dict(types)}")
    print(f"Top Logdescs: {logdescs.most_common(10)}")

    # Write PROFILE.md
    profile_content = f"""# Dataset Profile: Fortinet FortiGate Log Telemetry

## Overview
- **Source File:** `data/sample_100MB.log` (extracted from `firex-10G.log`)
- **Total Lines Analyzed:** {total_lines:,}
- **Time Range:** `{min_time}` to `{max_time}`
- **Log Format:** Key-Value Pair format (`key=value` or `key="value"`) typical of Fortinet FortiOS / FortiGate UTM appliances.

## Event Hierarchy & Distribution
### High-level Types:
{chr(10).join([f"- **`{k}`**: {v:,} ({v/total_lines*100:.1f}%)" for k, v in types.most_common()])}

### Subtypes Breakdown:
{chr(10).join([f"- **`{k}`**: {v:,}" for k, v in subtypes.most_common()])}

### Severity Levels:
{chr(10).join([f"- **`{k}`**: {v:,}" for k, v in levels.most_common()])}

## Security-Relevant Fields
### Top `logdesc` (Event Descriptions):
{chr(10).join([f"- `{k}`: {v:,}" for k, v in logdescs.most_common(15)])}

### Actions:
{chr(10).join([f"- `{k}`: {v:,}" for k, v in actions.most_common(10)])}

### Statuses:
{chr(10).join([f"- `{k}`: {v:,}" for k, v in statuses.most_common(10)])}

### Top Usernames Observed:
{chr(10).join([f"- `{k}`: {v:,}" for k, v in users.most_common(20)])}

### Top Services / Protocols:
{chr(10).join([f"- `{k}`: {v:,}" for k, v in services.most_common(15)])}

### Top Applications:
{chr(10).join([f"- `{k}`: {v:,}" for k, v in apps.most_common(15)])}

## All Discovered Field Keys ({len(all_keys)} total)
{', '.join([f'`{k}` ({v:,})' for k, v in all_keys.most_common()])}

## Representative Log Lines by Type
"""
    for t, sample in sample_lines_by_type.items():
        profile_content += f"\n### Type: `{t}`\n```log\n{sample}\n```\n"

    with open(DOCS_PROFILE_PATH, 'w', encoding='utf-8') as f:
        f.write(profile_content)
    print(f"Profile saved to {DOCS_PROFILE_PATH}")

if __name__ == "__main__":
    profile()
