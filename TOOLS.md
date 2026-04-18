# TOOLS.md -- Watson's Environment

## Host Access

Watson runs as user `watson` on the same machine as Eve.
The `agents` group gives read access to Eve's workspace and home directory.

### Eve's key paths (readable)
- Eve workspace: /home/kraetes/eve/
- Eve config: /home/kraetes/.openclaw/openclaw.json
- Eve stop-hook log: /home/kraetes/eve/memory/.session/stop-hook.log
- Eve session files: /home/kraetes/.claude/projects/-home-kraetes-eve/
- Eve long-task flag: /home/kraetes/eve/state/long-task.json

## Controlling Eve

Watson can restart Eve's gateway when it gets stuck or unresponsive.
systemd will auto-restart the killed gateway process.

  sudo /usr/local/bin/restart-eve-gateway

Use this ONLY when:
- A Claude process has been running >90 min with no active long-task flag
- Eve is unresponsive on Telegram AND gateway is unhealthy
- Amr explicitly asks Watson to restart Eve

Always check `long-task-check.py` first -- if Eve is mid-task by design,
do NOT kill her.

## Diagnostic Scripts (in /home/watson/watson/scripts/)

### Health checks
- eve-health.sh        -- gateway PID, uptime, stuck processes, stop-hook fails
- tunnel-check.sh      -- Cloudflare tunnel eve.kraetes.com reachability
- temp-monitor.py      -- CPU thermal zones (warn 70C, crit 85C)
- backup-verifier.py   -- git last commit, Obsidian freshness, disk %
- settings-guardian.py -- Eve's ~/.claude/settings.json drift detection
                          (--bless to accept new baseline, --show to view)
- stuck-detector.py    -- long-running Claude processes (respects long-task flag)

### Activity inspection
- session-inspector.py  -- last N turns of Eve's most recent session
- cron-monitor.py       -- all 23 of Eve's crons, next/last run, overdue flags
- cost-tracker.py       -- token usage + cost estimate from session JSONL files
- wake-eve.sh           -- probe Eve via HTTP + Telegram + active sessions

### Coordination
- long-task-check.py    -- read Eve's long-task flag (exit 2 = task in progress)
- weekly-digest.py      -- aggregate all diagnostics into a status report
- send-weekly-digest.sh -- send digest via KraetesWatsonBot (auto-runs Sun 21:00 UTC)

## Watson's Gateway

- Port: 18790
- Service: watson-gateway (system service -- sudo systemctl restart watson-gateway)
- Web UI: http://127.0.0.1:18790

## Channels

- Telegram: @KraetesWatsonBot (primary)
