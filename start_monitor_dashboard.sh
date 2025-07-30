#!/bin/bash

# AgentCeli Data Source Monitor Dashboard Startup Script

echo "🖥️ Starting AgentCeli Data Source Monitor Dashboard..."
echo "📊 Features:"
echo "  - Real-time data source monitoring"
echo "  - ⚠️  AI API cost alerts (OpenAI/Anthropic)"
echo "  - Request rate tracking per data source"
echo "  - Visual dashboard with live updates"
echo ""
echo "🌐 Dashboard will be available at:"
echo "   http://localhost:8088"
echo ""
echo "🛑 Press Ctrl+C to stop"
echo ""

cd /Users/julius/Desktop/AgentCeli
python3 datasource_monitor_dashboard.py