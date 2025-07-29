#!/bin/bash

# AgentCeli Data Collector Script
# Description: Bash script to easily collect AgentCeli data via API
# Author: Generated for AgentCeli project
# Usage: ./collect_agentceli_data.sh [options]

set -euo pipefail

# Configuration
AGENTCELI_HOST=${AGENTCELI_HOST:-"localhost"}
MAIN_API_PORT=${MAIN_API_PORT:-8080}
PUBLIC_API_PORT=${PUBLIC_API_PORT:-8082}
CLIENT_API_PORT=${CLIENT_API_PORT:-8081}
DASHBOARD_PORT=${DASHBOARD_PORT:-8083}

OUTPUT_DIR=${OUTPUT_DIR:-"./agentceli_data_collection"}
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# Create output directory
create_output_dir() {
    mkdir -p "$OUTPUT_DIR"
    log_info "Created output directory: $OUTPUT_DIR"
}

# Check if AgentCeli services are running
check_services() {
    local services_status=()
    
    log_info "Checking AgentCeli services..."
    
    # Check Main API Server
    if curl -s "http://${AGENTCELI_HOST}:${MAIN_API_PORT}/api/health" >/dev/null 2>&1; then
        log_info "✓ Main API Server (port $MAIN_API_PORT) - RUNNING"
        services_status+=("main_api:running")
    else
        log_warn "✗ Main API Server (port $MAIN_API_PORT) - NOT RUNNING"
        services_status+=("main_api:down")
    fi
    
    # Check Public API Server
    if curl -s "http://${AGENTCELI_HOST}:${PUBLIC_API_PORT}/api/health" >/dev/null 2>&1; then
        log_info "✓ Public API Server (port $PUBLIC_API_PORT) - RUNNING"
        services_status+=("public_api:running")
    else
        log_warn "✗ Public API Server (port $PUBLIC_API_PORT) - NOT RUNNING"
        services_status+=("public_api:down")
    fi
    
    # Check Client API Server
    if curl -s "http://${AGENTCELI_HOST}:${CLIENT_API_PORT}/api/health" >/dev/null 2>&1; then
        log_info "✓ Client API Server (port $CLIENT_API_PORT) - RUNNING"
        services_status+=("client_api:running")
    else
        log_warn "✗ Client API Server (port $CLIENT_API_PORT) - NOT RUNNING"
        services_status+=("client_api:down")
    fi
    
    # Check Dashboard Server
    if curl -s "http://${AGENTCELI_HOST}:${DASHBOARD_PORT}/api/dashboard/status" >/dev/null 2>&1; then
        log_info "✓ Dashboard Server (port $DASHBOARD_PORT) - RUNNING"
        services_status+=("dashboard:running")
    else
        log_warn "✗ Dashboard Server (port $DASHBOARD_PORT) - NOT RUNNING"
        services_status+=("dashboard:down")
    fi
    
    echo "${services_status[@]}"
}

# Fetch data from a specific endpoint
fetch_data() {
    local url="$1"
    local output_file="$2"
    local description="$3"
    
    log_info "Fetching $description..."
    log_debug "URL: $url"
    log_debug "Output: $output_file"
    
    if curl -s -o "$output_file" -w "%{http_code}" "$url" | grep -q "200"; then
        log_info "✓ Successfully fetched $description"
        
        # Validate JSON if it's a JSON file
        if [[ "$output_file" == *.json ]]; then
            if jq . "$output_file" >/dev/null 2>&1; then
                log_debug "✓ JSON validation passed"
            else
                log_warn "⚠ JSON validation failed for $description"
            fi
        fi
        
        return 0
    else
        log_error "✗ Failed to fetch $description"
        return 1
    fi
}

