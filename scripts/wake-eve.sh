#!/bin/bash
ISSUES=()

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:18789/ 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo "HTTP: OK"
else
    echo "HTTP: FAIL ($HTTP_CODE)"
    ISSUES+=("Eve HTTP not responding")
fi

BOT_TOKEN=$(python3 -c "import json; d=json.load(open('/home/kraetes/.openclaw/credentials/secrets.json')); print(d.get('telegram_bot_token',''))" 2>/dev/null)
if [ -n "$BOT_TOKEN" ]; then
    TG=$(curl -s --max-time 5 "https://api.telegram.org/bot${BOT_TOKEN}/getMe" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('ok' if d.get('ok') else 'fail')" 2>/dev/null)
    [ "$TG" = "ok" ] && echo "Telegram bot: OK" || { echo "Telegram bot: FAIL"; ISSUES+=("Eve Telegram bot API not responding"); }
else
    echo "Telegram: could not read token"
fi

ACTIVE=$(pgrep -u kraetes -f "^claude" 2>/dev/null | wc -l)
echo "Active Claude sessions: $ACTIVE"

[ ${#ISSUES[@]} -gt 0 ] && { for i in "${ISSUES[@]}"; do echo "! $i"; done; exit 1; }
echo "Eve is responsive"
