#!/usr/bin/env python3
"""
inbox-poller.py — Watson's inbox processor.
Reads messages from Eve's watson-inbox, logs them, moves to processed.
If wants_reply is set, writes a response to watson-outbox.
"""
import json, os, sys, glob, shutil
from datetime import datetime, timezone

INBOX = "/home/kraetes/eve/state/watson-inbox"
PROCESSED = "/home/kraetes/eve/state/watson-processed"
OUTBOX = "/home/kraetes/eve/state/watson-outbox"
STATUS_FILE = "/home/kraetes/eve/state/eve-status.json"

os.makedirs(PROCESSED, exist_ok=True)
os.makedirs(OUTBOX, exist_ok=True)

messages = sorted(glob.glob(f"{INBOX}/*.json"))

if not messages:
    sys.exit(0)

for path in messages:
    fname = os.path.basename(path)
    try:
        msg = json.load(open(path))
    except Exception as e:
        print(f"SKIP {fname}: bad JSON ({e})")
        shutil.move(path, f"{PROCESSED}/{fname}")
        continue

    mid = msg.get("id", "?")[:8]
    text = msg.get("message", "")
    severity = msg.get("severity", "info")
    wants_reply = msg.get("wants_reply", False)
    ts = msg.get("timestamp", "")

    print(f"INBOX [{severity}] {mid}: {text[:80]}")

    if wants_reply:
        reply = {
            "in_reply_to": msg.get("id"),
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "from": "watson",
            "message": f"Acknowledged: {text[:100]}. Watson has logged this. No immediate action needed.",
            "action": "none"
        }
        reply_path = f"{OUTBOX}/{fname}"
        json.dump(reply, open(reply_path, "w"), indent=2)
        os.chmod(reply_path, 0o664)
        print(f"  REPLY -> {reply_path}")

    shutil.move(path, f"{PROCESSED}/{fname}")
    print(f"  PROCESSED -> {fname}")
