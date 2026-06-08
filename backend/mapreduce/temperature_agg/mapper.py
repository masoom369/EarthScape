#!/usr/bin/env python3
"""
Temperature aggregation mapper.
CRITICAL #3: header detection checks if the temperature field parses as float.
Handles Region, REGION, region, absent headers — no fragile string match.
"""
import sys

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    parts = line.split(",")
    if len(parts) < 3:
        continue
    region, temp_raw = parts[0], parts[2]
    if not temp_raw or temp_raw == "null":
        continue
    # CRITICAL #3: skip header row by testing numeric parseability
    try:
        temp = float(temp_raw)
    except ValueError:
        continue
    print(f"{region}\t{temp}")