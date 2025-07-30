#!/bin/bash

# AgentCeli Liquidation Heatmap Starter
# Real-time liquidation monitoring with heatmap visualization

echo "🔥 Starting AgentCeli Liquidation Heatmap..."
echo "=============================================="

# Check if config exists
if [ ! -f "agentceli_config.json" ]; then
    echo "❌ agentceli_config.json not found!"
    echo "Please ensure configuration file exists"
    exit 1
fi

# Check Python dependencies
echo "📦 Checking dependencies..."
python3 -c "import flask, requests, json, threading" 2>/dev/null || {
    echo "❌ Missing dependencies. Installing..."
    pip3 install flask requests
}

echo "✅ Dependencies ready"
echo ""

# Display configuration info
echo "📊 Liquidation Heatmap Configuration:"
echo "   🌐 Dashboard: http://localhost:8085"
echo "   📊 API: http://localhost:8085/api/liquidation/heatmap"
echo "   ⏱️ Updates: Every 5 minutes"
echo "   🔥 Data Source: CoinGlass API"
echo ""

# Start liquidation heatmap
echo "🚀 Starting liquidation heatmap monitor..."
echo "   Press Ctrl+C to stop"
echo ""

python3 liquidation_heatmap.py