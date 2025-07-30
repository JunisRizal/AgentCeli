#!/bin/bash

# Enhanced AgentCeli Liquidation Heatmap Starter
# Multi-source liquidation risk analysis and visualization

echo "🔥 Starting Enhanced Liquidation Heatmap..."
echo "=============================================="

# Check if config exists
if [ ! -f "agentceli_config.json" ]; then
    echo "❌ agentceli_config.json not found!"
    exit 1
fi

# Check if AgentCeli data exists
if [ ! -f "correlation_data/hybrid_latest.json" ]; then
    echo "⚠️ No AgentCeli data found. Starting AgentCeli first..."
    echo "Run: python3 agentceli_hybrid.py"
    exit 1
fi

# Check Python dependencies
echo "📦 Checking dependencies..."
python3 -c "import flask, requests, json, threading, sqlite3" 2>/dev/null || {
    echo "❌ Missing dependencies. Installing..."
    pip3 install flask requests
}

echo "✅ Dependencies ready"
echo ""

# Display configuration
echo "🔥 Enhanced Liquidation Heatmap Configuration:"
echo "   🌐 Dashboard: http://localhost:8086"
echo "   📊 API: http://localhost:8086/api/liquidation/enhanced"
echo "   🔄 Data Sources: Volatility + Whale Flows + Fear & Greed"
echo "   ⏱️ Updates: Every 5 minutes"
echo "   📈 Analysis: Multi-source risk correlation"
echo ""

# Show current data status
echo "📊 Data Source Status:"
if [ -f "correlation_data/hybrid_latest.json" ]; then
    echo "   ✅ AgentCeli price data: Available"
else
    echo "   ❌ AgentCeli price data: Missing"
fi

if [ -d "santiment_data" ]; then
    whale_files=$(ls santiment_data/*latest.json 2>/dev/null | wc -l)
    echo "   ✅ Santiment whale data: $whale_files files"
else
    echo "   ⚠️ Santiment whale data: Not available"
fi

echo ""

# Start enhanced liquidation heatmap
echo "🚀 Starting enhanced liquidation heatmap..."
echo "   Press Ctrl+C to stop"
echo ""

python3 enhanced_liquidation_heatmap.py