# 🐙 AgentCeli - Comprehensive Cryptocurrency Data Collection & Analysis

**Real-time crypto data collection, liquidation heatmaps, and market intelligence**

## 🚀 Quick Start

```bash
# One-click startup (Recommended)
./AgentCeli_Starter_Package.sh

# Or start individual components
python3 agentceli_hybrid.py                    # Core data collection
python3 agentceli_master_dashboard.py          # Main dashboard  
python3 enhanced_liquidation_heatmap.py        # Liquidation analysis
```

## 📊 What is AgentCeli?

AgentCeli is a comprehensive cryptocurrency market intelligence system that provides:

- **Real-time price monitoring** from multiple exchanges
- **Liquidation heatmap analysis** with risk assessment
- **Whale movement tracking** via Santiment Pro
- **Market sentiment correlation** with Fear & Greed Index
- **Multi-source data aggregation** for reliable analysis

## 🌐 Web Interfaces

| Service | Port | Description |
|---------|------|-------------|
| **Master Dashboard** | 8081 | Main control panel with service management |
| **Liquidation Heatmap** | 8086 | Enhanced risk analysis and visualization |
| **Core API** | 8080 | Raw data API endpoints |

## 🔧 System Architecture

```
AgentCeli Core (agentceli_hybrid.py)
├── 🆓 Free APIs: Binance, CoinGecko, Fear & Greed
├── 💰 Paid APIs: Santiment Pro, CoinGlass, TAAPI
├── 📊 Data Output: JSON, CSV, SQLite
└── 🌐 HTTP API: Real-time endpoints

Master Dashboard (agentceli_master_dashboard.py)
├── 🎛️ Service Management: Start/stop components
├── 📈 Real-time Monitoring: Live data display
├── ⚙️ Data Source Controls: Enable/disable APIs
└── 📊 Status Overview: System health monitoring

Liquidation Heatmap (enhanced_liquidation_heatmap.py)
├── 🔥 Risk Analysis: Multi-source liquidation risk
├── 🌊 Volatility Tracking: Price movement analysis
├── 🐋 Whale Correlation: Large transaction impact
└── 😨 Sentiment Integration: Fear & Greed multiplier

Santiment Monitoring
├── 🐋 Whale Alerts: Large transaction detection
├── 💱 Exchange Flows: In/outflow analysis
├── 🤖 AI Social Sentiment: Social volume tracking
└── 📈 Multi-Asset Flows: Cross-asset analysis
```

## 📁 Data Sources

### 🆓 Free APIs (Always Available)
- **Binance**: Real-time prices for BTC, ETH, SOL, XRP
- **CoinGecko**: Market cap and 24h change data
- **Fear & Greed Index**: Market sentiment indicator
- **Alternative.me**: Cryptocurrency market sentiment

### 💰 Paid APIs (Optional)
- **Santiment Pro**: On-chain data, whale alerts, social sentiment
- **CoinGlass**: Liquidation data, futures metrics
- **TAAPI**: Technical analysis indicators

## 🔧 Configuration

Edit `agentceli_config.json` to configure data sources:

```json
{
  "data_sources": {
    "free_apis": {
      "binance": {"enabled": true, "priority": "high"},
      "coingecko": {"enabled": true, "priority": "high"},
      "fear_greed": {"enabled": true, "priority": "medium"}
    },
    "paid_apis": {
      "santiment": {
        "enabled": true,
        "key": "your_santiment_api_key",
        "cost_per_call": 0.02
      }
    }
  },
  "update_intervals": {"fast_data": 300},
  "rate_limits": {"daily_cost_limit": 5.0}
}
```

## 📊 Data Output Files

| File | Description | Update Frequency |
|------|-------------|------------------|
| `correlation_data/hybrid_latest.json` | Latest market data | 5 minutes |
| `correlation_data/hybrid_latest.csv` | CSV format for analysis | 5 minutes |
| `correlation_data/hybrid_crypto_data.db` | SQLite database | 5 minutes |
| `santiment_data/*_latest.json` | Santiment whale/flow data | 15 minutes |
| `liquidation_data/*_latest.json` | Liquidation risk analysis | 5 minutes |

## 🔥 Liquidation Heatmap Features

The Enhanced Liquidation Heatmap provides:

### 📈 Risk Analysis Components
- **Volatility Score**: Based on 24h price changes
- **Volume Impact**: High volume amplifies risk
- **Whale Flow Correlation**: Large transactions affecting price
- **Fear & Greed Multiplier**: Market sentiment impact

### 🎯 Risk Levels
- **🟢 LOW (0-40)**: Stable conditions
- **🟡 MEDIUM (40-60)**: Moderate risk
- **🟠 HIGH (60-80)**: Elevated risk
- **🔴 EXTREME (80+)**: Critical liquidation risk

### 📊 Estimated Liquidation Zones
- Support/resistance levels based on risk analysis
- Leverage-adjusted price targets
- Dynamic risk-based zone calculation

