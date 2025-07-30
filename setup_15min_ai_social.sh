#!/bin/bash
# Setup 15-minute AI Social Volume monitoring

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/santiment_ai_social_monitor.py"
LOG_FILE="$SCRIPT_DIR/logs/santiment_ai_social.log"

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Create cron job entry (runs every 15 minutes)
CRON_JOB="*/15 * * * * cd $SCRIPT_DIR && /usr/bin/python3 $PYTHON_SCRIPT >> $LOG_FILE 2>&1"

echo "🤖 Setting up 15-minute AI Social Volume monitoring..."
echo "📍 Script location: $PYTHON_SCRIPT"
echo "📝 Log file: $LOG_FILE"
echo "⏰ Schedule: Every 15 minutes"
echo "📊 Metric: social_volume_ai_total (Gesamtmarkt)"

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ 15-minute AI monitoring scheduled!"
echo "💡 To check status: crontab -l"
echo "📊 To run manually: python3 $PYTHON_SCRIPT"
echo "📁 Data will be saved to: $SCRIPT_DIR/santiment_data/"

# Test run
echo ""
echo "🧪 Running test collection..."
cd "$SCRIPT_DIR"
python3 "$PYTHON_SCRIPT"