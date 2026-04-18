#!/bin/bash
# send-weekly-digest.sh -- run digest, send via Watson's Telegram bot.
set -u
SCRIPTS_DIR="/home/watson/watson/scripts"
CONF="/home/watson/.openclaw/openclaw.json"
ALLOW="/home/watson/.openclaw/credentials/telegram-default-allowFrom.json"

BOT_TOKEN=$(python3 -c "import json; print(json.load(open('$CONF'))['channels']['telegram']['botToken'])")
CHAT_ID=$(python3 -c "import json; print(json.load(open('$ALLOW'))['allowFrom'][0])")

DIGEST=$(python3 "$SCRIPTS_DIR/weekly-digest.py" 2>&1)

curl -s --max-time 30 \
    -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d "chat_id=${CHAT_ID}" \
    --data-urlencode "text=${DIGEST}" \
    > /dev/null
