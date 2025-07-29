#!/bin/bash
# Start AgentCeli API for websites

cd /Users/julius/Desktop/AgentCeli

echo "🚀 Starting AgentCeli API endpoints..."

# Start main AgentCeli if not running
if ! curl -s http://localhost:8080/api/status > /dev/null; then
    echo "Starting main AgentCeli..."
    python3 agentceli_control.py start
    sleep 3
fi

# Start public API server
echo "Starting public API server (port 8082)..."
python3 public_api_server.py &
PUBLIC_PID=$!

echo "✅ AgentCeli API ready!"
echo "🔗 Your website endpoint: http://localhost:8082/api/crypto/latest"
echo "🔗 Simple prices: http://localhost:8082/api/crypto/prices"
echo "📊 Current data: BTC \$$(curl -s http://localhost:8082/api/crypto/prices | python3 -c 'import sys, json; print(f\"{json.load(sys.stdin)[\"btc\"]:,.2f}\")')"

# Save PID for stopping
echo $PUBLIC_PID > public_api.pid