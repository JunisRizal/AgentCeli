#!/bin/bash

# ========================================
# 🐙 AgentCeli API Requests for Other Programs
# Complete collection of API calls for external programs
# ========================================

AGENTCELI_URL="http://localhost:8080"
OUTPUT_DIR="./agentceli_api_data"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🐙 AgentCeli API Requests Collection${NC}"
echo -e "${BLUE}====================================${NC}"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo ""
echo -e "${YELLOW}📡 BASIC API REQUESTS:${NC}"
echo "=============================="

echo ""
echo "1️⃣  SIMPLE PRICES (Most Used)"
echo "   curl http://localhost:8080/api/prices"
echo ""
echo "   Returns: BTC, ETH, SOL, XRP prices + Fear & Greed Index"
echo "   Example:"
curl -s http://localhost:8080/api/prices | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'  BTC: \${data[\"btc\"]:,.2f}, ETH: \${data[\"eth\"]:,.2f}, Cost: \${data[\"cost_estimate\"]}')"

echo ""
echo "2️⃣  SYSTEM STATUS"
echo "   curl http://localhost:8080/api/status"
echo ""
echo "   Returns: System health, data source status, cost estimate"
echo "   Example:"
curl -s http://localhost:8080/api/status | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'  Status: {data[\"status\"]}, Cost: \${data[\"cost_estimate\"]}, APIs: {data[\"configuration\"][\"free_apis_active\"]} free')"

echo ""
echo "3️⃣  MARKET OVERVIEW (If Available)"
echo "   curl http://localhost:8080/api/market"
echo ""
echo "   Returns: Complete market data with sentiment"

echo ""
echo "4️⃣  INDIVIDUAL COIN DATA"
echo "   curl http://localhost:8080/api/price/btc"
echo "   curl http://localhost:8080/api/price/eth"
echo "   curl http://localhost:8080/api/price/sol"
echo "   curl http://localhost:8080/api/price/xrp"

echo ""
echo "5️⃣  HEALTH CHECK"
echo "   curl http://localhost:8080/api/health"
echo ""
echo "   Returns: Quick health status"

echo ""
echo -e "${YELLOW}📊 PROGRAMMING LANGUAGE EXAMPLES:${NC}"
echo "=================================="

echo ""
echo "🐍 PYTHON:"
cat << 'EOF'
import requests
import json

# Get live prices
response = requests.get('http://localhost:8080/api/prices')
data = response.json()

print(f"BTC: ${data['btc']:,.2f}")
print(f"ETH: ${data['eth']:,.2f}")
print(f"Fear & Greed: {data['fear_greed']}")
print(f"Cost: ${data['cost_estimate']}")
EOF

echo ""
echo "🟨 JAVASCRIPT/NODE.JS:"
cat << 'EOF'
// Using fetch
const response = await fetch('http://localhost:8080/api/prices');
const data = await response.json();

console.log(`BTC: $${data.btc.toLocaleString()}`);
console.log(`ETH: $${data.eth.toLocaleString()}`);
console.log(`Fear & Greed: ${data.fear_greed}`);

// Using axios
const axios = require('axios');
const { data } = await axios.get('http://localhost:8080/api/prices');
EOF

echo ""
echo "🔷 GO:"
cat << 'EOF'
package main

import (
    "encoding/json"
    "fmt"
    "net/http"
)

type PriceData struct {
    BTC        float64 `json:"btc"`
    ETH        float64 `json:"eth"`
    SOL        float64 `json:"sol"`
    XRP        float64 `json:"xrp"`
    FearGreed  string  `json:"fear_greed"`
    Timestamp  string  `json:"timestamp"`
}

func main() {
    resp, _ := http.Get("http://localhost:8080/api/prices")
    defer resp.Body.Close()
    
    var data PriceData
    json.NewDecoder(resp.Body).Decode(&data)
    
    fmt.Printf("BTC: $%.2f\n", data.BTC)
    fmt.Printf("ETH: $%.2f\n", data.ETH)
}
EOF

echo ""
echo "🦀 RUST:"
cat << 'EOF'
use reqwest;
use serde_json::Value;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let response = reqwest::get("http://localhost:8080/api/prices").await?;
    let data: Value = response.json().await?;
    
    println!("BTC: ${}", data["btc"]);
    println!("ETH: ${}", data["eth"]);
    
    Ok(())
}
EOF

echo ""
echo "☕ JAVA:"
cat << 'EOF'
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import com.fasterxml.jackson.databind.ObjectMapper;

HttpClient client = HttpClient.newHttpClient();
HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create("http://localhost:8080/api/prices"))
    .build();

HttpResponse<String> response = client.send(request, 
    HttpResponse.BodyHandlers.ofString());

ObjectMapper mapper = new ObjectMapper();
JsonNode data = mapper.readTree(response.body());

