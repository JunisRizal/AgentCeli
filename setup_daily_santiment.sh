#!/bin/bash
# Setup daily Santiment data collection

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/santiment_exchange_flows.py"
LOG_FILE="$SCRIPT_DIR/logs/santiment_daily.log"

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Create cron job entry (runs at 9 AM daily)
CRON_JOB="0 9 * * * cd $SCRIPT_DIR && /usr/bin/python3 $PYTHON_SCRIPT >> $LOG_FILE 2>&1"

echo "🕘 Setting up daily Santiment data collection..."
echo "📍 Script location: $PYTHON_SCRIPT"
echo "📝 Log file: $LOG_FILE"
echo "⏰ Schedule: Daily at 9:00 AM"

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ Daily collection scheduled!"
echo "💡 To check status: crontab -l"
echo "📊 To run manually: python3 $PYTHON_SCRIPT"
echo "📁 Data will be saved to: $SCRIPT_DIR/santiment_data/"

# Test run
echo ""
echo "🧪 Running test collection..."
cd "$SCRIPT_DIR"
python3 "$PYTHON_SCRIPT"