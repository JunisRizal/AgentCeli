#!/bin/bash
# AgentCeli Server Autostart Script
# Startet alle wichtigen AgentCeli Services automatisch

set -e  # Exit on any error

# Configuration
AGENTCELI_DIR="/Users/julius/Desktop/AgentCeli"
LOG_DIR="$AGENTCELI_DIR/logs"
PID_DIR="$AGENTCELI_DIR/pids"

# Create directories if they don't exist
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AgentCeli Server Autostart${NC}"
echo -e "${BLUE}================================${NC}"
echo "Directory: $AGENTCELI_DIR"
echo "Log Directory: $LOG_DIR"
echo "PID Directory: $PID_DIR"
echo ""

# Function to start a service
start_service() {
    local service_name=$1
    local script_file=$2
    local port=$3
    local description=$4
    
    echo -e "${YELLOW}Starting $service_name...${NC}"
    
    # Check if script exists
    if [ ! -f "$AGENTCELI_DIR/$script_file" ]; then
        echo -e "${RED}❌ Error: $script_file not found${NC}"
        return 1
    fi
    
    # Check if port is already in use
    if [ ! -z "$port" ]; then
        if lsof -i :$port > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  Port $port already in use, stopping existing process...${NC}"
            pkill -f "$script_file" || true
            sleep 2
        fi
    fi
    
    # Start the service
    cd "$AGENTCELI_DIR"
    nohup python3 "$script_file" > "$LOG_DIR/${service_name}.log" 2>&1 &
    local pid=$!
    echo $pid > "$PID_DIR/${service_name}.pid"
    
    # Wait a moment and check if process is still running
    sleep 2
    if kill -0 $pid 2>/dev/null; then
        echo -e "${GREEN}✅ $service_name started (PID: $pid)${NC}"
        if [ ! -z "$port" ]; then
            echo -e "   📊 URL: http://localhost:$port"
        fi
        echo -e "   📝 Log: $LOG_DIR/${service_name}.log"
        echo -e "   💬 $description"
    else
        echo -e "${RED}❌ Failed to start $service_name${NC}"
        return 1
    fi
    
    echo ""
}

# Function to check if a service is running
check_service() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            echo -e "${GREEN}✅ $service_name is running (PID: $pid)${NC}"
            return 0
        else
            echo -e "${RED}❌ $service_name is not running${NC}"
            rm -f "$pid_file"
            return 1
        fi
    else
        echo -e "${RED}❌ $service_name is not running${NC}"
        return 1
    fi
}

# Function to stop all services
stop_all_services() {
    echo -e "${YELLOW}🛑 Stopping all AgentCeli services...${NC}"
    
    # Stop by PID files
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            local service_name=$(basename "$pid_file" .pid)
            local pid=$(cat "$pid_file")
            
            if kill -0 $pid 2>/dev/null; then
                echo -e "${YELLOW}Stopping $service_name (PID: $pid)...${NC}"
                kill $pid
                sleep 1
                if kill -0 $pid 2>/dev/null; then
                    kill -9 $pid
                fi
                echo -e "${GREEN}✅ $service_name stopped${NC}"
            fi
            rm -f "$pid_file"
        fi
    done
    
    # Fallback: stop by process name
    pkill -f "agentceli_hybrid.py" || true
    pkill -f "status_dashboard.py" || true
    pkill -f "simple_dashboard.py" || true
    pkill -f "datasource_monitor_dashboard.py" || true
    pkill -f "liquidation_analyzer.py" || true
    
    echo -e "${GREEN}✅ All services stopped${NC}"
}

