#!/usr/bin/env python3
"""
Precipitation totals mapper.
CRITICAL #3: header detection checks numeric parseability of precipitation field.
Handles case-variants (Region, REGION, region) and absent headers.
"""
import sys

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    parts = line.split(",")
    if len(parts) < 4:
        continue
    region, ts, precip_raw = parts[0], parts[1], parts[3]
    if not precip_raw or precip_raw == "null":
        continue
    # CRITICAL #3: skip header row by testing numeric parseability
    try:
        precip = float(precip_raw)
    except ValueError:
        continue
    try:
        month = ts[:7]
        print(f"{region}_{month}\t{precip}")
    except IndexError:
        continue