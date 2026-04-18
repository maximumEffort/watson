# TOOLS.md — Watson's Environment

## Host Access

Watson runs as user `watson` on the same machine as Eve.
The `agents` group gives read access to Eve's workspace and home directory.

### Eve's key paths (readable)
- Eve workspace: /home/kraetes/eve/
- Eve config: /home/kraetes/.openclaw/openclaw.json
- Eve stop-hook log: /home/kraetes/eve/memory/.session/stop-hook.log
- Eve session files: /home/kraetes/.claude/

### Useful diagnostic commands

Check if Eve is stuck:
  ps -eo pid,etime,cmd | grep claude | grep -v grep

Eve gateway status:
  journalctl -u openclaw-gateway --since "30 min ago" --no-pager | tail -20

Eve recent stop-hook runs:
  tail -20 /home/kraetes/eve/memory/.session/stop-hook.log

## Watson's Gateway

- Port: 18790
- Service: watson-gateway (system service — sudo systemctl restart watson-gateway)
- Web UI: http://127.0.0.1:18790

## Channels

- Telegram: @KraetesWatsonBot (primary)
