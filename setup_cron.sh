#!/bin/bash
# AgentCeli Cron Job Setup Script
# Richtet automatische Starts alle 60 Minuten ein

set -e

# Configuration
AGENTCELI_DIR="/Users/julius/Desktop/AgentCeli"
CRON_LOG="$AGENTCELI_DIR/logs/cron.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}⏰ AgentCeli Cron Job Setup${NC}"
echo -e "${BLUE}===========================${NC}"
echo ""

# Create cron wrapper script
create_cron_wrapper() {
    local wrapper_script="$AGENTCELI_DIR/cron_wrapper.sh"
    
    cat > "$wrapper_script" << 'EOF'
#!/bin/bash
# AgentCeli Cron Wrapper - Wird alle 60 Minuten ausgeführt

# Configuration
AGENTCELI_DIR="/Users/julius/Desktop/AgentCeli"
LOG_FILE="$AGENTCELI_DIR/logs/cron.log"
AUTOSTART_SCRIPT="$AGENTCELI_DIR/autostart_agentceli.sh"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Log function
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log_message "=== Cron Job Started ==="

# Change to AgentCeli directory
cd "$AGENTCELI_DIR"

# Check if autostart script exists
if [ ! -f "$AUTOSTART_SCRIPT" ]; then
    log_message "ERROR: Autostart script not found: $AUTOSTART_SCRIPT"
    exit 1
fi

# Check status of services
log_message "Checking service status..."
service_status=$("$AUTOSTART_SCRIPT" status 2>&1)
log_message "Service Status Output: $service_status"

# Count running services
running_services=$(echo "$service_status" | grep -c "is running" || echo "0")
log_message "Running services: $running_services"

# If less than 3 services are running, restart all
if [ "$running_services" -lt 3 ]; then
    log_message "Not enough services running ($running_services), restarting all services..."
    
    # Stop all services first
    log_message "Stopping all services..."
    "$AUTOSTART_SCRIPT" stop >> "$LOG_FILE" 2>&1
    
    # Wait a moment
    sleep 5
    
    # Start all services
    log_message "Starting all services..."
    "$AUTOSTART_SCRIPT" start >> "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        log_message "✅ Services restarted successfully"
    else
        log_message "❌ Error restarting services"
    fi
else
    log_message "✅ All services are running normally ($running_services services)"
fi

# Health check - verify dashboards are responding
log_message "Performing health checks..."

# Check Status Dashboard (8093)
if curl -s http://localhost:8093 > /dev/null 2>&1; then
    log_message "✅ Status Dashboard (8093) is responding"
else
    log_message "❌ Status Dashboard (8093) is not responding"
fi

# Check Simple Dashboard (8092)
if curl -s http://localhost:8092 > /dev/null 2>&1; then
    log_message "✅ Simple Dashboard (8092) is responding"
else
    log_message "❌ Simple Dashboard (8092) is not responding"
fi

# Check Monitor Dashboard (8090)
if curl -s http://localhost:8090 > /dev/null 2>&1; then
    log_message "✅ Monitor Dashboard (8090) is responding"
else
    log_message "❌ Monitor Dashboard (8090) is not responding"
fi

# Check data file freshness
correlation_file="$AGENTCELI_DIR/correlation_data/hybrid_latest.json"
if [ -f "$correlation_file" ]; then
    file_age=$(( $(date +%s) - $(stat -f %m "$correlation_file" 2>/dev/null || stat -c %Y "$correlation_file" 2>/dev/null || echo 0) ))
    if [ "$file_age" -lt 3600 ]; then  # Less than 1 hour old
        log_message "✅ Data files are fresh (age: ${file_age}s)"
    else
        log_message "⚠️  Data files are old (age: ${file_age}s)"
    fi
else
    log_message "❌ Main data file not found: $correlation_file"
fi

log_message "=== Cron Job Completed ==="
log_message ""

# Keep only last 1000 lines of log to prevent it from growing too large
tail -n 1000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
EOF

    chmod +x "$wrapper_script"
    echo -e "${GREEN}✅ Created cron wrapper script: $wrapper_script${NC}"
}

# Setup cron job
setup_cron_job() {
    local wrapper_script="$AGENTCELI_DIR/cron_wrapper.sh"
    local cron_entry="0 * * * * $wrapper_script"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "$wrapper_script"; then
        echo -e "${YELLOW}⚠️  Cron job already exists${NC}"
        echo "Current crontab entries for AgentCeli:"
        crontab -l 2>/dev/null | grep "$wrapper_script" || true
        
        read -p "Replace existing cron job? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Setup cancelled${NC}"
            return 1
        fi
        
        # Remove existing entries
        crontab -l 2>/dev/null | grep -v "$wrapper_script" | crontab -
        echo -e "${GREEN}✅ Removed existing cron job${NC}"
    fi
    
    # Add new cron job
    (crontab -l 2>/dev/null || true; echo "$cron_entry") | crontab -
    echo -e "${GREEN}✅ Added cron job: $cron_entry${NC}"
}

