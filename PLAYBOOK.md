# PLAYBOOK.md -- Watson's Operational Decisions

This is the decision flow for each type of incident Watson handles.
Default posture: observe and report. Intervene only when the criteria below
are fully met. When unsure, ask Amr before acting.

## 1. "Eve is stuck" alert

Run this sequence. Do NOT restart until all three conditions are met.

1. `bash ~/watson/scripts/eve-health.sh`
   - If gateway DOWN and not auto-restarting -> systemd is broken, tell Amr
   - If gateway UP and reachable -> Eve is alive, check activity
2. `python3 ~/watson/scripts/stuck-detector.py`
   - Exit 0 with "No active Claude processes" -> Eve is idle, not stuck
   - WARNING lines -> process is long but under critical threshold, wait
   - CRITICAL line -> proceed to step 3
3. `python3 ~/watson/scripts/long-task-check.py`
   - Exit 2 (flag active, within window) -> do NOT restart. Report and wait.
   - Exit 0 (no flag) or exit 1 (flag overdue) -> intervene

Intervention:
  sudo /usr/local/bin/restart-eve-gateway

After restart, wait 30 sec, then run eve-health.sh again to confirm recovery.
Report both the kill and the recovery to Amr.

## 2. Settings drift

If `settings-guardian.py` reports DRIFT:
- Show Amr the diff (the tool already formats it)
- Do NOT --bless automatically
- Ask Amr: "Is this change intentional? Should I bless it as the new baseline?"
- Only run --bless after explicit confirmation

## 3. Temperature alerts

- WARNING (>70C) -> report to Amr, suggest checking fans/load
- CRITICAL (>85C) -> report urgently, suggest killing non-essential load
- Never auto-kill processes for temperature reasons

## 4. Tunnel / gateway unreachable

- `tunnel-check.sh` returns CRITICAL (HTTP 502/503 or connection failed)
  -> gateway might be down behind a working tunnel
  -> run eve-health.sh to confirm gateway state
  -> if gateway is unresponsive AND no long-task active, restart is allowed

- `tunnel-check.sh` returns "Tunnel unreachable"
  -> Cloudflare tunnel itself is broken, NOT Eve's fault
  -> check cloudflared service: `systemctl status cloudflared`
  -> tell Amr; do not touch Eve

## 5. Backup verifier alerts

- Git last commit >48h ago -> mention to Amr, don't act (might be quiet week)
- Obsidian newest note >48h ago -> same, just flag it
- Disk >80% -> warn; >90% -> urgent

Never auto-delete anything for disk cleanup.

## 6. Weekly digest

The systemd timer `watson-weekly-digest.timer` auto-fires every Sunday 21:00 UTC
and sends the digest via `KraetesWatsonBot` to Amr.

Do NOT send it manually unless Amr explicitly asks for an ad-hoc report.

If Amr asks for "status" or "report" mid-week, generate the digest on demand
but mention it is an ad-hoc run, not the scheduled one.

## 7. Long-task flag -- Eve's side

Eve sets the flag at `/home/kraetes/eve/state/long-task.json` when she starts
something lengthy (research, translation, deep dives). The flag contains
task description, start time, and expected minutes.

Watson respects the flag by:
- Not restarting Eve while flag is active and within its time window
- Raising stuck-detector thresholds by (expected + 30 min) when flag is set
- Reporting to Amr if the flag is overdue (elapsed > expected)

If Amr asks "what is Eve doing?" and the flag is set, describe the task,
elapsed time, and remaining estimated time.

## 8. When Amr asks Watson to act

Direct instructions from Amr override these defaults. If Amr says
"restart Eve", do it -- don't block on the checklist. Report what you
did, but trust the user's judgment.

Exception: destructive actions (deleting files, rm -rf, pkill -9 of non-Eve
processes) still require a sanity check even when Amr asks -- confirm once
before executing.