## 🐋 Santiment Pro Integration

### Available Data Streams
- **Whale Alerts**: Transactions > $1M
- **Exchange Flows**: In/outflow analysis for BTC, ETH, SOL, XRP
- **AI Social Sentiment**: Social volume and sentiment tracking
- **Multi-Asset Analysis**: Cross-correlation analysis

### Setup Instructions
1. Get Santiment Pro API key from [sanbase.net](https://sanbase.net)
2. Add key to `agentceli_config.json`
3. Enable Santiment in configuration
4. Restart AgentCeli core

## 📱 API Endpoints

### Core Data API (Port 8080)
```
GET /api/status          # System status
GET /api/prices          # Latest price data
```

### Master Dashboard API (Port 8081)
```
GET /api/services        # Service status
GET /api/data/latest     # Latest collected data
POST /api/service/start  # Start service
POST /api/service/stop   # Stop service
```

### Liquidation Heatmap API (Port 8086)
```
GET /api/liquidation/enhanced  # Enhanced risk analysis
GET /api/liquidation/status    # Heatmap status
```

## 🔧 Advanced Usage

### Running Multiple Instances
```bash
# Start core collector in background
python3 agentceli_hybrid.py &

# Start dashboard
python3 agentceli_master_dashboard.py &

# Start liquidation heatmap
python3 enhanced_liquidation_heatmap.py &
```

### Custom Data Analysis
```python
# Load AgentCeli data in Python
import json
with open('correlation_data/hybrid_latest.json', 'r') as f:
    data = json.load(f)

# Access price data
btc_price = data['sources']['binance']['BTCUSDT']['price']
fear_greed = data['fear_greed']['value']
```

### Database Integration
```python
import sqlite3
conn = sqlite3.connect('correlation_data/hybrid_crypto_data.db')
cursor = conn.cursor()

# Query price history
cursor.execute("SELECT * FROM live_prices WHERE symbol = 'BTC' ORDER BY timestamp DESC LIMIT 10")
recent_btc = cursor.fetchall()
```

## 🛠️ Troubleshooting

### Common Issues

**Configuration not loading:**
```bash
# Check config file
cat agentceli_config.json
# Restart with clean config
python3 agentceli_hybrid.py
```

**Santiment data missing:**
```bash
# Check API key
grep "santiment" agentceli_config.json
# Check data directory
ls -la santiment_data/
```

**Dashboard not showing data:**
```bash
# Verify core is running
curl http://localhost:8080/api/status
# Check data file
ls -la correlation_data/hybrid_latest.json
```

### Log Files
- `logs/agentceli.log`: Core system logs
- `logs/dashboard.log`: Dashboard activity
- `logs/santiment.log`: Santiment data collection
- `logs/watchdog.log`: System monitoring

## 📈 Performance Optimization

### Cost Management
- Use free APIs for basic monitoring
- Enable paid APIs only when needed
- Set daily cost limits in configuration
- Monitor API usage in dashboard

### Rate Limiting
- Built-in rate limiting for all APIs
- Automatic retry with backoff
- Error handling and recovery
- Usage monitoring and alerts

## 🔐 Security Features

- No API keys stored in code
- Configuration file encryption support
- Request authentication for paid APIs
- Secure session management
- Input validation and sanitization

## 📚 Integration Examples

### TradingView Integration
```javascript
// Use AgentCeli data in TradingView
fetch('http://localhost:8080/api/prices')
  .then(response => response.json())
  .then(data => {
    // Use BTC price: data.btc
    // Use Fear & Greed: data.fear_greed
  });
```

### Discord Bot Integration
```python
# Send liquidation alerts to Discord
import requests
liquidation_data = requests.get('http://localhost:8086/api/liquidation/enhanced').json()
high_risk_assets = [asset for asset, data in liquidation_data['liquidation_heatmap'].items() 
                   if data['risk_class'] == 'EXTREME']
```

## 🚀 Deployment

### Local Development
```bash
./AgentCeli_Starter_Package.sh
```

### Production Server
```bash
# Install as service
sudo cp AgentCeli_Starter_Package.sh /usr/local/bin/
sudo systemctl create agentceli.service
```

### Docker Container
```dockerfile
FROM python:3.9
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python3", "agentceli_hybrid.py"]
```

## 📞 Support

- **Documentation**: This README
- **Configuration**: `agentceli_config.json`
- **Logs**: `logs/` directory
- **Status**: Master Dashboard (http://localhost:8081)

## 🎯 Roadmap

- [ ] Machine learning price prediction
- [ ] Advanced technical indicators
- [ ] Multi-exchange arbitrage detection
- [ ] DeFi protocol integration
- [ ] Mobile app interface
- [ ] Real-time notifications
- [ ] Portfolio tracking
- [ ] Risk management tools

---

**🐙 AgentCeli - Your Cryptocurrency Intelligence Hub**

*Real-time data collection, advanced analysis, and intelligent market monitoring*