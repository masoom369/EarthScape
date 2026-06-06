#!/usr/bin/env python3
import sys

current_region = None
temps = []

for line in sys.stdin:
    region, temp = line.strip().split("\t", 1)
    if current_region and region != current_region:
        if temps:
            print(f"{current_region}\t{min(temps)}\t{max(temps)}\t{sum(temps)/len(temps)}")
        temps = []
    current_region = region
    temps.append(float(temp))

if current_region and temps:
    print(f"{current_region}\t{min(temps)}\t{max(temps)}\t{sum(temps)/len(temps)}")
