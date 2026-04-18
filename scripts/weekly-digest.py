#!/usr/bin/env python3
"""
weekly-digest.py -- Generate a weekly Watson report.
"""
import subprocess, json, os, glob, sys
from datetime import datetime, timedelta, timezone

SCRIPTS_DIR = "/home/watson/watson/scripts"
CLAUDE_PROJECTS = "/home/kraetes/.claude/projects/-home-kraetes-eve"

def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return f"[error: {e}]"

def first_status(out):
    for line in out.split("\n"):
        s = line.strip()
        if s and not s.startswith("==="):
            return s
    return "(no output)"

now = datetime.now(timezone.utc)
week_ago = now - timedelta(days=7)

lines = []
lines.append("*Watson Weekly Digest*")
lines.append(f"_{week_ago.strftime('%Y-%m-%d')} -> {now.strftime('%Y-%m-%d')}_")
lines.append("")

lines.append("*System Health*")
for label, cmd in [
    ("Gateway", ["bash", f"{SCRIPTS_DIR}/eve-health.sh"]),
    ("Tunnel",  ["bash", f"{SCRIPTS_DIR}/tunnel-check.sh"]),
    ("Temp",    ["python3", f"{SCRIPTS_DIR}/temp-monitor.py"]),
    ("Backup",  ["python3", f"{SCRIPTS_DIR}/backup-verifier.py"]),
    ("Settings",["python3", f"{SCRIPTS_DIR}/settings-guardian.py"]),
    ("Stuck",   ["python3", f"{SCRIPTS_DIR}/stuck-detector.py"]),
]:
    lines.append(f"- *{label}*: {first_status(run(cmd))}")
lines.append("")

lines.append("*Session Activity (7d)*")
try:
    sessions = glob.glob(f"{CLAUDE_PROJECTS}/*.jsonl")
    recent = [s for s in sessions if os.path.getmtime(s) >= week_ago.timestamp()]
    lines.append(f"- Sessions touched: {len(recent)}")
    total_user = total_assistant = 0
    for s in recent:
        try:
            with open(s) as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        if obj.get("type") == "user": total_user += 1
                        elif obj.get("type") == "assistant": total_assistant += 1
                    except Exception: pass
        except Exception: pass
    lines.append(f"- User msgs: {total_user} | Assistant msgs: {total_assistant}")
except Exception as e:
    lines.append(f"- Error: {e}")
lines.append("")

lines.append("*Cost Estimate*")
cost_out = run(["python3", f"{SCRIPTS_DIR}/cost-tracker.py"])
for line in cost_out.split("\n")[:6]:
    lines.append(f"  {line}")
lines.append("")

lines.append("*Cron Health*")
cron_out = run(["python3", f"{SCRIPTS_DIR}/cron-monitor.py"])
cron_lines = [l for l in cron_out.split("\n") if l.strip()]
overdue = [l for l in cron_lines if "overdue" in l.lower()]
if overdue:
    lines.append(f"- {len(overdue)} overdue:")
    for o in overdue[:5]:
        lines.append(f"  {o.strip()}")
else:
    lines.append(f"- All on schedule ({len(cron_lines)} lines tracked)")
lines.append("")

lines.append("_Watson out._")
print("\n".join(lines))
