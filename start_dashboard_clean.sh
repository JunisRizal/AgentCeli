#!/bin/bash
# Clean Dashboard Startup Script

echo "🧹 Starting Fresh Dashboard..."

# 1. Kill any existing dashboard processes
echo "1. Cleaning up existing processes..."
pkill -f datasource_monitor_dashboard.py 2>/dev/null
pkill -f start_monitor_dashboard.sh 2>/dev/null
sleep 2

# 2. Find available port
echo "2. Finding available port..."
DASHBOARD_PORT=8088
for port in 8088 8089 8090 9000 9001; do
  if ! lsof -ti:$port > /dev/null 2>&1; then
    DASHBOARD_PORT=$port
    echo "   ✅ Using port $port"
    break
  fi
done

# 3. Create sample data
echo "3. Creating sample data..."
python3 -c "
from datasource_monitor_dashboard import monitor
import time
from datetime import datetime

# Add realistic sample data
apis = [
    ('binance', '/api/v3/ticker/24hr', 0.15, 200, 0.0),
    ('coingecko', '/api/v3/simple/price', 0.35, 200, 0.0),
    ('santiment', '/graphql', 1.1, 200, 0.02),
    ('whale_alert', '/v1/transactions', 0.9, 200, 0.015),
    ('coinbase', '/products/stats', 0.25, 200, 0.0),
    ('fear_greed', '/fng', 0.18, 200, 0.0)
]

for api, endpoint, response_time, status, cost in apis:
    monitor.log_request(api, endpoint, response_time, status, cost)
    
print('✅ Sample data populated')
"

# 4. Start dashboard
echo "4. Starting dashboard on port $DASHBOARD_PORT..."
cd /Users/julius/Desktop/AgentCeli

# Update port in file if needed
if [ "$DASHBOARD_PORT" != "8088" ]; then
    sed -i '' "s/port=8088/port=$DASHBOARD_PORT/g" datasource_monitor_dashboard.py
    sed -i '' "s/localhost:8088/localhost:$DASHBOARD_PORT/g" datasource_monitor_dashboard.py
fi

# Start in background
python3 datasource_monitor_dashboard.py &
DASHBOARD_PID=$!

# Wait and test
sleep 4
if curl -s http://localhost:$DASHBOARD_PORT/ > /dev/null 2>&1; then
    echo "✅ Dashboard started successfully!"
    echo "🌐 URL: http://localhost:$DASHBOARD_PORT"
    echo "📊 PID: $DASHBOARD_PID"
    echo ""
    echo "🎯 Features Available:"
    echo "  • Real-time API monitoring"
    echo "  • Cost tracking with alerts"
    echo "  • Rate limiting status"
    echo "  • Interactive charts"
    echo ""
    echo "🛑 To stop: kill $DASHBOARD_PID"
else
    echo "❌ Dashboard startup failed"
    kill $DASHBOARD_PID 2>/dev/null
fi