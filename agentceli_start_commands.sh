#!/bin/bash

# ========================================
# 🐙 AgentCeli - All Starting Commands
# ========================================

echo "🐙 AgentCeli Starting Commands Collection"
echo "========================================"

# Change to AgentCeli directory
cd /Users/julius/Desktop/AgentCeli

echo ""
echo "📋 AVAILABLE STARTING METHODS:"
echo "==============================="

echo ""
echo "1️⃣  RECOMMENDED: Control Script (Easy)"
echo "   python3 agentceli_control.py start"
echo "   python3 agentceli_control.py status"
echo "   python3 agentceli_control.py stop"

echo ""
echo "2️⃣  AUTO-RESTART: Watchdog (Best for Production)"
echo "   bash start_watchdog.sh"
echo "   # Automatically restarts every 10 minutes if needed"

echo ""
echo "3️⃣  DIRECT: Hybrid Agent"
echo "   python3 agentceli_hybrid.py"

echo ""
echo "4️⃣  DIRECT: Free Agent"
echo "   python3 agentceli_free.py"

echo ""
echo "5️⃣  DIRECT: Enhanced Agent"
echo "   python3 enhanced_crypto_agent.py"

echo ""
echo "6️⃣  DIRECT: Live Agent"
echo "   python3 live_crypto_agent.py"

echo ""
echo "7️⃣  CLIENT CONNECTION MANAGER"
echo "   python3 client_connection_manager.py"

echo ""
echo "8️⃣  DASHBOARD (Web Interface)"
echo "   python3 dashboard_server.py"

echo ""
echo "9️⃣  BASH STARTUP SCRIPTS"
echo "   bash start_agentceli.sh"
echo "   bash start_api.sh"

echo ""
echo "🔧 MANAGEMENT COMMANDS:"
echo "======================="
echo "   python3 agentceli_control.py menu      # Interactive menu"
echo "   python3 agentceli_control.py restart   # Restart system"
echo "   python3 agentceli_control.py status    # System status"

echo ""
echo "📊 TESTING COMMANDS:"
echo "==================="
echo "   python3 test_agentceli.py              # Run tests"
echo "   python3 data_source_expansion.py       # Test data sources"

echo ""
echo "💡 RECOMMENDED STARTUP SEQUENCE:"
echo "================================"
echo "   1. bash start_watchdog.sh              # Start with auto-restart"
echo "   2. python3 dashboard_server.py &       # Optional: Web dashboard"
echo "   3. python3 client_connection_manager.py &  # Optional: Client API"

echo ""
echo "🛑 STOP ALL COMMANDS:"
echo "===================="
echo "   python3 agentceli_control.py stop      # Stop main system"
echo "   pkill -f agentceli                     # Kill all processes"
echo "   pkill -f watchdog                      # Stop watchdog"
echo "   pkill -f dashboard                     # Stop dashboard"

echo ""
echo "✅ Current Status Check:"
echo "========================"
python3 agentceli_control.py status