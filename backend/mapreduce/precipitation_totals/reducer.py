#!/usr/bin/env python3
import sys

current_key = None
total = 0.0

for line in sys.stdin:
    key, val = line.strip().split("\t", 1)
    if current_key and key != current_key:
        print(f"{current_key}\t{total}")
        total = 0.0
    current_key = key
    total += float(val)

if current_key:
    print(f"{current_key}\t{total}")