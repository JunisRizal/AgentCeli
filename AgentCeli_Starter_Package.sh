#!/bin/bash

# AgentCeli Complete Starter Package
# One-click deployment for comprehensive crypto data collection and analysis

clear
echo "🐙 AgentCeli Complete Starter Package"
echo "======================================"
echo "Comprehensive cryptocurrency data collection, analysis and visualization"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored status
print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️${NC} $1"
}

print_header() {
    echo -e "${PURPLE}$1${NC}"
}

# Check system requirements
print_header "📋 System Requirements Check"
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    print_status "Python 3 found: $PYTHON_VERSION"
else
    print_error "Python 3 not found. Please install Python 3.7+"
    exit 1
fi

echo "Checking pip..."
if command -v pip3 &> /dev/null; then
    print_status "pip3 available"
else
    print_error "pip3 not found. Please install pip"
    exit 1
fi

# Check configuration
print_header "⚙️ Configuration Check"
if [ -f "agentceli_config.json" ]; then
    print_status "agentceli_config.json found"
    
    # Check for Santiment Pro key
    if grep -q '"santiment"' agentceli_config.json && grep -q '"enabled": true' agentceli_config.json; then
        print_status "Santiment Pro configuration detected"
    else
        print_warning "Santiment Pro not configured (optional)"
    fi
else
    print_error "agentceli_config.json not found!"
    echo "Creating default configuration..."
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
fi

# Install dependencies
print_header "📦 Installing Dependencies"
echo "Installing required Python packages..."
pip3 install -q flask requests sqlite3 threading pathlib datetime || {
    print_error "Failed to install dependencies"
    exit 1
}
print_status "Dependencies installed"

# Create directories
print_header "📁 Setting Up Directories"
mkdir -p correlation_data
mkdir -p santiment_data
mkdir -p liquidation_data
mkdir -p logs
mkdir -p templates
print_status "Directories created"

# Make scripts executable
print_header "🔧 Setting Up Scripts"
chmod +x start_*.sh
chmod +x setup_*.sh
chmod +x *.py
print_status "Scripts made executable"

echo ""
print_header "🚀 AgentCeli Startup Options"
echo ""

# Main menu function
show_menu() {
    echo -e "${CYAN}Select AgentCeli component to start:${NC}"
    echo ""
    echo "1) 🐙 AgentCeli Core Data Collection"
    echo "2) 📊 Master Dashboard (Recommended)"
    echo "3) 🔥 Enhanced Liquidation Heatmap"
    echo "4) 🐋 Santiment Whale Monitoring"
    echo "5) 📈 All Services (Full Stack)"
    echo "6) ⚙️ Configuration & Status"
    echo "7) 🧹 Clean & Reset"
    echo "8) ❌ Exit"
    echo ""
    echo -n "Enter your choice [1-8]: "
}

# Start individual services
start_agentceli_core() {
    print_header "🐙 Starting AgentCeli Core Data Collection"
    echo "Port: 8080 | Updates: Every 5 minutes"
    echo "Press Ctrl+C to stop"
    echo ""
    python3 agentceli_hybrid.py
}

start_master_dashboard() {
    print_header "📊 Starting Master Dashboard"
    echo "Dashboard: http://localhost:8081"
    echo "Features: Service management, real-time monitoring, data source controls"
    echo "Press Ctrl+C to stop"
    echo ""
    python3 agentceli_master_dashboard.py
}

start_liquidation_heatmap() {
    print_header "🔥 Starting Enhanced Liquidation Heatmap"
    echo "Dashboard: http://localhost:8086"
    echo "Features: Multi-source risk analysis, liquidation zones, Fear & Greed correlation"
    echo "Press Ctrl+C to stop"
    echo ""
    python3 enhanced_liquidation_heatmap.py
}

start_santiment_monitoring() {
    print_header "🐋 Starting Santiment Whale Monitoring"
    echo "Starting multiple Santiment collectors..."
    
    # Start AI social monitoring
    if [ -f "santiment_ai_social_monitor.py" ]; then
        echo "Starting AI social monitoring..."
        python3 santiment_ai_social_monitor.py &
    fi
    
    # Start whale alerts
    if [ -f "santiment_whale_alerts.py" ]; then
        echo "Starting whale alerts..."
        python3 santiment_whale_alerts.py &
    fi
    
    # Start exchange flows
    if [ -f "santiment_exchange_flows.py" ]; then
        echo "Starting exchange flows..."
        python3 santiment_exchange_flows.py &
    fi
    
    print_status "Santiment monitoring started"
    echo "Data will be saved to santiment_data/"
    echo "Press Ctrl+C to stop all processes"
    wait
}

