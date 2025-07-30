#!/bin/bash

# AgentCeli Watchdog Starter Script
# Keeps AgentCeli running with auto-restart every 10 minutes

echo "🐕 Starting AgentCeli Watchdog..."
echo "⚙️  Auto-restart every 10 minutes if data collection stops"
echo "🛑 Press Ctrl+C to stop"
echo ""

cd /Users/julius/Desktop/AgentCeli

# Make sure watchdog script is executable
chmod +x agentceli_watchdog.py

# Start the watchdog
python3 agentceli_watchdog.py