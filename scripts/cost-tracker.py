#!/usr/bin/env python3
"""
cost-tracker.py — Estimate Eve's Claude API spend from session files.
Usage: python3 cost-tracker.py [--days N] [--today]
"""
import json, glob, os, sys, argparse
from datetime import datetime, timezone, timedelta

PROJECT_DIR = "/home/kraetes/.claude/projects/-home-kraetes-eve"

# Claude Sonnet 4.6 pricing per 1M tokens
PRICE = {
    "input":          3.00,
    "output":        15.00,
    "cache_write":    3.75,
    "cache_read":     0.30,
}

parser = argparse.ArgumentParser()
parser.add_argument("--days", type=int, default=1)
parser.add_argument("--today", action="store_true")
args = parser.parse_args()

now = datetime.now(tz=timezone.utc)
if args.today:
    cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
else:
    cutoff = now - timedelta(days=args.days)
cutoff_ts = cutoff.timestamp()

totals = {"input": 0, "output": 0, "cache_write": 0, "cache_read": 0}
sessions = 0
cron_sessions = 0

files = glob.glob(os.path.join(PROJECT_DIR, "*.jsonl"))
for path in files:
    if os.path.getmtime(path) < cutoff_ts:
        continue
    is_cron = False
    file_totals = {"input": 0, "output": 0, "cache_write": 0, "cache_read": 0}
    try:
        with open(path, errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except:
                    continue
                # Detect cron session
                if e.get("type") == "user":
                    content = e.get("message", {}).get("content", "")
                    if isinstance(content, list):
                        content = " ".join(p.get("text","") for p in content if isinstance(p,dict))
                    if isinstance(content, str) and content.strip().startswith("[cron:"):
                        is_cron = True
                # Collect usage
                # Only count assistant message usage, skip top-level summary entries
                if e.get("type") not in ("assistant", None):
                    continue
                usage = e.get("message", {}).get("usage")
                if usage:
                    file_totals["input"] += usage.get("input_tokens", 0)
                    file_totals["output"] += usage.get("output_tokens", 0)
                    file_totals["cache_write"] += usage.get("cache_creation_input_tokens", 0)
                    file_totals["cache_read"] += usage.get("cache_read_input_tokens", 0)
    except:
        continue

    if is_cron:
        cron_sessions += 1
    else:
        sessions += 1
    for k in totals:
        totals[k] += file_totals[k]

cost = sum(totals[k] * PRICE[k] / 1_000_000 for k in PRICE)

label = "today" if args.today else f"last {args.days}d"
print(f"=== Eve API Cost — {label} ===")
print(f"  Sessions: {sessions} conversation, {cron_sessions} cron")
print(f"  Input tokens:      {totals['input']:>10,}")
print(f"  Output tokens:     {totals['output']:>10,}")
print(f"  Cache write:       {totals['cache_write']:>10,}")
print(f"  Cache read:        {totals['cache_read']:>10,}")
print(f"  Estimated cost:    ${cost:.4f}")

if cost > 5.0:
    print(f"\n  ⚠ High spend: ${cost:.2f}")
    sys.exit(1)