start_all_services() {
    print_header "📈 Starting All AgentCeli Services"
    echo "This will start all components in background..."
    echo ""
    
    # Start core data collection
    echo "Starting AgentCeli core..."
    python3 agentceli_hybrid.py &
    CORE_PID=$!
    
    sleep 3
    
    # Start master dashboard
    echo "Starting master dashboard..."
    python3 agentceli_master_dashboard.py &
    DASHBOARD_PID=$!
    
    sleep 2
    
    # Start liquidation heatmap
    echo "Starting liquidation heatmap..."
    python3 enhanced_liquidation_heatmap.py &
    HEATMAP_PID=$!
    
    sleep 2
    
    print_status "All services started!"
    echo ""
    echo -e "${GREEN}🌐 Access Points:${NC}"
    echo "   Core API: http://localhost:8080"
    echo "   Master Dashboard: http://localhost:8081"
    echo "   Liquidation Heatmap: http://localhost:8086"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Wait and cleanup on exit
    trap "echo 'Stopping all services...'; kill $CORE_PID $DASHBOARD_PID $HEATMAP_PID 2>/dev/null; exit" SIGINT
    wait
}

show_configuration() {
    print_header "⚙️ AgentCeli Configuration & Status"
    echo ""
    
    # Show configuration
    echo "📋 Current Configuration:"
    if [ -f "agentceli_config.json" ]; then
        echo "   Config file: ✅ Found"
        
        # Check API status
        if grep -q '"santiment".*"enabled": true' agentceli_config.json; then
            echo "   Santiment Pro: ✅ Enabled"
        else
            echo "   Santiment Pro: ⚠️ Disabled"
        fi
        
        if grep -q '"coinglass".*"enabled": true' agentceli_config.json; then
            echo "   CoinGlass: ✅ Enabled"
        else
            echo "   CoinGlass: ⚠️ Disabled"
        fi
    else
        echo "   Config file: ❌ Missing"
    fi
    
    echo ""
    echo "📊 Data Status:"
    
    # Check data files
    if [ -f "correlation_data/hybrid_latest.json" ]; then
        echo "   Core data: ✅ Available"
        LAST_UPDATE=$(grep -o '"timestamp": "[^"]*"' correlation_data/hybrid_latest.json | cut -d'"' -f4)
        echo "   Last update: $LAST_UPDATE"
    else
        echo "   Core data: ❌ No data collected yet"
    fi
    
    if [ -d "santiment_data" ] && [ "$(ls -A santiment_data)" ]; then
        SANTIMENT_FILES=$(ls santiment_data/*latest.json 2>/dev/null | wc -l)
        echo "   Santiment data: ✅ $SANTIMENT_FILES files available"
    else
        echo "   Santiment data: ⚠️ No data available"
    fi
    
    if [ -d "liquidation_data" ] && [ "$(ls -A liquidation_data)" ]; then
        echo "   Liquidation data: ✅ Available"
    else
        echo "   Liquidation data: ⚠️ Not generated yet"
    fi
    
    echo ""
    echo "🔧 Available Scripts:"
    echo "   ./start_enhanced_liquidation_heatmap.sh"
    echo "   ./agentceli_start_commands.sh"
    echo "   python3 agentceli_hybrid.py"
    echo "   python3 agentceli_master_dashboard.py"
    
    echo ""
    echo "Press any key to return to main menu..."
    read -n 1
}

clean_and_reset() {
    print_header "🧹 Clean & Reset AgentCeli"
    echo ""
    echo "This will:"
    echo "- Stop all running processes"
    echo "- Clear log files"
    echo "- Reset data collection"
    echo "- Keep configuration and source code"
    echo ""
    echo -n "Are you sure? [y/N]: "
    read -n 1 CONFIRM
    echo ""
    
    if [[ $CONFIRM =~ ^[Yy]$ ]]; then
        echo "Cleaning AgentCeli..."
        
        # Stop processes
        pkill -f "agentceli" 2>/dev/null || true
        pkill -f "santiment" 2>/dev/null || true
        
        # Clean logs
        if [ -d "logs" ]; then
            rm -f logs/*.log
            echo "Logs cleared"
        fi
        
        # Reset monitoring database
        if [ -f "monitoring.db" ]; then
            rm -f monitoring.db
            echo "Monitoring database reset"
        fi
        
        print_status "AgentCeli cleaned and reset"
    else
        echo "Cancelled"
    fi
    
    echo ""
    echo "Press any key to return to main menu..."
    read -n 1
}

# Main menu loop
while true; do
    clear
    echo "🐙 AgentCeli Complete Starter Package"
    echo "======================================"
    echo ""
    
    show_menu
    read CHOICE
    
    case $CHOICE in
        1)
            start_agentceli_core
            ;;
        2)
            start_master_dashboard
            ;;
        3)
            start_liquidation_heatmap
            ;;
        4)
            start_santiment_monitoring
            ;;
        5)
            start_all_services
            ;;
        6)
            show_configuration
            ;;
        7)
            clean_and_reset
            ;;
        8)
            print_status "Thanks for using AgentCeli!"
            exit 0
            ;;
        *)
            print_error "Invalid option. Please try again."
            sleep 2
            ;;
    esac
done