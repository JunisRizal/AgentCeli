#!/usr/bin/env python3
"""
AgentCeli Simple Dashboard - Clean & Minimal
Just the essentials: 4 coins, whale data, clean white design
"""

from flask import Flask, jsonify, render_template_string
import json
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

class SimpleDataLoader:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        
    def get_crypto_prices(self):
        """Get current crypto prices from correlation data"""
        try:
            correlation_file = self.base_dir / "correlation_data" / "hybrid_latest.json"
            if correlation_file.exists():
                with open(correlation_file, 'r') as f:
                    data = json.load(f)
                
                prices = {}
                binance_data = data.get("sources", {}).get("binance", {})
                
                coins = {
                    "BTC": "BTCUSDT",
                    "ETH": "ETHUSDT", 
                    "SOL": "SOLUSDT",
                    "XRP": "XRPUSDT"
                }
                
                for symbol, pair in coins.items():
                    if pair in binance_data:
                        coin_data = binance_data[pair]
                        prices[symbol] = {
                            "price": coin_data.get("price", 0),
                            "change_24h": coin_data.get("change_24h", 0),
                            "volume_24h": coin_data.get("volume_24h", 0)
                        }
                
                return prices
        except Exception as e:
            print(f"Error loading prices: {e}")
            return {}
    
    def get_whale_data(self):
        """Get whale activity from Santiment data"""
        try:
            santiment_file = self.base_dir / "santiment_data" / "multi_asset_flows_latest.json"
            if santiment_file.exists():
                with open(santiment_file, 'r') as f:
                    data = json.load(f)
                
                whale_summary = {}
                assets = data.get("assets", {})
                
                for asset in ["BTC", "ETH", "SOL", "XRP"]:
                    if asset in assets:
                        asset_data = assets[asset]
                        
                        # Get latest inflow/outflow values
                        latest_inflow = 0
                        latest_outflow = 0
                        
                        if asset_data.get("inflows"):
                            latest_inflow = asset_data["inflows"][-1].get("value", 0) or 0
                        if asset_data.get("outflows"):
                            latest_outflow = asset_data["outflows"][-1].get("value", 0) or 0
                        
                        whale_summary[asset] = {
                            "inflow": latest_inflow,
                            "outflow": latest_outflow,
                            "net_flow": latest_inflow - latest_outflow
                        }
                
                return whale_summary
        except Exception as e:
            print(f"Error loading whale data: {e}")
            return {}

# Global data loader
data_loader = SimpleDataLoader()

