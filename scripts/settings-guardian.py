#!/usr/bin/env python3
"""
settings-guardian.py — Detect changes to Eve's Claude settings.json.
Stores a baseline hash + snapshot. On drift, shows a diff.

Usage:
  settings-guardian.py              # check (exit 1 if changed)
  settings-guardian.py --bless      # accept current state as new baseline
  settings-guardian.py --show       # show current baseline
"""
import hashlib, json, os, sys, argparse, difflib
from datetime import datetime

SETTINGS = "/home/kraetes/.claude/settings.json"
BASELINE_DIR = "/home/watson/watson/state"
BASELINE = f"{BASELINE_DIR}/settings-baseline.json"

parser = argparse.ArgumentParser()
parser.add_argument("--bless", action="store_true", help="Accept current state as new baseline")
parser.add_argument("--show", action="store_true", help="Show current baseline")
args = parser.parse_args()

os.makedirs(BASELINE_DIR, exist_ok=True)

def read_current():
    if not os.path.exists(SETTINGS):
        return None, None
    content = open(SETTINGS).read()
    h = hashlib.sha256(content.encode()).hexdigest()
    return content, h

def read_baseline():
    if not os.path.exists(BASELINE):
        return None
    return json.load(open(BASELINE))

def write_baseline(content, h):
    data = {
        "hash": h,
        "content": content,
        "blessed_at": datetime.now().isoformat(timespec="seconds"),
    }
    json.dump(data, open(BASELINE, "w"), indent=2)

current, current_hash = read_current()
if current is None:
    print(f"ERROR: {SETTINGS} not found")
    sys.exit(1)

if args.show:
    baseline = read_baseline()
    if baseline:
        print(f"Baseline blessed at: {baseline['blessed_at']}")
        print(f"Baseline hash: {baseline['hash'][:12]}...")
        print("---")
        print(baseline["content"])
    else:
        print("No baseline set yet")
    sys.exit(0)

if args.bless:
    write_baseline(current, current_hash)
    print(f"Baseline updated: {current_hash[:12]}... ({len(current)} bytes)")
    sys.exit(0)

baseline = read_baseline()
if baseline is None:
    print("ALERT: No baseline exists. Run with --bless to accept current settings.")
    print(f"Current hash: {current_hash[:12]}...")
    sys.exit(1)

if baseline["hash"] == current_hash:
    print(f"OK: settings.json unchanged since {baseline['blessed_at']}")
    sys.exit(0)

print(f"DRIFT DETECTED: settings.json changed since {baseline['blessed_at']}")
print(f"  Baseline hash: {baseline['hash'][:12]}...")
print(f"  Current hash:  {current_hash[:12]}...")
print("---DIFF---")
diff = difflib.unified_diff(
    baseline["content"].splitlines(keepends=True),
    current.splitlines(keepends=True),
    fromfile="baseline", tofile="current"
)
sys.stdout.writelines(diff)
print("---")
print("Review the diff. If the change is legitimate, run: --bless")
sys.exit(1)
