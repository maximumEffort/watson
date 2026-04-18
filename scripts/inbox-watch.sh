#!/bin/bash
# inbox-watch.sh -- loop inotifywait; fires inbox-poller.py on any new/closed-write in the inbox.
INBOX="/home/kraetes/eve/state/watson-inbox"
POLLER="/home/watson/watson/scripts/inbox-poller.py"

# Drain any pre-existing messages before starting the loop
python3 "$POLLER" 2>&1 | logger -t watson-inbox-watch

while inotifywait -qq -e close_write,moved_to,create "$INBOX"; do
    # Small debounce so if multiple files drop at once we process them together
    sleep 0.5
    python3 "$POLLER" 2>&1 | logger -t watson-inbox-watch
done
