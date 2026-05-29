#!/bin/bash
# Install cron job for PSP video archive sync.
# Runs every 2 hours; edit the schedule as needed.
# Usage: bash setup_cron.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$(which python3)"
LOG="$SCRIPT_DIR/sync.log"

CRON_LINE="0 */2 * * * cd \"$SCRIPT_DIR\" && $PYTHON sync.py >> \"$LOG\" 2>&1"

# Remove any existing entry for this script, then add the new one
( crontab -l 2>/dev/null | grep -v "psp/videoarchive/sync.py" ; echo "$CRON_LINE" ) | crontab -

echo "Installed cron job:"
crontab -l | grep "sync.py"
echo ""
echo "Log file: $LOG"
echo "To run manually: cd $SCRIPT_DIR && python3 sync.py"
echo "To check status: cd $SCRIPT_DIR && python3 sync.py --status"