# Main script logic
case "${1:-start}" in
    "start")
        echo -e "${BLUE}🚀 Starting AgentCeli Services...${NC}"
        echo ""
        
        # 1. Data Collection (Core Service)
        start_service "data_collector" "agentceli_hybrid.py" "" "Core data collection from APIs"
        
        # 2. Liquidation Analyzer
        start_service "liquidation_analyzer" "liquidation_analyzer.py" "" "Risk analysis and liquidation calculations"
        
        # 3. Status Dashboard (Main Dashboard)
        start_service "status_dashboard" "status_dashboard.py" "8093" "Main status overview dashboard"
        
        # 4. Simple Dashboard (User Interface)
        start_service "simple_dashboard" "simple_dashboard.py" "8092" "User-friendly crypto dashboard"
        
        # 5. Data Source Monitor (Admin Interface)
        start_service "monitor_dashboard" "datasource_monitor_dashboard.py" "8090" "API monitoring and cost tracking"
        
        echo -e "${GREEN}🎉 AgentCeli Server startup complete!${NC}"
        echo ""
        echo -e "${BLUE}📊 Available Dashboards:${NC}"
        echo -e "   • Status Dashboard: http://localhost:8093 (Main Overview)"
        echo -e "   • Simple Dashboard: http://localhost:8092 (User Interface)"
        echo -e "   • Monitor Dashboard: http://localhost:8090 (Admin Interface)"
        echo ""
        echo -e "${BLUE}📝 Logs Directory: $LOG_DIR${NC}"
        echo -e "${BLUE}🔄 To stop all services: $0 stop${NC}"
        echo -e "${BLUE}📋 To check status: $0 status${NC}"
        ;;
        
    "stop")
        stop_all_services
        ;;
        
    "restart")
        stop_all_services
        sleep 3
        $0 start
        ;;
        
    "status")
        echo -e "${BLUE}📋 AgentCeli Services Status${NC}"
        echo -e "${BLUE}=============================${NC}"
        
        check_service "data_collector"
        check_service "liquidation_analyzer"
        check_service "status_dashboard"
        check_service "simple_dashboard"
        check_service "monitor_dashboard"
        
        echo ""
        echo -e "${BLUE}📊 Port Status:${NC}"
        echo -e "   Port 8090: $(lsof -i :8090 > /dev/null 2>&1 && echo -e "${GREEN}Open${NC}" || echo -e "${RED}Closed${NC}") (Monitor Dashboard)"
        echo -e "   Port 8092: $(lsof -i :8092 > /dev/null 2>&1 && echo -e "${GREEN}Open${NC}" || echo -e "${RED}Closed${NC}") (Simple Dashboard)"
        echo -e "   Port 8093: $(lsof -i :8093 > /dev/null 2>&1 && echo -e "${GREEN}Open${NC}" || echo -e "${RED}Closed${NC}") (Status Dashboard)"
        ;;
        
    "logs")
        echo -e "${BLUE}📝 Recent Logs (last 20 lines each)${NC}"
        echo -e "${BLUE}====================================${NC}"
        
        for log_file in "$LOG_DIR"/*.log; do
            if [ -f "$log_file" ]; then
                local service_name=$(basename "$log_file" .log)
                echo -e "${YELLOW}--- $service_name ---${NC}"
                tail -n 20 "$log_file"
                echo ""
            fi
        done
        ;;
        
    "install")
        echo -e "${BLUE}📦 Installing AgentCeli as System Service${NC}"
        echo -e "${BLUE}=========================================${NC}"
        
        # Create systemd service file
        cat > /tmp/agentceli.service << EOF
[Unit]
Description=AgentCeli Crypto Data Intelligence Platform
After=network.target

[Service]
Type=forking
User=$(whoami)
WorkingDirectory=$AGENTCELI_DIR
ExecStart=$AGENTCELI_DIR/autostart_agentceli.sh start
ExecStop=$AGENTCELI_DIR/autostart_agentceli.sh stop
ExecReload=$AGENTCELI_DIR/autostart_agentceli.sh restart
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        echo "Service file created. To install as system service:"
        echo "sudo cp /tmp/agentceli.service /etc/systemd/system/"
        echo "sudo systemctl daemon-reload"
        echo "sudo systemctl enable agentceli"
        echo "sudo systemctl start agentceli"
        ;;
        
    *)
        echo -e "${BLUE}AgentCeli Server Management Script${NC}"
        echo -e "${BLUE}==================================${NC}"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|install}"
        echo ""
        echo "Commands:"
        echo "  start    - Start all AgentCeli services"
        echo "  stop     - Stop all AgentCeli services"
        echo "  restart  - Restart all AgentCeli services"
        echo "  status   - Show status of all services"
        echo "  logs     - Show recent logs from all services"
        echo "  install  - Install as system service (requires sudo)"
        echo ""
        echo "Default action: start"
        ;;
esac