@app.route('/')
def dashboard():
    """Simple dashboard page"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/data')
def get_data():
    """Get all data for dashboard"""
    return jsonify({
        "prices": data_loader.get_crypto_prices(),
        "whales": data_loader.get_whale_data(),
        "timestamp": datetime.now().isoformat()
    })

# Simple HTML template
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>AgentCeli Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: white;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .header h1 {
            margin: 0;
            color: #2a5298;
            font-size: 2.5rem;
        }
        
        .header p {
            margin: 10px 0 0 0;
            color: #666;
            font-size: 1.1rem;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .section {
            margin-bottom: 40px;
        }
        
        .section h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5rem;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
        
        .coins-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .coin-card {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }
        
        .coin-symbol {
            font-size: 1.2rem;
            font-weight: bold;
            color: #2a5298;
            margin-bottom: 10px;
        }
        
        .coin-price {
            font-size: 2rem;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        
        .coin-change {
            font-size: 1rem;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .coin-change.positive { color: #28a745; }
        .coin-change.negative { color: #dc3545; }
        
        .coin-volume {
            font-size: 0.9rem;
            color: #666;
        }
        
        .whale-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .whale-card {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
        }
        
        .whale-asset {
            font-size: 1.1rem;
            font-weight: bold;
            color: #2a5298;
            margin-bottom: 15px;
            text-align: center;
        }
        
        .whale-flows {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 10px;
            text-align: center;
        }
        
        .whale-flow {
            padding: 10px;
            border-radius: 6px;
            background: white;
        }
        
        .whale-flow-label {
            font-size: 0.8rem;
            color: #666;
            margin-bottom: 5px;
        }
        
        .whale-flow-value {
            font-size: 1rem;
            font-weight: bold;
        }
        
        .inflow { border-left: 4px solid #28a745; }
        .outflow { border-left: 4px solid #dc3545; }
        .netflow { border-left: 4px solid #007bff; }
        
        .refresh-btn {
            background: #2a5298;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1rem;
            margin: 20px 0;
        }
        
        .refresh-btn:hover {
            background: #1e3c72;
        }
        
        .timestamp {
            text-align: center;
            color: #666;
            font-size: 0.9rem;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }
        
        .loading {
            text-align: center;
            color: #666;
            font-style: italic;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 6px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐙 AgentCeli Dashboard</h1>
            <p>Live Crypto Prices & Whale Activity</p>
        </div>
        
        <div class="section">
            <h2>💰 Live Crypto Prices</h2>
            <button class="refresh-btn" onclick="loadData()">🔄 Refresh Data</button>
            <div id="coins-container" class="coins-grid">
                <div class="loading">Loading prices...</div>
            </div>
        </div>
        
        <div class="section">
            <h2>🐋 Whale Activity (Exchange Flows)</h2>
            <div id="whales-container" class="whale-grid">
                <div class="loading">Loading whale data...</div>
            </div>
        </div>
        
        <div class="timestamp">
            Last updated: <span id="timestamp">-</span>
        </div>
    </div>
    
    <script>
        let lastData = null;
        
        async function loadData() {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();
                
                if (response.ok) {
                    lastData = data;
                    updatePrices(data.prices);
                    updateWhales(data.whales);
                    updateTimestamp(data.timestamp);
                } else {
                    showError('Failed to load data');
                }
            } catch (error) {
                console.error('Error loading data:', error);
                showError('Error loading data: ' + error.message);
            }
        }
        
        function updatePrices(prices) {
            const container = document.getElementById('coins-container');
            container.innerHTML = '';
            
            if (!prices || Object.keys(prices).length === 0) {
                container.innerHTML = '<div class="error">No price data available</div>';
                return;
            }
            
            Object.entries(prices).forEach(([symbol, data]) => {
                const changeClass = data.change_24h >= 0 ? 'positive' : 'negative';
                const changeIcon = data.change_24h >= 0 ? '📈' : '📉';
                
                const card = document.createElement('div');
                card.className = 'coin-card';
                card.innerHTML = `
                    <div class="coin-symbol">${symbol}</div>
                    <div class="coin-price">$${data.price.toLocaleString()}</div>
                    <div class="coin-change ${changeClass}">
                        ${changeIcon} ${data.change_24h.toFixed(2)}%
                    </div>
                    <div class="coin-volume">
                        24h Vol: ${(data.volume_24h / 1000).toFixed(1)}K
                    </div>
                `;
                container.appendChild(card);
            });
        }
        
        function updateWhales(whales) {
            const container = document.getElementById('whales-container');
            container.innerHTML = '';
            
            if (!whales || Object.keys(whales).length === 0) {
                container.innerHTML = '<div class="error">No whale data available</div>';
                return;
            }
            
            Object.entries(whales).forEach(([asset, data]) => {
                const netFlowColor = data.net_flow >= 0 ? '#28a745' : '#dc3545';
                const netFlowIcon = data.net_flow >= 0 ? '📈' : '📉';
                
                const card = document.createElement('div');
                card.className = 'whale-card';
                card.innerHTML = `
                    <div class="whale-asset">${asset} Exchange Flows</div>
                    <div class="whale-flows">
                        <div class="whale-flow inflow">
                            <div class="whale-flow-label">Inflow</div>
                            <div class="whale-flow-value">$${data.inflow.toLocaleString()}</div>
                        </div>
                        <div class="whale-flow outflow">
                            <div class="whale-flow-label">Outflow</div>
                            <div class="whale-flow-value">$${data.outflow.toLocaleString()}</div>
                        </div>
                        <div class="whale-flow netflow">
                            <div class="whale-flow-label">Net Flow</div>
                            <div class="whale-flow-value" style="color: ${netFlowColor}">
                                ${netFlowIcon} $${Math.abs(data.net_flow).toLocaleString()}
                            </div>
                        </div>
                    </div>
                `;
                container.appendChild(card);
            });
        }
        
        function updateTimestamp(timestamp) {
            const date = new Date(timestamp);
            document.getElementById('timestamp').textContent = date.toLocaleString();
        }
        
        function showError(message) {
            document.getElementById('coins-container').innerHTML = 
                `<div class="error">${message}</div>`;
            document.getElementById('whales-container').innerHTML = 
                `<div class="error">${message}</div>`;
        }
        
        // Load data on page load
        document.addEventListener('DOMContentLoaded', loadData);
        
        // Auto-refresh every 2 minutes
        setInterval(loadData, 120000);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("🚀 Starting Simple AgentCeli Dashboard...")
    print("📊 Dashboard: http://localhost:8092")
    print("✨ Features: 4 Coins + Whale Activity + Clean Design")
    app.run(host='127.0.0.1', port=8092, debug=False)