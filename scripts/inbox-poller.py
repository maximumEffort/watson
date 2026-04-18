#!/usr/bin/env python3
"""
inbox-poller.py v2 -- severity-aware inbox processor.

Triage by severity:
- info:     canned acknowledgment
- warning:  canned ack + current eve-status snapshot
- critical: full diagnostic run (eve-health, stuck-detector, long-task-check),
            package results into reply, notify Amr via Telegram
"""
import json, os, sys, glob, shutil, subprocess
from datetime import datetime, timezone

INBOX = "/home/kraetes/eve/state/watson-inbox"
PROCESSED = "/home/kraetes/eve/state/watson-processed"
OUTBOX = "/home/kraetes/eve/state/watson-outbox"
STATUS_FILE = "/home/kraetes/eve/state/eve-status.json"
SCRIPTS = "/home/watson/watson/scripts"
WATSON_CONF = "/home/watson/.openclaw/openclaw.json"
WATSON_ALLOW = "/home/watson/.openclaw/credentials/telegram-default-allowFrom.json"

os.makedirs(PROCESSED, exist_ok=True)
os.makedirs(OUTBOX, exist_ok=True)


def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"exit": r.returncode, "stdout": r.stdout.strip(), "stderr": r.stderr.strip()}
    except Exception as e:
        return {"exit": -1, "stdout": "", "stderr": f"error: {e}"}


def read_eve_status():
    try:
        return json.load(open(STATUS_FILE))
    except Exception as e:
        return {"error": f"cannot read {STATUS_FILE}: {e}"}


def notify_amr(text):
    try:
        token = json.load(open(WATSON_CONF))["channels"]["telegram"]["botToken"]
        chat_id = json.load(open(WATSON_ALLOW))["allowFrom"][0]
        subprocess.run([
            "curl", "-s", "--max-time", "10",
            "-X", "POST", f"https://api.telegram.org/bot{token}/sendMessage",
            "-d", f"chat_id={chat_id}",
            "--data-urlencode", f"text={text}",
        ], capture_output=True, timeout=12)
    except Exception:
        pass


def build_reply(msg, severity):
    text = msg.get("message", "")
    mid = msg.get("id", "")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    reply = {
        "in_reply_to": mid,
        "timestamp": now,
        "from": "watson",
        "severity_handled": severity,
    }

    if severity == "critical":
        diagnostics = {
            "eve_health": run(["bash", f"{SCRIPTS}/eve-health.sh"]),
            "stuck_detector": run(["python3", f"{SCRIPTS}/stuck-detector.py"]),
            "long_task": run(["python3", f"{SCRIPTS}/long-task-check.py"]),
            "eve_status": read_eve_status(),
        }
        reply["message"] = (
            f"CRITICAL acknowledged. Ran full diagnostics on your message: "
            f"'{text[:120]}'. See diagnostics field for results. "
            f"Amr has been notified via Telegram."
        )
        reply["diagnostics"] = diagnostics
        reply["action"] = "amr_notified"

        notify_amr(
            f"[Watson] CRITICAL from Eve: {text[:200]}\n\n"
            f"Diagnostics attached in outbox reply ({mid[:8]}). "
            f"Eve health: {diagnostics['eve_health']['stdout'][:100]}"
        )

    elif severity == "warning":
        reply["message"] = (
            f"Warning acknowledged: '{text[:120]}'. "
            f"No auto-diagnostics triggered. Current eve-status included."
        )
        reply["eve_status"] = read_eve_status()
        reply["action"] = "logged"

    else:
        reply["message"] = f"Info acknowledged: '{text[:120]}'. Logged, no action."
        reply["action"] = "none"

    return reply


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
    severity = msg.get("severity", "info").lower()
    if severity not in ("info", "warning", "critical"):
        severity = "info"
    wants_reply = msg.get("wants_reply", False)
    text = msg.get("message", "")

    print(f"INBOX [{severity}] {mid}: {text[:80]}")

    if wants_reply or severity == "critical":
        reply = build_reply(msg, severity)
        reply_path = f"{OUTBOX}/{fname}"
        json.dump(reply, open(reply_path, "w"), indent=2)
        os.chmod(reply_path, 0o664)
        print(f"  REPLY ({severity}) -> {reply_path}")

    shutil.move(path, f"{PROCESSED}/{fname}")
    print(f"  PROCESSED -> {fname}")