System.out.println("BTC: $" + data.get("btc").asDouble());
EOF

echo ""
echo -e "${YELLOW}🔄 AUTOMATION EXAMPLES:${NC}"
echo "======================="

echo ""
echo "📅 CRON JOB (Every 5 minutes):"
echo "*/5 * * * * curl -s http://localhost:8080/api/prices > /tmp/crypto_prices.json"

echo ""
echo "🔁 CONTINUOUS MONITORING:"
cat << 'EOF'
#!/bin/bash
while true; do
    curl -s http://localhost:8080/api/prices | jq '.btc' > btc_price.txt
    sleep 60
done
EOF

echo ""
echo "📊 DATA COLLECTION SCRIPT:"
cat << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
curl -s http://localhost:8080/api/prices > "crypto_data_${TIMESTAMP}.json"
curl -s http://localhost:8080/api/status > "status_${TIMESTAMP}.json"
EOF

echo ""
echo -e "${YELLOW}📁 FILE-BASED ACCESS:${NC}"
echo "====================="

echo ""
echo "🗂️  DIRECT FILE READING:"
echo "   Latest JSON: /Users/julius/Desktop/AgentCeli/correlation_data/hybrid_latest.json"
echo "   Latest CSV:  /Users/julius/Desktop/AgentCeli/correlation_data/hybrid_latest.csv"
echo "   Current:     /Users/julius/Desktop/AgentCeli/agentceli_data/agentceli_current.json"

echo ""
echo "📖 FILE READING EXAMPLES:"
echo ""
echo "Python:"
echo "   with open('/Users/julius/Desktop/AgentCeli/correlation_data/hybrid_latest.json') as f:"
echo "       data = json.load(f)"

echo ""
echo "Bash:"
echo "   cat /Users/julius/Desktop/AgentCeli/correlation_data/hybrid_latest.json | jq '.sources.binance.BTCUSDT.price'"

echo ""
echo -e "${YELLOW}🧪 TESTING COMMANDS:${NC}"
echo "==================="

echo ""
echo "✅ Test API Connection:"
echo "curl -I http://localhost:8080/api/prices"

echo ""
echo "⏱️  Response Time Test:"
echo "time curl -s http://localhost:8080/api/prices > /dev/null"

echo ""
echo "🔍 Pretty Print JSON:"
echo "curl -s http://localhost:8080/api/prices | python3 -m json.tool"

echo ""
echo "📊 Quick Stats:"
echo "curl -s http://localhost:8080/api/prices | jq '{btc: .btc, cost: .cost_estimate, timestamp: .timestamp}'"

echo ""
echo -e "${YELLOW}🚨 ERROR HANDLING:${NC}"
echo "=================="

echo ""
echo "🐍 Python with Error Handling:"
cat << 'EOF'
import requests
import json

try:
    response = requests.get('http://localhost:8080/api/prices', timeout=10)
    response.raise_for_status()
    data = response.json()
    
    if 'btc' in data:
        print(f"BTC: ${data['btc']:,.2f}")
    else:
        print("No BTC data available")
        
except requests.exceptions.RequestException as e:
    print(f"API Error: {e}")
    # Fallback to file access
    try:
        with open('/Users/julius/Desktop/AgentCeli/correlation_data/hybrid_latest.json') as f:
            data = json.load(f)
            btc_price = data['sources']['binance']['BTCUSDT']['price']
            print(f"BTC (from file): ${btc_price:,.2f}")
    except Exception as file_error:
        print(f"File access also failed: {file_error}")
EOF

echo ""
echo "🔧 Bash with Fallback:"
cat << 'EOF'
#!/bin/bash
API_DATA=$(curl -s --max-time 10 http://localhost:8080/api/prices)
if [ $? -eq 0 ] && echo "$API_DATA" | jq -e '.btc' > /dev/null 2>&1; then
    echo "API Success: $API_DATA"
else
    echo "API failed, using file..."
    cat /Users/julius/Desktop/AgentCeli/correlation_data/hybrid_latest.json
fi
EOF

echo ""
echo -e "${GREEN}✅ READY TO USE!${NC}"
echo "================"
echo "All API endpoints are ready for your programs to use."
echo "Cost: \$0.00 (100% free APIs)"
echo ""
echo "Current API Status:"
curl -s http://localhost:8080/api/status | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Status: {data[\"status\"]}, Free APIs: {data[\"configuration\"][\"free_apis_active\"]}, Cost: \${data[\"cost_estimate\"]}')"

echo ""
echo "Current Prices:"
curl -s http://localhost:8080/api/prices | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'BTC: \${data[\"btc\"]:,.2f}, ETH: \${data[\"eth\"]:,.2f}, SOL: \${data[\"sol\"]:,.2f}, XRP: \${data[\"xrp\"]:.4f}')"