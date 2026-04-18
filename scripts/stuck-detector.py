#!/usr/bin/env python3
"""
stuck-detector.py — Detect Claude processes that have been running too long.
Respects Eve's long-task flag at /home/kraetes/eve/state/long-task.json.
Exit 0: all clear. Exit 1: stuck process found.
Usage: python3 stuck-detector.py [--warn-mins N] [--critical-mins N]
"""
import subprocess, sys, argparse, json, os
from datetime import datetime, timezone

parser = argparse.ArgumentParser()
parser.add_argument("--warn-mins", type=int, default=45)
parser.add_argument("--critical-mins", type=int, default=90)
args = parser.parse_args()

FLAG = "/home/kraetes/eve/state/long-task.json"

def etime_to_mins(etime):
    etime = etime.strip()
    parts = etime.split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) + int(parts[1]) / 60
        elif len(parts) == 3:
            h, m, s = parts
            if "-" in h:
                d, h = h.split("-")
                return int(d)*1440 + int(h)*60 + int(m) + int(s)/60
            return int(h)*60 + int(m) + int(s)/60
    except:
        return 0
    return 0

# Check long-task flag
long_task = None
if os.path.exists(FLAG):
    try:
        data = json.load(open(FLAG))
        elapsed = (datetime.now(timezone.utc).timestamp() - data.get("started", 0)) / 60
        expected = data.get("expected_mins", 60)
        if elapsed < expected:
            long_task = data.get("task", "long task")
            print(f"INFO: Long task in progress ({long_task}) -- {elapsed:.0f}/{expected}m, thresholds raised")
            args.warn_mins = max(args.warn_mins, int(expected) + 15)
            args.critical_mins = max(args.critical_mins, int(expected) + 30)
    except Exception:
        pass

result = subprocess.run(
    ["pgrep", "-u", "kraetes", "-f", "^claude"],
    capture_output=True, text=True
)
pids = result.stdout.strip().split("\n") if result.stdout.strip() else []

issues = []
warnings = []

for pid in pids:
    if not pid.strip():
        continue
    r = subprocess.run(["ps", "-p", pid, "-o", "etime=,cmd=", "--no-headers"],
                       capture_output=True, text=True)
    if not r.stdout.strip():
        continue
    parts = r.stdout.strip().split(None, 1)
    if len(parts) < 1:
        continue
    etime = parts[0]
    cmd = parts[1][:60] if len(parts) > 1 else ""
    mins = etime_to_mins(etime)

    if mins >= args.critical_mins:
        issues.append(f"CRITICAL: PID {pid} stuck {mins:.0f} min ({etime}) -- {cmd}")
    elif mins >= args.warn_mins:
        warnings.append(f"WARNING: PID {pid} running {mins:.0f} min ({etime}) -- {cmd}")

for w in warnings:
    print(w)
for i in issues:
    print(i)

if not pids or pids == [""]:
    print("No active Claude processes")
elif not issues and not warnings:
    print(f"OK: {len(pids)} Claude process(es), none exceed {args.warn_mins}min threshold")

sys.exit(1 if issues else 0)
