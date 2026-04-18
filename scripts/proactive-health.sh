#!/bin/bash

# Proactive Health Check — auto-execute PLAYBOOK Section 1 every 5 min
# Executes decision tree: eve-health → stuck-detector → long-task-check → restart if warranted
# Notifies Amr after taking action

set -e

WATSON_HOME="/home/watson/watson"
SCRIPTS_DIR="${WATSON_HOME}/scripts"
ALERTS_DIR="/home/kraetes/eve/state/watson-inbox"

[ -d "$ALERTS_DIR" ] || mkdir -p "$ALERTS_DIR"

# Step 1: Check gateway health
echo "[$(date)] Running eve-health.sh..."
EVE_HEALTH=$("$SCRIPTS_DIR/eve-health.sh" 2>&1)

if echo "$EVE_HEALTH" | grep -q "Gateway.*DOWN\|not.*running"; then
    # Gateway is down but not auto-restarting — systemd issue, alert only
    ALERT="Gateway is DOWN and not auto-restarting. Check systemd service."
    cat > "$ALERTS_DIR/proactive-gateway-down-$(date +%s).json" <<ALERT_EOF
{
    "id": "proactive-gateway-down-$(date +%s)",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "from": "watson",
    "severity": "critical",
    "message": "$ALERT",
    "wants_reply": false
}
ALERT_EOF
    echo "Alert sent: $ALERT"
    exit 0
fi

if ! echo "$EVE_HEALTH" | grep -q "Gateway.*UP\|running"; then
    echo "Gateway status unclear, skipping further checks"
    exit 0
fi

# Step 2: Check for stuck processes
echo "[$(date)] Running stuck-detector.py..."
STUCK_OUTPUT=$("$SCRIPTS_DIR/stuck-detector.py" 2>&1 || true)

if echo "$STUCK_OUTPUT" | grep -q "CRITICAL"; then
    # Process is critically stuck, proceed to step 3
    echo "Stuck process detected (CRITICAL), checking long-task flag..."
elif echo "$STUCK_OUTPUT" | grep -q "WARNING"; then
    # Process is long but under threshold, wait
    echo "Long process detected (WARNING), not critical, skipping restart"
    exit 0
else
    # No stuck processes
    echo "No stuck processes, all clear"
    exit 0
fi

# Step 3: Check long-task flag
echo "[$(date)] Running long-task-check.py..."
LONG_TASK_STATUS=$("$SCRIPTS_DIR/long-task-check.py" 2>&1 || true)

if [ $? -eq 2 ]; then
    # Long-task flag is active and within time window, do NOT restart
    echo "Long-task flag active, NOT restarting Eve"
    ALERT="Eve appears stuck but long-task flag is active. Waiting for task to complete."
    cat > "$ALERTS_DIR/proactive-respecting-long-task-$(date +%s).json" <<ALERT_EOF
{
    "id": "proactive-respecting-long-task-$(date +%s)",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "from": "watson",
    "severity": "info",
    "message": "$ALERT",
    "wants_reply": false
}
ALERT_EOF
    exit 0
fi

# All three conditions met: restart Eve
echo "[$(date)] All PLAYBOOK Section 1 criteria met. Restarting Eve gateway..."

RESTART_CMD="/usr/local/bin/restart-eve-gateway"
if [ -x "sudo $RESTART_CMD" ]; then
    sudo $RESTART_CMD
    sleep 2
    
    # Verify recovery
    RECOVERY=$("$SCRIPTS_DIR/eve-health.sh" 2>&1 || true)
    if echo "$RECOVERY" | grep -q "Gateway.*UP"; then
        STATUS="✓ Restart successful, gateway is UP"
    else
        STATUS="⚠ Restart executed but gateway status unclear"
    fi
else
    STATUS="✗ Restart command not found at sudo $RESTART_CMD"
fi

# Alert Amr
cat > "$ALERTS_DIR/proactive-restart-$(date +%s).json" <<ALERT_EOF
{
    "id": "proactive-restart-$(date +%s)",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "from": "watson",
    "severity": "warning",
    "message": "Watson auto-restarted Eve gateway (PLAYBOOK Section 1 criteria met). $STATUS",
    "wants_reply": false
}
ALERT_EOF

echo "Alert sent: Eve gateway restarted"
