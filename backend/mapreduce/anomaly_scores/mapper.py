#!/usr/bin/env python3
import json
import sys

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        rec = json.loads(line)
        region = rec.get("region", "Unknown")
        print(f"{region}\t{json.dumps(rec)}")
    except json.JSONDecodeError:
        continue