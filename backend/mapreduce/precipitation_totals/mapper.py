#!/usr/bin/env python3
import sys

for line in sys.stdin:
    line = line.strip()
    if not line or line.startswith("region"):
        continue
    parts = line.split(",")
    if len(parts) < 4:
        continue
    region, ts, precip = parts[0], parts[1], parts[3]
    if not precip or precip == "null":
        continue
    try:
        month = ts[:7]
        print(f"{region}_{month}\t{float(precip)}")
    except (ValueError, IndexError):
        continue