# Collect all available data
collect_all_data() {
    local timestamp_dir="$OUTPUT_DIR/$TIMESTAMP"
    mkdir -p "$timestamp_dir"
    
    log_info "Starting data collection to: $timestamp_dir"
    
    # Main API Server data
    if curl -s "http://${AGENTCELI_HOST}:${MAIN_API_PORT}/api/health" >/dev/null 2>&1; then
        log_info "Collecting from Main API Server..."
        
        fetch_data "http://${AGENTCELI_HOST}:${MAIN_API_PORT}/api/health" \
                  "$timestamp_dir/main_api_health.json" \
                  "Main API health status"
        
        fetch_data "http://${AGENTCELI_HOST}:${MAIN_API_PORT}/api/all" \
                  "$timestamp_dir/complete_dataset.json" \
                  "Complete dataset for correlation analysis"
        
        fetch_data "http://${AGENTCELI_HOST}:${MAIN_API_PORT}/api/prices" \
                  "$timestamp_dir/simplified_prices.json" \
                  "Simplified prices for websites"
        
        fetch_data "http://${AGENTCELI_HOST}:${MAIN_API_PORT}/api/market" \
                  "$timestamp_dir/market_summary.json" \
                  "Market summary for dashboards"
        
        fetch_data "http://${AGENTCELI_HOST}:${MAIN_API_PORT}/api/correlation" \
                  "$timestamp_dir/correlation_data.json" \
                  "Structured correlation analysis data"
        
        fetch_data "http://${AGENTCELI_HOST}:${MAIN_API_PORT}/api/export/csv" \
                  "$timestamp_dir/correlation_data.csv" \
                  "Correlation data CSV export"
    fi
    
    # Public API Server data
    if curl -s "http://${AGENTCELI_HOST}:${PUBLIC_API_PORT}/api/health" >/dev/null 2>&1; then
        log_info "Collecting from Public API Server..."
        
        fetch_data "http://${AGENTCELI_HOST}:${PUBLIC_API_PORT}/api/health" \
                  "$timestamp_dir/public_api_health.json" \
                  "Public API health status"
        
        fetch_data "http://${AGENTCELI_HOST}:${PUBLIC_API_PORT}/api/crypto/latest" \
                  "$timestamp_dir/crypto_latest_full.json" \
                  "Latest crypto data with full market info"
        
        fetch_data "http://${AGENTCELI_HOST}:${PUBLIC_API_PORT}/api/crypto/prices" \
                  "$timestamp_dir/crypto_prices_simple.json" \
                  "Simple crypto price data"
    fi
    
    # Client API Server data
    if curl -s "http://${AGENTCELI_HOST}:${CLIENT_API_PORT}/api/health" >/dev/null 2>&1; then
        log_info "Collecting from Client API Server..."
        
        fetch_data "http://${AGENTCELI_HOST}:${CLIENT_API_PORT}/api/health" \
                  "$timestamp_dir/client_api_health.json" \
                  "Client API health status"
        
        fetch_data "http://${AGENTCELI_HOST}:${CLIENT_API_PORT}/api/clients" \
                  "$timestamp_dir/registered_clients.json" \
                  "List of registered clients"
        
        fetch_data "http://${AGENTCELI_HOST}:${CLIENT_API_PORT}/api/clients/stats" \
                  "$timestamp_dir/client_stats.json" \
                  "Statistics for all clients"
        
        fetch_data "http://${AGENTCELI_HOST}:${CLIENT_API_PORT}/api/data/latest" \
                  "$timestamp_dir/latest_client_data.json" \
                  "Latest data for registered clients"
    fi
    
    # Dashboard Server data
    if curl -s "http://${AGENTCELI_HOST}:${DASHBOARD_PORT}/api/dashboard/status" >/dev/null 2>&1; then
        log_info "Collecting from Dashboard Server..."
        
        fetch_data "http://${AGENTCELI_HOST}:${DASHBOARD_PORT}/api/dashboard/status" \
                  "$timestamp_dir/dashboard_status.json" \
                  "Dashboard system status"
        
        fetch_data "http://${AGENTCELI_HOST}:${DASHBOARD_PORT}/api/dashboard/live-data" \
                  "$timestamp_dir/dashboard_live_data.json" \
                  "Dashboard live crypto data"
        
        fetch_data "http://${AGENTCELI_HOST}:${DASHBOARD_PORT}/api/dashboard/sources" \
                  "$timestamp_dir/data_sources_status.json" \
                  "Data sources status"
        
        fetch_data "http://${AGENTCELI_HOST}:${DASHBOARD_PORT}/api/dashboard/clients" \
                  "$timestamp_dir/dashboard_clients.json" \
                  "Dashboard client information"
    fi
    
    # Create a summary file
    create_collection_summary "$timestamp_dir"
    
    log_info "Data collection completed! Files saved to: $timestamp_dir"
}

