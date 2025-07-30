#!/bin/bash
# Fix Dashboard Deployment Issues

echo "🔧 Fixing AgentCeli Dashboard Deployment Issues..."
echo "=" * 50

# 1. Kill existing dashboard processes
echo "1. Stopping existing dashboard processes..."
if lsof -ti:8086 > /dev/null 2>&1; then
    echo "   📌 Found process on port 8086, stopping it..."
    lsof -ti:8086 | xargs kill -9
    sleep 2
    echo "   ✅ Process stopped"
else
    echo "   ℹ️ Port 8086 is free"
fi

# 2. Check for other dashboard ports
echo "2. Checking other dashboard ports..."
for port in 5000 8081 8082; do
    if lsof -ti:$port > /dev/null 2>&1; then
        echo "   📌 Port $port in use"
    else
        echo "   ✅ Port $port available"
    fi
done

# 3. Create logs directory
echo "3. Setting up directories..."
mkdir -p logs
mkdir -p santiment_data
mkdir -p templates
echo "   ✅ Directories ready"

# 4. Check template file
echo "4. Checking template file..."
if [ -f "templates/datasource_monitor.html" ]; then
    echo "   ✅ Template file exists"
else
    echo "   ⚠️ Template file missing, this will cause deployment failure"
fi

# 5. Test dashboard startup
echo "5. Testing dashboard startup..."
cd /Users/julius/Desktop/AgentCeli

# Start dashboard in background and test
python3 datasource_monitor_dashboard.py &
DASHBOARD_PID=$!

# Wait a moment for startup
sleep 3

# Test if it's accessible
if curl -s http://localhost:8086/ > /dev/null; then
    echo "   ✅ Dashboard started successfully!"
    echo "   🌐 Access at: http://localhost:8086"
    
    # Keep it running or stop it based on user preference
    echo "   📝 Dashboard is running with PID: $DASHBOARD_PID"
    echo "   🛑 To stop: kill $DASHBOARD_PID"
else
    echo "   ❌ Dashboard failed to start"
    kill $DASHBOARD_PID 2>/dev/null
fi

echo ""
echo "🚀 Dashboard Deployment Summary:"
echo "   • Port 8086: AgentCeli Data Source Monitor"
echo "   • Features: Real-time monitoring, cost tracking, Santiment data"
echo "   • URL: http://localhost:8086"
echo "   • Logs: logs/whale_alert.log"
echo ""
echo "📋 Alternative startup commands:"
echo "   ./start_monitor_dashboard.sh"
echo "   python3 datasource_monitor_dashboard.py"