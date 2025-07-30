#!/usr/bin/env python3
"""
AgentCeli Data Source Monitoring Dashboard
Real-time monitoring of data sources, API costs, and request rates
"""

from flask import Flask, render_template, jsonify, send_from_directory
import json
import time
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import threading
from collections import defaultdict, deque
import os

# Avoid local requests.py conflict
import sys
if "/Users/julius/Desktop/AgentCeli" in sys.path:
    sys.path.remove("/Users/julius/Desktop/AgentCeli")
import requests as http_requests

app = Flask(__name__)

class DataSourceMonitor:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.config_file = self.base_dir / "agentceli_config.json"
        self.db_file = self.base_dir / "monitoring.db"
        
        # Request tracking
        self.request_counts = defaultdict(int)
        self.request_history = defaultdict(lambda: deque(maxlen=100))
        self.cost_tracking = defaultdict(float)
        self.last_update = {}
        
        # API Cost alerts
        self.cost_alerts = []
        self.ai_api_usage = {
            "openai": {"requests": 0, "cost": 0.0, "last_used": None},
            "anthropic": {"requests": 0, "cost": 0.0, "last_used": None}
        }
        
        self.setup_database()
        self.load_config()
        
    def setup_database(self):
        """Setup SQLite database for monitoring"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                endpoint TEXT,
                response_time REAL,
                status_code INTEGER,
                cost REAL DEFAULT 0.0,
                request_type TEXT DEFAULT 'data'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cost_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT NOT NULL,
                source TEXT NOT NULL,
                cost REAL,
                message TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def load_config(self):
        """Load AgentCeli configuration"""
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except:
            self.config = {}
    
    def log_request(self, source, endpoint="", response_time=0, status_code=200, cost=0.0, request_type="data"):
        """Log API request to database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO api_requests (source, endpoint, response_time, status_code, cost, request_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (source, endpoint, response_time, status_code, cost, request_type))
        
        conn.commit()
        conn.close()
        
        # Update in-memory tracking
        self.request_counts[source] += 1
        self.request_history[source].append({
            "timestamp": datetime.now().isoformat(),
            "response_time": response_time,
            "status_code": status_code,
            "cost": cost
        })
        
        self.cost_tracking[source] += cost
        
        # Check for AI API usage
        if "openai" in source.lower() or "gpt" in source.lower():
            self.ai_api_usage["openai"]["requests"] += 1
            self.ai_api_usage["openai"]["cost"] += cost
            self.ai_api_usage["openai"]["last_used"] = datetime.now().isoformat()
            self.create_cost_alert("AI_API_USAGE", source, cost, f"OpenAI API used: ${cost:.4f}")
            
        elif "anthropic" in source.lower() or "claude" in source.lower():
            self.ai_api_usage["anthropic"]["requests"] += 1
            self.ai_api_usage["anthropic"]["cost"] += cost
            self.ai_api_usage["anthropic"]["last_used"] = datetime.now().isoformat()
            self.create_cost_alert("AI_API_USAGE", source, cost, f"Anthropic API used: ${cost:.4f}")
    
    def create_cost_alert(self, alert_type, source, cost, message):
        """Create cost alert"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "source": source,
            "cost": cost,
            "message": message,
            "severity": "HIGH" if cost > 0.10 else "MEDIUM" if cost > 0.01 else "LOW"
        }
        
        self.cost_alerts.append(alert)
        
        # Keep only last 50 alerts
        if len(self.cost_alerts) > 50:
            self.cost_alerts = self.cost_alerts[-50:]
        
        # Log to database
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cost_alerts (alert_type, source, cost, message)
            VALUES (?, ?, ?, ?)
        ''', (alert_type, source, cost, message))
        conn.commit()
        conn.close()
    
    def get_data_source_status(self):
        """Get current status of all data sources"""
        sources = {}
        
        # Free APIs from config
        if "data_sources" in self.config and "free_apis" in self.config["data_sources"]:
            for name, config in self.config["data_sources"]["free_apis"].items():
                sources[name] = {
                    "type": "FREE",
                    "enabled": config.get("enabled", False),
                    "priority": config.get("priority", "medium"),
                    "requests_today": self.get_requests_today(name),
                    "avg_response_time": self.get_avg_response_time(name),
                    "cost_today": 0.0,
                    "last_request": self.get_last_request_time(name),
                    "status": "active" if config.get("enabled", False) else "disabled",
                    "data_types": self.get_data_types(name)
                }
        
        # Paid APIs from config
        if "data_sources" in self.config and "paid_apis" in self.config["data_sources"]:
            for name, config in self.config["data_sources"]["paid_apis"].items():
                sources[name] = {
                    "type": "PAID",
                    "enabled": config.get("enabled", False),
                    "cost_per_call": config.get("cost_per_call", 0.0),
                    "requests_today": self.get_requests_today(name),
                    "avg_response_time": self.get_avg_response_time(name),
                    "cost_today": self.cost_tracking.get(name, 0.0),
                    "last_request": self.get_last_request_time(name),
                    "status": "active" if config.get("enabled", False) else "disabled",
                    "data_types": self.get_data_types(name)
                }
        
        # Add Santiment specifically
        if "santiment" not in sources:
            sources["santiment"] = {
                "type": "PAID",
                "enabled": True,
                "cost_per_call": 0.02,
                "requests_today": self.get_requests_today("santiment"),
                "avg_response_time": self.get_avg_response_time("santiment"),
                "cost_today": self.cost_tracking.get("santiment", 0.0),
                "last_request": self.get_last_request_time("santiment"),
                "status": "active",
                "data_types": ["whale_transactions", "exchange_flows", "sentiment"]
            }
        
        return sources
    
    def get_data_types(self, source):
        """Get detailed data types collected by source - ONLY sources AgentCeli actually uses"""
        type_mapping = {
            "binance": [
                "real_time_prices", "trading_volumes", "24h_price_changes", 
                "bid_ask_spreads", "market_depth", "ticker_data"
            ],
            "coinbase": [
                "spot_prices", "trading_volumes", "market_data",
                "order_book", "trade_executions", "market_stats"
            ],
            "coingecko": [
                "current_prices", "market_capitalizations", "total_volumes",
                "price_change_percentages", "market_rank", "circulating_supply",
                "total_supply", "all_time_high", "all_time_low"
            ],
            "fear_greed": [
                "fear_greed_index", "market_sentiment_score", 
                "sentiment_classification", "historical_sentiment"
            ],
            "santiment": [
                "whale_transaction_count_1m_usd_to_inf", "exchange_inflow",
                "exchange_outflow", "sentiment_balance_total"
            ]
        }
        return type_mapping.get(source, ["data_collection"])
    
    def get_requests_today(self, source):
        """Get request count for today"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute('''
            SELECT COUNT(*) FROM api_requests 
            WHERE source = ? AND DATE(timestamp) = ?
        ''', (source, today))
        
        result = cursor.fetchone()[0]
        conn.close()
        return result
    
    def get_avg_response_time(self, source):
        """Get average response time for source"""
        if source in self.request_history and self.request_history[source]:
            recent_requests = list(self.request_history[source])[-10:]  # Last 10 requests
            if recent_requests:
                avg_time = sum([r["response_time"] for r in recent_requests]) / len(recent_requests)
                return round(avg_time, 3)
        return 0.0
    
    def get_last_request_time(self, source):
        """Get last request timestamp"""
        if source in self.request_history and self.request_history[source]:
            return list(self.request_history[source])[-1]["timestamp"]
        return None
    
    def get_request_rate_data(self):
        """Get request rate data for charts"""
        rate_data = {}
        
        for source in self.request_history:
            if self.request_history[source]:
                # Group by minute for the last hour
                minute_counts = defaultdict(int)
                now = datetime.now()
                
                for request in self.request_history[source]:
                    req_time = datetime.fromisoformat(request["timestamp"])
                    if (now - req_time).total_seconds() <= 3600:  # Last hour
                        minute_key = req_time.strftime("%H:%M")
                        minute_counts[minute_key] += 1
                
                rate_data[source] = dict(minute_counts)
        
        return rate_data

# Global monitor instance
monitor = DataSourceMonitor()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('datasource_monitor.html')

@app.route('/api/sources/status')
def get_sources_status():
    """Get current status of all data sources"""
    return jsonify(monitor.get_data_source_status())

@app.route('/api/costs/alerts')
def get_cost_alerts():
    """Get cost alerts"""
    return jsonify({
        "alerts": monitor.cost_alerts[-20:],  # Last 20 alerts
        "ai_usage": monitor.ai_api_usage,
        "total_cost_today": sum(monitor.cost_tracking.values())
    })

@app.route('/api/requests/rates')
def get_request_rates():
    """Get request rate data"""
    return jsonify(monitor.get_request_rate_data())

@app.route('/api/sources/detailed')
def get_detailed_sources():
    """Get detailed information about ACTUAL data sources AgentCeli uses"""
    # Only show sources that are actually configured and used by AgentCeli
    detailed_sources = {
        "binance": {
            "name": "Binance Exchange",
            "type": "FREE",
            "description": "World's largest crypto exchange - AgentCeli's primary price source",
            "rate_limit": "1200 requests/minute",
            "data_categories": {
                "Market Data": ["real_time_prices", "trading_volumes", "24h_price_changes"],
                "Trading Info": ["bid_ask_spreads", "market_depth", "ticker_data"],
                "Historical": ["OHLCV_data", "trade_history"]
            },
            "assets_supported": ["BTC", "ETH", "SOL", "XRP", "ADA", "DOT", "LINK"]
        },
        "coinbase": {
            "name": "Coinbase Pro API",
            "type": "FREE", 
            "description": "Major US exchange - AgentCeli backup price source",
            "rate_limit": "10 requests/second",
            "data_categories": {
                "Market Data": ["spot_prices", "trading_volumes", "market_data"],
                "Trading Info": ["order_book", "trade_executions", "market_stats"],
                "Exchange Data": ["currency_pairs", "fee_schedules"]
            },
            "assets_supported": ["BTC", "ETH", "SOL", "XRP", "Major altcoins"]
        },
        "coingecko": {
            "name": "CoinGecko API",
            "type": "FREE",
            "description": "Comprehensive market data - AgentCeli's market cap source",
            "rate_limit": "50 requests/minute (free tier)",
            "data_categories": {
                "Price Data": ["current_prices", "price_change_percentages", "all_time_high", "all_time_low"],
                "Market Info": ["market_capitalizations", "total_volumes", "market_rank"],
                "Supply Data": ["circulating_supply", "total_supply"],
                "Community": ["developer_data", "community_data"]
            },
            "assets_supported": ["BTC", "ETH", "SOL", "XRP", "10,000+ others"]
        },
        "fear_greed": {
            "name": "Fear & Greed Index",
            "type": "FREE",
            "description": "Market sentiment indicator - AgentCeli's sentiment source",
            "rate_limit": "Unlimited",
            "data_categories": {
                "Sentiment": ["fear_greed_index", "market_sentiment_score"],
                "Classification": ["sentiment_classification", "historical_sentiment"],
                "Market Impact": ["volatility_impact", "market_momentum"]
            },
            "assets_supported": ["Overall crypto market sentiment"]
        },
        "santiment": {
            "name": "Santiment Network",
            "type": "PAID",
            "description": "On-chain whale data - AgentCeli's premium data source",
            "rate_limit": "Based on API key subscription",
            "cost_per_call": "$0.02",
            "data_categories": {
                "Whale Activity": ["whale_transaction_count_1m_usd_to_inf", "large_transactions"],
                "Exchange Flows": ["exchange_inflow", "exchange_outflow"],
                "Social Data": ["sentiment_balance_total", "social_sentiment"],
                "Network Metrics": ["network_activity", "dev_activity"]
            },
            "assets_supported": ["BTC", "ETH", "SOL", "XRP", "1000+ ERC-20 tokens"]
        }
    }
    
    return jsonify(detailed_sources)

@app.route('/api/simulate/request/<source>')
def simulate_request(source):
    """Simulate API request for testing"""
    import random
    
    # Simulate request
    response_time = random.uniform(0.1, 2.0)
    status_code = random.choice([200, 200, 200, 429, 500])  # Mostly 200
    cost = 0.0
    
    # Add cost for paid APIs
    if source in ["santiment", "coinglass", "taapi"]:
        cost = random.uniform(0.01, 0.05)
    elif source in ["openai", "anthropic"]:
        cost = random.uniform(0.002, 0.02)
    
    monitor.log_request(source, f"/api/{source}/data", response_time, status_code, cost)
    
    return jsonify({
        "success": True,
        "simulated": True,
        "source": source,
        "response_time": response_time,
        "status_code": status_code,
        "cost": cost
    })

# === SANTIMENT DATA ENDPOINTS ===

@app.route('/api/santiment/data')
def get_santiment_data():
    """Get latest Santiment multi-asset flow data"""
    try:
        santiment_file = monitor.base_dir / "santiment_data" / "multi_asset_flows_latest.json"
        
        if santiment_file.exists():
            with open(santiment_file, 'r') as f:
                data = json.load(f)
                return jsonify(data)
        else:
            return jsonify({"error": "No Santiment data available"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/santiment/ai-social')
def get_ai_social_data():
    """Get latest AI social volume data"""
    try:
        ai_social_file = monitor.base_dir / "santiment_data" / "ai_social_latest.json"
        
        if ai_social_file.exists():
            with open(ai_social_file, 'r') as f:
                data = json.load(f)
                return jsonify(data)
        else:
            return jsonify({"error": "No AI social data available"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/santiment_data/<filename>')
def serve_santiment_data(filename):
    """Serve Santiment data files directly"""
    try:
        santiment_dir = monitor.base_dir / "santiment_data"
        return send_from_directory(santiment_dir, filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route('/api/santiment/summary')
def get_santiment_summary():
    """Get Santiment data summary for dashboard"""
    try:
        santiment_file = monitor.base_dir / "santiment_data" / "multi_asset_flows_latest.json"
        
        if not santiment_file.exists():
            return jsonify({"error": "No Santiment data available"}), 404
        
        with open(santiment_file, 'r') as f:
            data = json.load(f)
        
        # Create summary
        summary = {
            "timestamp": data.get("timestamp"),
            "data_source": "santiment",
            "cost_estimate": data.get("cost_estimate", 0.02),
            "date_range": data.get("date_range", {}),
            "assets_summary": {}
        }
        
        # Process asset summaries
        for asset, asset_data in data.get("assets", {}).items():
            inflow_count = len(asset_data.get("inflows", []))
            outflow_count = len(asset_data.get("outflows", []))
            sentiment_count = len(asset_data.get("sentiment", []))
            
            # Calculate latest values
            latest_inflow = 0
            latest_outflow = 0
            latest_sentiment = 0
            
            if asset_data.get("inflows"):
                latest_inflow = asset_data["inflows"][-1].get("value", 0) or 0
            if asset_data.get("outflows"):
                latest_outflow = asset_data["outflows"][-1].get("value", 0) or 0
            if asset_data.get("sentiment"):
                latest_sentiment = asset_data["sentiment"][-1].get("value", 0) or 0
            
            net_flow = latest_inflow - latest_outflow
            
            # Count social metrics
            social_metrics_count = 0
            if asset_data.get("social"):
                for platform, platform_data in asset_data["social"].items():
                    if platform_data:
                        social_metrics_count += 1
            
            summary["assets_summary"][asset] = {
                "data_points": {
                    "inflows": inflow_count,
                    "outflows": outflow_count,
                    "sentiment": sentiment_count,
                    "social_metrics": social_metrics_count
                },
                "latest_values": {
                    "inflow": latest_inflow,
                    "outflow": latest_outflow,
                    "net_flow": net_flow,
                    "sentiment": latest_sentiment
                },
                "status": "active" if inflow_count > 0 or outflow_count > 0 else "no_data"
            }
        
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/correlation/data')
def get_correlation_data():
    """Get latest correlation/price data"""
    try:
        correlation_file = monitor.base_dir / "correlation_data" / "hybrid_latest.json"
        
        if correlation_file.exists():
            with open(correlation_file, 'r') as f:
                data = json.load(f)
                return jsonify(data)
        else:
            return jsonify({"error": "No correlation data available"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/integrated/dashboard')
def get_integrated_dashboard_data():
    """Get all integrated data for dashboard charts"""
    try:
        # Load Santiment data
        santiment_data = None
        santiment_file = monitor.base_dir / "santiment_data" / "multi_asset_flows_latest.json"
        if santiment_file.exists():
            with open(santiment_file, 'r') as f:
                santiment_data = json.load(f)
        
        # Load correlation/price data
        correlation_data = None
        correlation_file = monitor.base_dir / "correlation_data" / "hybrid_latest.json"
        if correlation_file.exists():
            with open(correlation_file, 'r') as f:
                correlation_data = json.load(f)
        
        return jsonify({
            "santiment": santiment_data,
            "correlation": correlation_data,
            "timestamp": datetime.now().isoformat(),
            "data_sources_available": {
                "santiment": santiment_data is not None,
                "correlation": correlation_data is not None
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🖥️  Starting AgentCeli Data Source Monitor Dashboard...")
    print("📊 Dashboard available at: http://localhost:8090")
    print("🔍 Features:")
    print("  - Real-time data source monitoring")
    print("  - API cost tracking and alerts")
    print("  - Request rate monitoring")
    print("  - AI API usage warnings (OpenAI/Anthropic)")
    print("  - Enhanced data source details with categories")
    print("  - 📈 Santiment Exchange Flow Charts (BTC, ETH, SOL, XRP)")
    print("  - 🧠 Social Volume & Sentiment Visualization")
    print("  - 💰 Interactive asset selection and metrics")
    print("  - 📊 Chart.js powered visualizations")
    
    app.run(host='127.0.0.1', port=8090, debug=False)