# Show cron status
show_cron_status() {
    echo -e "${BLUE}📋 Current Cron Jobs:${NC}"
    crontab -l 2>/dev/null | grep -E "(agentceli|AgentCeli)" || echo "No AgentCeli cron jobs found"
    echo ""
    
    echo -e "${BLUE}📝 Recent Cron Log (last 20 lines):${NC}"
    if [ -f "$CRON_LOG" ]; then
        tail -n 20 "$CRON_LOG"
    else
        echo "No cron log found yet"
    fi
}

# Remove cron job
remove_cron_job() {
    local wrapper_script="$AGENTCELI_DIR/cron_wrapper.sh"
    
    if crontab -l 2>/dev/null | grep -q "$wrapper_script"; then
        crontab -l 2>/dev/null | grep -v "$wrapper_script" | crontab -
        echo -e "${GREEN}✅ Removed AgentCeli cron job${NC}"
    else
        echo -e "${YELLOW}⚠️  No AgentCeli cron job found${NC}"
    fi
    
    # Remove wrapper script
    if [ -f "$wrapper_script" ]; then
        rm -f "$wrapper_script"
        echo -e "${GREEN}✅ Removed wrapper script${NC}"
    fi
}

# Main script logic
case "${1:-setup}" in
    "setup")
        echo -e "${BLUE}Setting up AgentCeli cron job...${NC}"
        echo ""
        
        # Create directories
        mkdir -p "$AGENTCELI_DIR/logs"
        
        # Create wrapper script
        create_cron_wrapper
        
        # Setup cron job
        setup_cron_job
        
        echo ""
        echo -e "${GREEN}🎉 Cron job setup complete!${NC}"
        echo ""
        echo -e "${BLUE}Configuration:${NC}"
        echo -e "   • Frequency: Every 60 minutes (0 * * * *)"
        echo -e "   • Script: $AGENTCELI_DIR/cron_wrapper.sh"
        echo -e "   • Log: $CRON_LOG"
        echo ""
        echo -e "${BLUE}What it does:${NC}"
        echo -e "   • Checks if AgentCeli services are running"
        echo -e "   • Restarts services if less than 3 are running"
        echo -e "   • Performs health checks on dashboards" 
        echo -e "   • Checks data file freshness"
        echo -e "   • Logs all activities"
        echo ""
        echo -e "${BLUE}Management commands:${NC}"
        echo -e "   • Check status: $0 status"
        echo -e "   • View logs: $0 logs"
        echo -e "   • Remove cron: $0 remove"
        ;;
        
    "status")
        show_cron_status
        ;;
        
    "logs")
        echo -e "${BLUE}📝 Full Cron Log:${NC}"
        if [ -f "$CRON_LOG" ]; then
            cat "$CRON_LOG"
        else
            echo "No cron log found yet"
        fi
        ;;
        
    "remove")
        echo -e "${YELLOW}🗑️  Removing AgentCeli cron job...${NC}"
        remove_cron_job
        echo -e "${GREEN}✅ Cron job removed${NC}"
        ;;
        
    "test")
        echo -e "${BLUE}🧪 Testing cron wrapper script...${NC}"
        wrapper_script="$AGENTCELI_DIR/cron_wrapper.sh"
        
        if [ -f "$wrapper_script" ]; then
            echo "Running wrapper script manually..."
            "$wrapper_script"
            echo ""
            echo "Check the logs:"
            tail -n 10 "$CRON_LOG"
        else
            echo -e "${RED}❌ Wrapper script not found. Run 'setup' first.${NC}"
        fi
        ;;
        
    *)
        echo -e "${BLUE}AgentCeli Cron Job Setup${NC}"
        echo -e "${BLUE}========================${NC}"
        echo ""
        echo "Usage: $0 {setup|status|logs|remove|test}"
        echo ""
        echo "Commands:"
        echo "  setup   - Setup cron job to run every 60 minutes"
        echo "  status  - Show current cron jobs and recent logs"
        echo "  logs    - Show full cron log"
        echo "  remove  - Remove AgentCeli cron job"
        echo "  test    - Test the cron wrapper script manually"
        echo ""
        echo "Default action: setup"
        ;;
esac