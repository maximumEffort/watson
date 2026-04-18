#!/bin/bash
ISSUES=()
REPORT=()

GW_PID=$(pgrep -u kraetes -f "openclaw-gateway" 2>/dev/null)
if [ -z "$GW_PID" ]; then
    ISSUES+=("CRITICAL: Eve gateway not running")
    REPORT+=("Gateway: DOWN")
else
    GW_UPTHMe=$(ps -o etime= -p "$GW_PID" 2>/dev/null | tr -d ' ')
    REPORT+=("Gateway: UP (PID $GW_PID, uptime $GW_UPTIME)")
fi

STUCK=()
while IFS= read -r line; do
    PID=$(echo "$line" | awk '{print $1}')
    ETIME=$(echo "$line" | awk '{print $2}')
    COLONS=$(echo "$ETIME" | tr -cd ':' | wc -c)
    if [ "$COLONS" -ge 2 ] || echo "$ETIME" | grep -q '-'; then
        STUCK+=("PID $PID ($ETIME)")
    fi
done < <(pgrep -u kraetes -f "^claude" 2>/dev/null | xargs -I{} ps -o pid=,etime= -p {} 2>/dev/null)

if [ ${#STUCK[@]} -gt 0 ]; then
    ISSUES+=("WARNING: Stuck Claude process(es): ${STUCK[*]}")
    REPORT+=("Stuck processes: ${STUCK[*]}")
else
    RUNNING=$(pgrep -u kraetes -f "^claude" 2>/dev/null | wc -l)
    REPORT+=("Claude processes: $RUNNING active, none stuck")
fi

STOP_LOG="/home/kraetes/eve/memory/.session/stop-hook.log"
if [ -f "$STOP_LOG" ]; then
    RECENT_FAILS=$(tail -20 "$STOP_LOG" | grep -c "FAIL\|TIMEOUT\|ERROR" 2>/dev/null || echo 0)
    if [ "$RECENT_FAILS" -gt 0 ]; then
        ISSUES+=("WARNING: $RECENT_FAILS stop-hook failure(s) in last 20 entries")
    fi
    LAST_RUN=$(tail -1 "$STOP_LOG" | grep -o '\[.*\]' | tr -d '[]' || echo "unknown")
    REPORT+=("Stop-hook last run: $LAST_RUN (failures: $RECENT_FAILS)")
else
    REPORT+=("Stop-hook log: not found")
fi

echo "=== Eve Health Check ==="
for line in "${REPORT[@]}"; do echo "  $line"; done

if [ ${#ISSUES[@]} -gt 0 ]; then
    echo "Issues:"
    for issue in "${ISSUES[@]}"; do echo "  ! $issue"; done
    exit 1
else
    echo "All clear"
    exit 0
fi
