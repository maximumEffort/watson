#!/usr/bin/env python3
"""
session-inspector.py — Shows what Eve was doing in her most recent session.
Usage: python3 session-inspector.py [--all] [--n N]
"""
import json, os, glob, sys, argparse
from datetime import datetime, timezone

PROJECT_DIR = "/home/kraetes/.claude/projects/-home-kraetes-eve"
DEFAULT_TURNS = 10

parser = argparse.ArgumentParser()
parser.add_argument("--n", type=int, default=DEFAULT_TURNS)
parser.add_argument("--all", action="store_true", help="Show all sessions, not just latest")
args = parser.parse_args()

jsonls = glob.glob(os.path.join(PROJECT_DIR, "*.jsonl"))
jsonls.sort(key=os.path.getmtime, reverse=True)

def format_time(ts):
    try:
        return datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%H:%M:%S UTC")
    except:
        return "?"

def read_session(path):
    turns = []
    with open(path, errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except:
                continue
            t = e.get("type", "")
            if t == "user":
                msg = e.get("message", {})
                content = msg.get("content", "")
                if isinstance(content, list):
                    content = " ".join(p.get("text","") for p in content if isinstance(p,dict) and p.get("type")=="text")
                if isinstance(content, str) and content.strip():
                    text = content.strip()
                    if text.startswith("[cron:"):
                        return None, True  # cron session
                    turns.append(("USER", text[:300]))
            elif t == "assistant":
                msg = e.get("message", {})
                content = msg.get("content", "")
                if isinstance(content, list):
                    # Extract text + tool calls
                    parts = []
                    for p in content:
                        if isinstance(p, dict):
                            if p.get("type") == "text" and p.get("text","").strip():
                                parts.append(p["text"][:200])
                            elif p.get("type") == "tool_use":
                                parts.append(f"[TOOL: {p.get('name','?')}]")
                    content = " | ".join(parts)
                if isinstance(content, str) and content.strip():
                    turns.append(("EVE", content.strip()[:300]))
    return turns, False

shown = 0
for path in jsonls:
    if shown >= (100 if args.all else 1):
        break
    mtime = os.path.getmtime(path)
    age_min = (datetime.now().timestamp() - mtime) / 60
    turns, is_cron = read_session(path)
    if is_cron or not turns:
        continue

    print(f"\n{'='*60}")
    print(f"Session: {os.path.basename(path)}")
    print(f"Last modified: {datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')} ({age_min:.0f} min ago)")
    print(f"Turns: {len(turns)}")
    print(f"{'='*60}")
    for role, text in turns[-args.n:]:
        prefix = "Amr: " if role == "USER" else "Eve:  "
        print(f"\n{prefix}{text}")
    shown += 1
    if not args.all:
        break

if shown == 0:
    print("No non-cron sessions found.")
