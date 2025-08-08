#!/bin/bash

# AgentCeli - START HERE
# Complete onboarding and startup script

clear
echo "🐙 Welcome to AgentCeli!"
echo "========================"
echo "Comprehensive Cryptocurrency Intelligence Platform"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠️${NC} $1"; }
print_error() { echo -e "${RED}❌${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ️${NC} $1"; }
print_header() { echo -e "${PURPLE}$1${NC}"; }

# Check if this is first run
FIRST_RUN=false
if [ ! -f ".agentceli_initialized" ]; then
    FIRST_RUN=true
fi

if [ "$FIRST_RUN" = true ]; then
    print_header "🎯 First Time Setup"
    echo ""
    echo "Welcome to AgentCeli! This appears to be your first run."
    echo "Let's get you set up quickly..."
    echo ""
    
    # Run installation
    print_info "Running automatic installation..."
    ./install_agentceli.sh
    
    # Mark as initialized
    touch .agentceli_initialized
    
    echo ""
    print_status "Installation complete!"
    echo ""
fi

# Main startup interface
print_header "🚀 AgentCeli Quick Start"
echo ""

# Check system status
print_info "System Status Check:"

# Check configuration
if [ -f "agentceli_config.json" ]; then
    print_status "Configuration: Ready"
    
    # Check for API keys
    if grep -q '"santiment".*"enabled": true' agentceli_config.json; then
        print_status "Santiment Pro: Configured"
    else
        print_warning "Santiment Pro: Not configured (optional)"
    fi
else
    print_error "Configuration: Missing"
fi

# Check data
if [ -f "correlation_data/hybrid_latest.json" ]; then
    print_status "Data Collection: Active"
else
    print_warning "Data Collection: Not started yet"
fi

# Check if services are running
if pgrep -f "agentceli_hybrid.py" > /dev/null; then
    print_status "Core Service: Running"
else
    print_warning "Core Service: Stopped"
fi

echo ""
print_header "📊 What AgentCeli Provides:"
echo ""
echo "🐙 Core Data Collection:"
echo "   • Real-time prices from Binance, CoinGecko"
echo "   • Fear & Greed Index monitoring" 
echo "   • Multi-source data aggregation"
echo ""
echo "📊 Master Dashboard:"
echo "   • Service management and monitoring"
echo "   • Real-time data visualization"
echo "   • Data source control panel"
echo ""
echo "🔥 Liquidation Heatmap:"
echo "   • Multi-source risk analysis"
echo "   • Volatility-based liquidation estimates"
echo "   • Whale movement correlation"
echo "   • Fear & Greed sentiment integration"
echo ""
echo "🐋 Santiment Pro Integration (Optional):"
echo "   • Whale transaction alerts"
echo "   • Exchange flow analysis"
echo "   • AI social sentiment tracking"
echo ""

# Startup options
echo ""
print_header "🎛️ Quick Launch Options:"
echo ""
echo "1) 🚀 Launch Everything (Recommended for first time)"
echo "2) 📊 Master Dashboard Only"
echo "3) 🔥 Liquidation Heatmap Only"
echo "4) 🐙 Core Data Collection Only"
echo "5) ⚙️ Configuration & Setup"
echo "6) 📚 View Documentation"
echo "7) ❌ Exit"
echo ""

while true; do
    echo -n "Select option [1-7]: "
    read CHOICE
    
    case $CHOICE in
        1)
            print_header "🚀 Launching Complete AgentCeli Stack"
            echo ""
            print_info "This will start all AgentCeli components:"
            echo "   • Core data collection (Port 8080)"
            echo "   • Master dashboard (Port 8081)"
            echo "   • Liquidation heatmap (Port 8086)"
            echo ""
            echo "🌐 You'll be able to access:"
            echo "   http://localhost:8081 - Master Dashboard"
            echo "   http://localhost:8086 - Liquidation Heatmap"
            echo ""
            echo "Press Enter to continue or Ctrl+C to cancel..."
            read
            
            ./AgentCeli_Starter_Package.sh
            break
            ;;
        2)
            print_header "📊 Starting Master Dashboard"
            echo ""
            echo "🌐 Dashboard will be available at: http://localhost:8081"
            echo "Press Enter to continue..."
            read
            
            python3 agentceli_master_dashboard.py
            break
            ;;
        3)
            print_header "🔥 Starting Liquidation Heatmap"
            echo ""
            echo "🌐 Heatmap will be available at: http://localhost:8086"
            echo "Press Enter to continue..."
            read
            
            python3 enhanced_liquidation_heatmap.py
            break
            ;;
        4)
            print_header "🐙 Starting Core Data Collection"
            echo ""
            echo "🔄 Data collection will start with 5-minute updates"
            echo "📊 API available at: http://localhost:8080"
            echo "Press Enter to continue..."
            read
            
            python3 agentceli_hybrid.py
            break
            ;;
        5)
            print_header "⚙️ Configuration & Setup"
            echo ""
            
            # Show current config
            echo "📋 Current Configuration:"
            if [ -f "agentceli_config.json" ]; then
                echo "Config file exists. Key settings:"
                
                # Show enabled APIs
                echo ""
                echo "🆓 Free APIs enabled:"
                grep -A 10 '"free_apis"' agentceli_config.json | grep '"enabled": true' | while read line; do
                    api=$(echo $line | grep -o '"[^"]*"' | head -1 | tr -d '"')
                    echo "   • $api"
                done
                
                echo ""
                echo "💰 Paid APIs enabled:"
                grep -A 20 '"paid_apis"' agentceli_config.json | grep -B 1 '"enabled": true' | grep -o '"[^"]*"' | head -1 | while read api; do
                    if [ ! -z "$api" ]; then
                        echo "   • $(echo $api | tr -d '"')"
                    fi
                done
            else
                print_error "No configuration file found"
                echo "Run option 1 to create default configuration"
            fi
            
            echo ""
            echo "🔧 To configure API keys:"
            echo "   1. Edit agentceli_config.json"
            echo "   2. Add your API keys for paid services"
            echo "   3. Set 'enabled': true for APIs you want to use"
            echo ""
            echo "Press any key to continue..."
            read -n 1
            ;;
        6)
            print_header "📚 AgentCeli Documentation"
            echo ""
            
            if [ -f "README_AgentCeli.md" ]; then
                echo "📖 Full documentation available in: README_AgentCeli.md"
                echo ""
                echo "🔗 Quick Links:"
                echo "   • System Architecture"
                echo "   • API Configuration"
                echo "   • Data Sources & Outputs"
                echo "   • Troubleshooting Guide"
                echo "   • Integration Examples"
                echo ""
                echo "🌐 Web Interfaces:"
                echo "   • http://localhost:8081 - Master Dashboard"
                echo "   • http://localhost:8086 - Liquidation Heatmap"
                echo "   • http://localhost:8080 - Core API"
                echo ""
            else
                print_warning "Documentation file not found"
            fi
            
            echo "Press any key to continue..."
            read -n 1
            ;;
        7)
            print_status "Thanks for using AgentCeli!"
            exit 0
            ;;
        *)
            print_error "Invalid option. Please select 1-7."
            ;;
    esac
done