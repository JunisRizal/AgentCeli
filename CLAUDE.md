# AgentCeli - Crypto Data Intelligence Platform

## 🔥 LIQUIDATION DATA CAPABILITIES

**Real-time Liquidation Analysis (4 Symbols):**
- **BTC**: 8.4/100 Risk (LOW) - $118,400 (+0.58%)
- **ETH**: 7.8/100 Risk (LOW) - $3,796 (+0.69%)  
- **XRP**: 47.5/100 Risk (HIGH) - $3.14 (+1.03%)
- **SOL**: 3.8/100 Risk (LOW) - $179 (-0.71%)

**Risk Scoring System:**
- 0-20: LOW (🟢) - Stabile Bedingungen
- 20-40: MEDIUM (🟡) - Normale Marktrisiken  
- 40-60: HIGH (🟠) - Erhöhte Liquidation-Gefahr
- 60+: EXTREME (🔴) - Sehr hohe Liquidation-Wahrscheinlichkeit

**Data Sources:**
- Binance Free API (Preise, Volumen, 24h Änderungen)
- Fear & Greed Index (aktuell: 74 = Greed)
- Whale Movement Data (7d/24h Nettoflüsse)
- Volatilitäts-Komponenten
- Liquidation-Zonen (5x/10x Long/Short Berechnung)

## 📊 DATA COLLECTION INFRASTRUCTURE

**Live Data Files:**
- `correlation_data/hybrid_latest.json` - Multi-source price data
- `correlation_data/hybrid_latest.csv` - CSV export for analysis
- `liquidation_data/liquidation_analysis_latest.json` - Risk analysis
- `liquidation_data/enhanced_liquidation_heatmap_latest.json` - Detailed explanations

**Analysis Tools:**
- `liquidation_analyzer.py` - Pure data analysis (no visualization)
- `agentceli_hybrid.py` - Multi-source data collector
- `data_source_expansion.py` - API source management

## 🌐 SANTIMENT.NET ENDPOINTS (46 Files)

**Available Santiment Data Sources:**
- **AI Social Sentiment**: `santiment_ai_social_monitor.py`
- **Exchange Flows**: `santiment_exchange_flows.py` 
- **Whale Alerts**: `santiment_whale_alerts.py`
- **Multi-Asset Flows**: `santiment_data/` directory
- **Historical Data**: Various endpoint-specific files

**Santiment Data Types:**
- Exchange In/Outflows (real-time)
- Whale Transaction Alerts (>$100k moves)
- Social Sentiment AI Analysis
- Network Activity Metrics
- Development Activity Tracking

## 🚀 ACTIVE MONITORING SYSTEMS

**Watchdog Services:**
- `agentceli_watchdog.py` - System health monitoring
- `api_usage_monitor.py` - API rate limit tracking
- `datasource_monitor_dashboard.py` - Data source status

**Dashboard Interfaces:**
- `dashboard_working.py` - Main data visualization
- `simple_dashboard.py` - Lightweight version
- `datasource_monitor_dashboard.py` - Source monitoring

## 📈 DATA UPDATE FREQUENCIES

- **Price Data**: Every 10-15 minutes
- **Liquidation Risk**: Every 10-15 minutes  
- **Fear & Greed**: Every hour
- **Whale Data**: Real-time when available
- **Santiment Metrics**: Varies by endpoint

## 🛠️ QUICK START COMMANDS

**Start Data Collection:**
```bash
python agentceli_hybrid.py
```

**Run Liquidation Analysis:**
```bash
python liquidation_analyzer.py
```

**Launch Dashboard:**
```bash
python dashboard_working.py
```

**Monitor System Health:**
```bash
python agentceli_watchdog.py
```

## 🔍 SEARCH HELPERS

**Find Liquidation Data:**
- Look in `liquidation_data/` directory
- Current analysis: `liquidation_analysis_latest.json`
- Historical: Multiple timestamped files

**Find Santiment Data:**
- Main directory: `santiment_data/`
- Scripts: Files starting with `santiment_`
- Logs: `logs/santiment.log`

**Find Price Data:**
- Current: `correlation_data/hybrid_latest.json`
- Database: `correlation_data/hybrid_crypto_data.db`
- CSV: `correlation_data/hybrid_latest.csv`

## ⚡ CURRENT SYSTEM STATUS

- **APIs Active**: 4 free sources (Binance, CoinGecko, Fear&Greed, Alternative.me)
- **Paid APIs**: 0 (cost optimization mode)
- **Data Quality**: HIGH (multi-source verification)
- **Update Status**: Real-time collection active
- **Risk Analysis**: Fully operational
- **Dashboard**: Working with live data

## 💡 NEXT DEVELOPMENT PRIORITIES

1. **Santiment Pro Integration** - Add paid API for advanced whale data
2. **Real-time Alerts** - Push notifications for high-risk conditions
3. **Portfolio Integration** - Connect to user trading accounts
4. **Historical Backtesting** - Test liquidation predictions
5. **Mobile Dashboard** - Responsive interface for mobile devices

---
*Last Updated: 2025-07-30 17:19 - Auto-updating system active*