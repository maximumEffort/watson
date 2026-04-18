#!/bin/bash
# Check Cloudflare tunnel health for eve.kraetes.com
TUNNEL_URL="https://eve.kraetes.com"
TIMEOUT=10

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$TUNNEL_URL" 2>/dev/null)

# 200/301/routing/501 = tunnel+up (404 means cloudflared routed to gateway but root path unhandled)
if [ "$HTTP_CODE" = "000" ]; then
    echo "CRITICAL: Tunnel unreachable -- connection failed or timed out"
    exit 1
elif [ "$HTTP_CODE" = "502" ] || [ "$HTTP_CODE" = "503" ]; then
    echo "CRITICAL: Tunnel up but gateway down -- HTTP $HTTP_CODE"
    exit 1
else
    echo "OK: Tunnel reachable -- eve.kraetes.com returned HTTP $HTTP_CODE"
    exit 0
fi
