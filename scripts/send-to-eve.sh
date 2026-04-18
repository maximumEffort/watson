#!/bin/bash
# send-to-eve.sh -- Watson's helper to initiate messages to Eve.
# Usage: send-to-eve.sh "message" [--severity info|warning|critical] [--wants-reply]
set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 \"message\" [--severity info|warning|critical] [--wants-reply]"
    exit 1
fi

MESSAGE="$1"
shift
SEVERITY="info"
WANTS_REPLY=false
PY_WANTS_REPLY="False"

while [ $# -gt 0 ]; do
    case "$1" in
        --severity)
            SEVERITY="$2"
            shift 2
            ;;
        --wants-reply)
            WANTS_REPLY=true
PY_WANTS_REPLY="True"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

INBOX="/home/kraetes/eve/state/eve-inbox"
UUID=$(uuidgen 2>/dev/null || python3 -c "import uuid; print(uuid.uuid4())")
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
FNAME="${UUID:0:8}-${TS%%T*}.json"

python3 -c "
import json, sys
msg = {
    'id': '$UUID',
    'timestamp': '$TS',
    'from': 'watson',
    'severity': '$SEVERITY',
    'message': sys.argv[1],
    'wants_reply': $PY_WANTS_REPLY,
}
with open('$INBOX/$FNAME', 'w') as f:
    json.dump(msg, f, indent=2)
" "$MESSAGE"

chmod 664 "$INBOX/$FNAME"
echo "-> Eve (ID: ${UUID:0:8}, severity: $SEVERITY)"
