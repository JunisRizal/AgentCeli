#!/bin/bash
# AgentCeli Startup Script
# Starts the crypto data collection system after shutdown

echo "🚀 Starting AgentCeli Data Collection System"
echo "=============================================="

# Change to AgentCeli directory
cd /Users/julius/Desktop/AgentCeli || {
    echo "❌ Error: Cannot find AgentCeli directory"
    exit 1
}

echo "📍 Working directory: $(pwd)"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 not found"
    exit 1
fi

# Check required files
required_files=("agentceli_hybrid.py" "agentceli_free.py" "connect_correlation.py")
missing_files=()

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        missing_files+=("$file")
    fi
done

if [[ ${#missing_files[@]} -gt 0 ]]; then
    echo "❌ Missing required files:"
    printf '   • %s\n' "${missing_files[@]}"
    exit 1
fi

echo "✅ All required files found"

# Create data directories if they don't exist
mkdir -p correlation_data agentceli_data delivery_output
echo "✅ Data directories ready"

# Test internet connection
echo "🌐 Testing internet connection..."
if ping -c 1 google.com &> /dev/null; then
    echo "✅ Internet connection OK"
else
    echo "❌ No internet connection - AgentCeli needs internet for live data"
    exit 1
fi

# Test API connections
echo "📡 Testing crypto API connections..."

test_binance() {
    if curl -s --connect-timeout 5 "https://api.binance.com/api/v3/ping" > /dev/null; then
        echo "✅ Binance API: Connected"
        return 0
    else
        echo "⚠️ Binance API: Failed"
        return 1
    fi
}

test_coingecko() {
    if curl -s --connect-timeout 5 "https://api.coingecko.com/api/v3/ping" > /dev/null; then
        echo "✅ CoinGecko API: Connected"
        return 0
    else
        echo "⚠️ CoinGecko API: Failed"
        return 1
    fi
}

test_binance
binance_ok=$?

test_coingecko
coingecko_ok=$?

if [[ $binance_ok -ne 0 && $coingecko_ok -ne 0 ]]; then
    echo "❌ Error: No crypto APIs available"
    exit 1
fi

echo

# Show options
echo "📋 Startup Options:"
echo "1. Start AgentCeli Hybrid (recommended)"
echo "2. Start AgentCeli Free (basic version)"
echo "3. Start AgentCeli Kraken (full API server)"
echo "4. Quick test and exit"

# Check for command line argument
if [[ $# -gt 0 ]]; then
    choice=$1
    echo "Using command line option: $choice"
else
    read -p "Choose option (1-4): " choice
fi

case $choice in
    1)
        echo "🚀 Starting AgentCeli Hybrid..."
        echo "💡 This version: FREE APIs + option to add paid APIs later"
        echo
        python3 agentceli_hybrid.py &
        AGENTCELI_PID=$!
        echo "✅ AgentCeli Hybrid started (PID: $AGENTCELI_PID)"
        ;;
    
    2)
        echo "🚀 Starting AgentCeli Free..."
        echo "💡 This version: Only free APIs"
        echo
        python3 agentceli_free.py &
        AGENTCELI_PID=$!
        echo "✅ AgentCeli Free started (PID: $AGENTCELI_PID)"
        ;;
    
    3)
        echo "🚀 Starting AgentCeli Kraken..."
        echo "💡 This version: Full API server + file system"
        echo
        python3 agentceli_kraken.py &
        AGENTCELI_PID=$!
        echo "✅ AgentCeli Kraken started (PID: $AGENTCELI_PID)"
        ;;
    
    4)
        echo "🔍 Running connection test..."
        python3 -c "
from connect_correlation import CryptoPredictor1h1d3d

print('Testing AgentCeli connection...')
try:
    predictor = CryptoPredictor1h1d3d()
    print('✅ Connection module loaded successfully')
except Exception as e:
    print(f'❌ Connection test failed: {e}')
"
        exit 0
        ;;
    
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

# Wait for startup
echo "⏳ Waiting for AgentCeli to initialize..."
sleep 5

# Check if process is still running
if kill -0 $AGENTCELI_PID 2>/dev/null; then
    echo "✅ AgentCeli is running (PID: $AGENTCELI_PID)"
else
    echo "❌ AgentCeli failed to start"
    exit 1
fi

# Show status
echo
echo "📊 AgentCeli Status:"
echo "   • Process ID: $AGENTCELI_PID"
echo "   • Data directory: $(pwd)/correlation_data/"
echo "   • Log files: Check terminal output"

# Check if API server is running (for hybrid/kraken)
if [[ $choice == "1" || $choice == "3" ]]; then
    echo "🌐 Checking API server..."
    sleep 3
    
    if curl -s http://localhost:8080/api/status > /dev/null 2>&1; then
        echo "✅ HTTP API server: http://localhost:8080"
        echo "   • Status: http://localhost:8080/api/status"
        echo "   • Prices: http://localhost:8080/api/prices"
    else
        echo "⚠️ HTTP API server not yet available (may take a moment)"
    fi
fi

# Show data files
echo
echo "📁 Data Files (will be created as data comes in):"
echo "   • correlation_data/hybrid_latest.csv"
echo "   • correlation_data/hybrid_latest.json"  
echo "   • correlation_data/hybrid_crypto_data.db"

# Show connection info for correlation system
echo
echo "🔗 For Your Correlation System:"
echo "   Use this in your Agents-main3kopie code:"
echo
echo "   from connect_correlation import CryptoPredictor1h1d3d"
echo "   predictor = CryptoPredictor1h1d3d("
echo "       agentceli_data_path='/Users/julius/Desktop/AgentCeli/correlation_data'"
echo "   )"

# Show stop instructions
echo
echo "⏹️ To Stop AgentCeli:"
echo "   kill $AGENTCELI_PID"
echo "   or press Ctrl+C"

echo
echo "🎉 AgentCeli startup complete!"
echo "📊 Live crypto data collection is now running"

# Save PID for easy stopping
echo $AGENTCELI_PID > agentceli.pid
echo "💾 PID saved to agentceli.pid"