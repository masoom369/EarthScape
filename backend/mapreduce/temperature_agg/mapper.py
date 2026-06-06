#!/usr/bin/env python3
import sys

for line in sys.stdin:
    line = line.strip()
    if not line or line.startswith("region"):
        continue
    parts = line.split(",")
    if len(parts) < 3:
        continue
    region, temp = parts[0], parts[2]
    if not temp or temp == "null":
        continue
    try:
        print(f"{region}\t{float(temp)}")
    except ValueError:
        continue