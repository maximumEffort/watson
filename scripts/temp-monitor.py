#!/usr/bin/env python3
"""
temp-monitor.py — Check CPU temperature. Warn >70C, critical >85C.
Exit 0: OK. Exit 1: warning or critical.
"""
import os, sys, glob

WARN_C = 70
CRIT_C = 85

def read_thermal_zones():
    temps = []
    for path in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
        try:
            val = int(open(path).read().strip()) / 1000.0
            zone = path.split("/")[-2]
            temps.append((zone, val))
        except Exception:
            pass
    return temps

temps = read_thermal_zones()

if not temps:
    print("UNKNOWN: No thermal zones found (sensors not available)")
    sys.exit(0)

max_zone, max_temp = max(temps, key=lambda x: x[1])
all_info = ", ".join(f"{z}={t:.1f}C" for z, t in sorted(temps))

if max_temp >= CRIT_C:
    print(f"CRITICAL: {max_zone} at {max_temp:.1f}C -- {all_info}")
    sys.exit(1)
elif max_temp >= WARN_C:
    print(f"WARNING: {max_zone} at {max_temp:.1f}C -- {all_info}")
    sys.exit(1)
else:
    print(f"OK: Max temp {max_temp:.1f}C ({max_zone}) -- {all_info}")
    sys.exit(0)
