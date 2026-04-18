#!/usr/bin/env python3
"""
cron-monitor.py — Check Eve's cron jobs for missed/overdue runs.
Flags crons that should have run but haven't.
"""
import json, sys
from datetime import datetime, timezone

JOBS_FILE = "/home/kraetes/.openclaw/cron/jobs.json"
NOW_MS = datetime.now(tz=timezone.utc).timestamp() * 1000

def parse_cron_interval_ms(expr):
    """Very rough: return expected interval in ms from common patterns."""
    parts = expr.strip().split()
    if len(parts) != 5:
        return None
    minute, hour, dom, month, dow = parts
    if minute.startswith("*/"):
        return int(minute[2:]) * 60 * 1000
    if hour == "*" and minute != "*":
        return 60 * 60 * 1000  # hourly
    if dow != "*":
        return 7 * 24 * 60 * 60 * 1000  # weekly
    return 24 * 60 * 60 * 1000  # daily

d = json.load(open(JOBS_FILE))
jobs = d.get("jobs", [])

print(f"=== Eve Cron Monitor — {len(jobs)} jobs ===\n")

issues = []
for job in jobs:
    name = job.get("name", "?")
    enabled = job.get("enabled", True)
    schedule = job.get("schedule", {})
    state = job.get("state", {})
    expr = schedule.get("expr", "")
    next_run = state.get("nextRunAtMs")
    last_run = state.get("lastRunAtMs") or state.get("lastSuccessAtMs")

    if not enabled:
        print(f"  [DISABLED] {name}")
        continue

    interval_ms = parse_cron_interval_ms(expr)
    overdue_ms = NOW_MS - next_run if next_run else None
    overdue_min = overdue_ms / 60000 if overdue_ms else 0

    if overdue_min > 60:
        status = f"OVERDUE {overdue_min:.0f}min"
        issues.append(f"{name} overdue by {overdue_min:.0f} min")
    elif overdue_min > 0:
        status = f"due {overdue_min:.0f}min ago"
    else:
        mins_until = abs(overdue_ms or 0) / 60000
        status = f"next in {mins_until:.0f}min"

    last_str = ""
    if last_run:
        last_ago = (NOW_MS - last_run) / 60000
        last_str = f" | last ran {last_ago:.0f}min ago"

    print(f"  {'⚠ ' if 'OVERDUE' in status else '  '}{name}: {status}{last_str}")

print()
if issues:
    print(f"Issues: {len(issues)}")
    for i in issues:
        print(f"  ! {i}")
    sys.exit(1)
else:
    print("All crons on schedule")
