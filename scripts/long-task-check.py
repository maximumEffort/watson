#!/usr/bin/env python3
"""
long-task-check.py — Read Eve's long-task flag.
Eve writes /home/kraetes/eve/state/long-task.json when starting a long job.
Watson reads it to suppress false stuck-process alerts.

Flag format:
  {"task": "description", "started": unix_timestamp, "expected_mins": N}

Exit 0: no active long task (or flag cleared).
Exit 2: long task in progress (Watson should not alert about stuck processes).
"""
import json, sys, os
from datetime import datetime, timezone

FLAG = "/home/kraetes/eve/state/long-task.json"

if not os.path.exists(FLAG):
    print("No long task flag set")
    sys.exit(0)

try:
    data = json.load(open(FLAG))
    started = data.get("started", 0)
    expected = data.get("expected_mins", 60)
    task = data.get("task", "unknown task")
    elapsed_m = (datetime.now(timezone.utc).timestamp() - started) / 60
    deadline_m = expected - elapsed_m
    started_str = datetime.fromtimestamp(started).strftime("%H:%M")

    if deadline_m > 0:
        print(f"LONG TASK IN PROGRESS: {task}")
        print(f"  Started: {started_str} | Elapsed: {elapsed_m:.0f}m | Expected: {expected}m | Remaining: {deadline_m:.0f}m")
        sys.exit(2)
    else:
        overtime = -deadline_m
        print(f"WARNING: Long task overdue by {overtime:.0f}m: {task}")
        print(f"  Started: {started_str} | Expected to finish after {expected}m")
        sys.exit(1)
except Exception as e:
    print(f"ERROR reading long-task flag: {e}")
    sys.exit(1)
