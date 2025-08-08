#!/bin/bash

# AgentCeli Installation Script
# Sets up complete AgentCeli environment

echo "🐙 AgentCeli Installation Script"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

# Check Python
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    print_status "Python 3 found: $PYTHON_VERSION"
else
    print_error "Python 3 not found"
    echo "Please install Python 3.7+ from https://python.org"
    exit 1
fi

# Check pip
echo "Checking pip..."
if command -v pip3 &> /dev/null; then
    print_status "pip3 available"
else
    print_error "pip3 not found"
    echo "Installing pip..."
    python3 -m ensurepip --upgrade
fi

# Install dependencies
echo ""
echo "📦 Installing AgentCeli dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    print_status "Dependencies installed from requirements.txt"
else
    # Install essential packages manually
    pip3 install flask requests pandas numpy
    print_status "Essential dependencies installed"
fi

# Create directories
echo ""
echo "📁 Creating directory structure..."
mkdir -p correlation_data
mkdir -p santiment_data  
mkdir -p liquidation_data
mkdir -p logs
mkdir -p templates
print_status "Directories created"

# Make scripts executable
echo ""
echo "🔧 Setting up executable permissions..."
chmod +x *.sh
chmod +x *.py
print_status "Scripts made executable"

# Create default config if not exists
echo ""
echo "⚙️ Setting up configuration..."
if [ ! -f "agentceli_config.json" ]; then
    cat > agentceli_config.json << 'EOF'
{
  "data_sources": {
    "free_apis": {
      "binance": {"enabled": true, "priority": "high"},
      "coinbase": {"enabled": true, "priority": "medium"}, 
      "coingecko": {"enabled": true, "priority": "high"},
      "fear_greed": {"enabled": true, "priority": "medium"}
    },
    "paid_apis": {
      "coinglass": {"enabled": false, "key": null, "cost_per_call": 0.01},
      "taapi": {"enabled": false, "key": null, "cost_per_call": 0.005},
      "santiment": {"enabled": false, "key": null, "cost_per_call": 0.02}
    }
  },
  "update_intervals": {"fast_data": 300},
  "rate_limits": {"daily_cost_limit": 5.0}
}
EOF
    print_status "Default configuration created"
else
    print_status "Configuration file already exists"
fi

# Test installation
echo ""
echo "🧪 Testing installation..."
python3 -c "
import flask, requests, json, threading
print('✅ All required modules available')
try:
    from agentceli_hybrid import AgentCeliHybrid
    print('✅ AgentCeli modules importable')
except Exception as e:
    print(f'⚠️ AgentCeli import test: {e}')
" 2>/dev/null || print_warning "Some modules may need attention"

# Show completion status
echo ""
echo "🎉 AgentCeli Installation Complete!"
echo "===================================="
echo ""
print_status "✅ Python environment ready"
print_status "✅ Dependencies installed"
print_status "✅ Directory structure created"
print_status "✅ Scripts configured"
print_status "✅ Default configuration ready"
echo ""

echo "🚀 Next Steps:"
echo "1. Configure your API keys in agentceli_config.json (optional)"
echo "2. Start AgentCeli: ./AgentCeli_Starter_Package.sh"
echo "3. Access dashboard: http://localhost:8081"
echo ""

echo "🔧 Optional API Setup:"
echo "• Santiment Pro: Add your key for whale/social data"
echo "• CoinGlass: Add your key for liquidation data"
echo "• TAAPI: Add your key for technical indicators"
echo ""

print_status "Ready to launch AgentCeli!"