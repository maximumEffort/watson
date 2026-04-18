#!/usr/bin/env python3
"""
backup-verifier.py — Verify Eve's backups are fresh.
Checks: git repo last push, obsidian vault recent activity, disk space.
Exit 0: OK. Exit 1: stale or critical.
"""
import subprocess, sys, os
from datetime import datetime, timezone

WARN_HOURS = 48
CRIT_HOURS = 168  # 7 days
EVE_REPO = "/home/kraetes/eve"
OBSIDIAN_VAULT = "/home/kraetes/eve/obsidian-vault"
DISK_WARN_PCT = 80
DISK_CRIT_PCT = 90

issues = []
warnings = []
ok = []

# 1. Check git repo last push (via FETCH_HEAD or remote tracking)
try:
    r = subprocess.run(
        ["git", "-C", EVE_REPO, "log", "-1", "--format=%ct", "origin/main"],
        capture_output=True, text=True, timeout=10
    )
    if r.returncode == 0 and r.stdout.strip():
        ts = int(r.stdout.strip())
        age_h = (datetime.now(timezone.utc).timestamp() - ts) / 3600
        last = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        if age_h >= CRIT_HOURS:
            issues.append(f"CRITICAL: Eve git last pushed {age_h:.0f}h ago ({last})")
        elif age_h >= WARN_HOURS:
            warnings.append(f"WARNING: Eve git last pushed {age_h:.0f}h ago ({last})")
        else:
            ok.append(f"Git: last push {age_h:.0f}h ago ({last})")
    else:
        warnings.append("WARNING: Could not determine last git push time")
except Exception as e:
    warnings.append(f"WARNING: Git check failed -- {e}")

# 2. Check Obsidian vault recent activity
try:
    r = subprocess.run(
        ["find", OBSIDIAN_VAULT, "-name", "*.md", "-newer",
         f"{OBSIDIAN_VAULT}/../.git/FETCH_HEAD", "-type", "f"],
        capture_output=True, text=True, timeout=10
    )
    # Fall back to checking newest file mtime
    r2 = subprocess.run(
        ["find", OBSIDIAN_VAULT, "-name", "*.md", "-type", "f",
         "-printf", "%T@\n"],
        capture_output=True, text=True, timeout=10
    )
    if r2.stdout.strip():
        newest_ts = max(float(x) for x in r2.stdout.strip().split("\n") if x)
        age_h = (datetime.now(timezone.utc).timestamp() - newest_ts) / 3600
        last = datetime.fromtimestamp(newest_ts).strftime("%Y-%m-%d %H:%M")
        if age_h >= CRIT_HOURS:
            issues.append(f"CRITICAL: Obsidian vault stale -- newest note {age_h:.0f}h ago ({last})")
        elif age_h >= WARN_HOURS:
            warnings.append(f"WARNING: Obsidian vault quiet -- newest note {age_h:.0f}h ago ({last})")
        else:
            ok.append(f"Obsidian: newest note {age_h:.0f}h ago ({last})")
    else:
        warnings.append(f"WARNING: No .md files found in {OBSIDIAN_VAULT}")
except Exception as e:
    warnings.append(f"WARNING: Obsidian check failed -- {e}")

# 3. Disk space
try:
    r = subprocess.run(["df", "-h", "/home/kraetes"], capture_output=True, text=True)
    lines = r.stdout.strip().split("\n")
    if len(lines) >= 2:
        parts = lines[1].split()
        pct = int(parts[4].rstrip("%"))
        used, total = parts[2], parts[1]
        if pct >= DISK_CRIT_PCT:
            issues.append(f"CRITICAL: Disk {pct}% full ({used}/{total})")
        elif pct >= DISK_WARN_PCT:
            warnings.append(f"WARNING: Disk {pct}% full ({used}/{total})")
        else:
            ok.append(f"Disk: {pct}% used ({used}/{total})")
except Exception as e:
    warnings.append(f"WARNING: Disk check failed -- {e}")

for msg in warnings + issues:
    print(msg)
for msg in ok:
    print(msg)

sys.exit(1 if (issues or warnings) else 0)