# Create a summary of the collected data
create_collection_summary() {
    local timestamp_dir="$1"
    local summary_file="$timestamp_dir/collection_summary.json"
    
    log_info "Creating collection summary..."
    
    cat > "$summary_file" << EOF
{
  "collection_timestamp": "$TIMESTAMP",
  "collection_date": "$(date -Iseconds)",
  "agentceli_host": "$AGENTCELI_HOST",
  "ports": {
    "main_api": $MAIN_API_PORT,
    "public_api": $PUBLIC_API_PORT,
    "client_api": $CLIENT_API_PORT,
    "dashboard": $DASHBOARD_PORT
  },
  "collected_files": [
EOF
    
    # List all collected files
    local first=true
    for file in "$timestamp_dir"/*.json "$timestamp_dir"/*.csv; do
        if [[ -f "$file" ]]; then
            filename=$(basename "$file")
            if [[ "$filename" != "collection_summary.json" ]]; then
                if [[ "$first" == true ]]; then
                    first=false
                else
                    echo "," >> "$summary_file"
                fi
                echo -n "    \"$filename\"" >> "$summary_file"
            fi
        fi
    done
    
    cat >> "$summary_file" << EOF

  ],
  "file_sizes": {
EOF
    
    # Add file sizes
    first=true
    for file in "$timestamp_dir"/*.json "$timestamp_dir"/*.csv; do
        if [[ -f "$file" ]]; then
            filename=$(basename "$file")
            if [[ "$filename" != "collection_summary.json" ]]; then
                size=$(wc -c < "$file" 2>/dev/null || echo "0")
                if [[ "$first" == true ]]; then
                    first=false
                else
                    echo "," >> "$summary_file"
                fi
                echo -n "    \"$filename\": $size" >> "$summary_file"
            fi
        fi
    done
    
    cat >> "$summary_file" << EOF

  }
}
EOF
    
    log_info "Collection summary created: $summary_file"
}

# Collect specific endpoint data
collect_specific() {
    local endpoint="$1"
    local output_name="${2:-$(basename "$endpoint" | tr '/' '_')}"
    local timestamp_dir="$OUTPUT_DIR/$TIMESTAMP"
    mkdir -p "$timestamp_dir"
    
    case "$endpoint" in
        "health"|"all"|"prices"|"market"|"correlation"|"export/csv")
            local url="http://${AGENTCELI_HOST}:${MAIN_API_PORT}/api/$endpoint"
            ;;
        "crypto/latest"|"crypto/prices")
            local url="http://${AGENTCELI_HOST}:${PUBLIC_API_PORT}/api/$endpoint"
            ;;
        "clients"|"clients/stats"|"data/latest")
            local url="http://${AGENTCELI_HOST}:${CLIENT_API_PORT}/api/$endpoint"
            ;;
        "dashboard/status"|"dashboard/live-data"|"dashboard/sources"|"dashboard/clients")
            local url="http://${AGENTCELI_HOST}:${DASHBOARD_PORT}/api/$endpoint"
            ;;
        *)
            log_error "Unknown endpoint: $endpoint"
            show_help
            return 1
            ;;
    esac
    
    local extension="json"
    if [[ "$endpoint" == "export/csv" ]]; then
        extension="csv"
    fi
    
    fetch_data "$url" "$timestamp_dir/${output_name}.${extension}" "Specific endpoint: $endpoint"
}

# Show usage help
show_help() {
    cat << EOF
AgentCeli Data Collector Script

USAGE:
    $0 [OPTIONS] [COMMAND]

COMMANDS:
    all                     Collect all available data from all APIs
    check                   Check status of all AgentCeli services
    specific ENDPOINT       Collect data from a specific endpoint
    
SPECIFIC ENDPOINTS:
    Main API (port $MAIN_API_PORT):
        health              Health check and status
        all                 Complete dataset for correlation analysis
        prices              Simplified prices for websites
        market              Market summary for dashboards
        correlation         Structured correlation analysis data
        export/csv          Download correlation data as CSV
        
    Public API (port $PUBLIC_API_PORT):
        crypto/latest       Latest crypto data with full market info
        crypto/prices       Simple crypto price data
        
    Client API (port $CLIENT_API_PORT):
        clients             List all registered clients
        clients/stats       Statistics for all clients
        data/latest         Latest data for registered clients
        
    Dashboard API (port $DASHBOARD_PORT):
        dashboard/status    Dashboard system status
        dashboard/live-data Dashboard live crypto data
        dashboard/sources   Data sources status
        dashboard/clients   Dashboard client information

OPTIONS:
    -h, --help              Show this help message
    -d, --debug             Enable debug output
    -o, --output DIR        Set output directory (default: ./agentceli_data_collection)
    
ENVIRONMENT VARIABLES:
    AGENTCELI_HOST          AgentCeli server host (default: localhost)
    MAIN_API_PORT           Main API server port (default: 8080)
    PUBLIC_API_PORT         Public API server port (default: 8082)
    CLIENT_API_PORT         Client API server port (default: 8081)
    DASHBOARD_PORT          Dashboard server port (default: 8083)
    OUTPUT_DIR              Output directory (default: ./agentceli_data_collection)
    DEBUG                   Enable debug output (true/false)

EXAMPLES:
    $0 all                                  # Collect all data
    $0 check                                # Check service status
    $0 specific health                      # Get health status
    $0 specific crypto/latest               # Get latest crypto data
    $0 -o /tmp/data specific prices         # Save prices to /tmp/data
    DEBUG=true $0 all                       # Enable debug output

EOF
}

# Main script logic
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -d|--debug)
                DEBUG=true
                shift
                ;;
            -o|--output)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            all)
                create_output_dir
                collect_all_data
                exit 0
                ;;
            check)
                check_services
                exit 0
                ;;
            specific)
                if [[ -z "${2:-}" ]]; then
                    log_error "Endpoint required for 'specific' command"
                    show_help
                    exit 1
                fi
                create_output_dir
                collect_specific "$2" "${3:-}"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # If no command provided, show help
    log_warn "No command provided"
    show_help
    exit 1
}

# Dependency checks
check_dependencies() {
    local missing_deps=()
    
    if ! command -v curl >/dev/null 2>&1; then
        missing_deps+=("curl")
    fi
    
    if ! command -v jq >/dev/null 2>&1; then
        log_warn "jq not found - JSON validation will be skipped"
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_error "Please install the missing dependencies and try again"
        exit 1
    fi
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    log_info "AgentCeli Data Collector Script"
    log_info "================================"
    
    check_dependencies
    main "$@"
fi