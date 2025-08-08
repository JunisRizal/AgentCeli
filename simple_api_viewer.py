#!/usr/bin/env python3
"""
Simple API Viewer - Direct crypto data + AgentCeli status
Shows real crypto prices and your AgentCeli API status side by side
"""

from flask import Flask, jsonify, render_template_string
import requests
import json
from datetime import datetime

app = Flask(__name__)

def get_real_crypto_prices():
    """Get real crypto prices directly from Binance"""
    try:
        response = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Extract main coins
            prices = {}
            pairs = {'BTCUSDT': 'BTC', 'ETHUSDT': 'ETH', 'SOLUSDT': 'SOL', 'XRPUSDT': 'XRP'}
            
            for ticker in data:
                if ticker['symbol'] in pairs:
                    symbol = pairs[ticker['symbol']]
                    prices[symbol] = {
                        'price': float(ticker['lastPrice']),
                        'change_24h': float(ticker['priceChangePercent']),
                        'volume': float(ticker['volume']),
                        'source': 'Binance Direct'
                    }
            
            return prices
        else:
            return {"error": f"Binance API returned {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def get_fear_greed():
    """Get Fear & Greed Index"""
    try:
        response = requests.get("https://api.alternative.me/fng/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and 'data' in data:
                return {
                    'value': int(data['data'][0]['value']),
                    'classification': data['data'][0]['value_classification'],
                    'source': 'Alternative.me'
                }
    except:
        pass
    return {"error": "Failed to get Fear & Greed"}

def get_agentceli_status():
    """Check AgentCeli API status"""
    try:
        # Test AgentCeli API
        status_response = requests.get("http://localhost:8080/api/status", timeout=3)
        prices_response = requests.get("http://localhost:8080/api/prices", timeout=3)
        
        return {
            'api_running': status_response.status_code == 200,
            'status_data': status_response.json() if status_response.status_code == 200 else None,
            'prices_data': prices_response.json() if prices_response.status_code == 200 else None,
            'dashboard_url': 'http://localhost:9000'
        }
    except Exception as e:
        return {
            'api_running': False,
            'error': str(e),
            'dashboard_url': 'http://localhost:9000'
        }

@app.route('/')
def viewer():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/data')
def get_data():
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'real_crypto_prices': get_real_crypto_prices(),
        'fear_greed': get_fear_greed(),
        'agentceli_status': get_agentceli_status()
    })

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>📊 Simple API Viewer</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            color: white;
            min-height: 100vh;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { 
            text-align: center; 
            padding: 30px; 
            background: rgba(255,255,255,0.1); 
            border-radius: 15px; 
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }
        .grid { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 20px; 
            margin-bottom: 20px;
        }
        .panel { 
            background: rgba(255,255,255,0.1); 
            padding: 25px; 
            border-radius: 15px; 
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .crypto-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 15px;
        }
        .crypto-card { 
            background: rgba(0,0,0,0.3); 
            padding: 20px; 
            border-radius: 10px; 
            text-align: center;
            border: 2px solid #4CAF50;
        }
        .crypto-price { 
            font-size: 2rem; 
            font-weight: bold; 
            color: #4CAF50; 
            margin: 10px 0;
        }
        .crypto-change { 
            font-size: 1.1rem; 
            font-weight: bold;
        }
        .positive { color: #4CAF50; }
        .negative { color: #f44336; }
        .status-good { color: #4CAF50; }
        .status-bad { color: #f44336; }
        .status-warning { color: #ff9800; }
        .refresh-btn { 
            background: #4CAF50; 
            color: white; 
            border: none; 
            padding: 12px 24px; 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 16px;
            margin-bottom: 20px;
        }
        .refresh-btn:hover { 
            background: #45a049; 
            transform: translateY(-2px);
        }
        .info-box { 
            background: rgba(0,0,0,0.3); 
            padding: 15px; 
            border-radius: 8px; 
            margin: 10px 0;
        }
        .fear-greed { 
            text-align: center; 
            padding: 20px; 
            background: rgba(0,0,0,0.3); 
            border-radius: 10px;
        }
        .fear-value { 
            font-size: 3rem; 
            font-weight: bold; 
            margin: 10px 0;
        }
        .timestamp { 
            color: rgba(255,255,255,0.7); 
            font-size: 0.9em; 
            text-align: center;
            margin-top: 20px;
        }
        .link { 
            color: #4CAF50; 
            text-decoration: underline; 
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Simple API Viewer</h1>
            <p>Real crypto prices + AgentCeli status</p>
            <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Data</button>
        </div>
        
        <div class="grid">
            <!-- Real Crypto Prices -->
            <div class="panel">
                <h2>💰 Live Crypto Prices (Real)</h2>
                <p style="color: #4CAF50; font-size: 0.9em;">Direct from Binance API</p>
                <div class="crypto-grid" id="crypto-prices">
                    <div>Loading real prices...</div>
                </div>
                
                <div class="fear-greed" id="fear-greed">
                    <div>Loading Fear & Greed...</div>
                </div>
            </div>
            
            <!-- AgentCeli Status -->
            <div class="panel">
                <h2>🐙 AgentCeli API Status</h2>
                <div id="agentceli-status">
                    <div>Checking AgentCeli...</div>
                </div>
                
                <div class="info-box">
                    <h3>Your Dashboards:</h3>
                    <div><span class="link" onclick="window.open('http://localhost:9000', '_blank')">🎛️ Main Dashboard (Port 9000)</span></div>
                    <div><span class="link" onclick="window.open('http://localhost:8080/api/status', '_blank')">🔗 AgentCeli API (Port 8080)</span></div>
                </div>
            </div>
        </div>
        
        <div class="timestamp" id="timestamp">
            Last updated: Loading...
        </div>
    </div>

    <script>
        function refreshData() {
            fetch('/api/data')
                .then(response => response.json())
                .then(data => {
                    updateCryptoPrices(data.real_crypto_prices);
                    updateFearGreed(data.fear_greed);
                    updateAgentCeliStatus(data.agentceli_status);
                    updateTimestamp(data.timestamp);
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('crypto-prices').innerHTML = 
                        '<div style="color: #f44336;">Error loading data: ' + error + '</div>';
                });
        }
        
        function updateCryptoPrices(prices) {
            const container = document.getElementById('crypto-prices');
            let html = '';
            
            if (prices.error) {
                html = '<div style="color: #f44336;">Error: ' + prices.error + '</div>';
            } else {
                for (const [symbol, data] of Object.entries(prices)) {
                    const changeClass = data.change_24h >= 0 ? 'positive' : 'negative';
                    const changeSign = data.change_24h >= 0 ? '+' : '';
                    
                    html += `
                        <div class="crypto-card">
                            <h3>${symbol}</h3>
                            <div class="crypto-price">$${data.price.toLocaleString()}</div>
                            <div class="crypto-change ${changeClass}">
                                ${changeSign}${data.change_24h.toFixed(2)}%
                            </div>
                            <small>Source: ${data.source}</small>
                        </div>
                    `;
                }
            }
            
            container.innerHTML = html;
        }
        
        function updateFearGreed(fearGreed) {
            const container = document.getElementById('fear-greed');
            
            if (fearGreed.error) {
                container.innerHTML = '<div style="color: #f44336;">Fear & Greed: ' + fearGreed.error + '</div>';
            } else {
                let color = '#4CAF50'; // Default green
                if (fearGreed.value < 25) color = '#f44336'; // Red for fear
                else if (fearGreed.value < 50) color = '#ff9800'; // Orange for neutral
                
                container.innerHTML = `
                    <h3>Fear & Greed Index</h3>
                    <div class="fear-value" style="color: ${color};">${fearGreed.value}</div>
                    <div>${fearGreed.classification}</div>
                    <small>Source: ${fearGreed.source}</small>
                `;
            }
        }
        
        function updateAgentCeliStatus(status) {
            const container = document.getElementById('agentceli-status');
            let html = '';
            
            if (status.api_running) {
                html += '<div class="info-box"><span class="status-good">✅ AgentCeli API Running</span></div>';
                
                if (status.status_data) {
                    html += `
                        <div class="info-box">
                            <h4>Status Data:</h4>
                            <div>Configuration: ${status.status_data.configuration?.free_apis_active || 0} free APIs, ${status.status_data.configuration?.paid_apis_active || 0} paid APIs</div>
                            <div>Cost Estimate: $${status.status_data.cost_estimate || 0}</div>
                            <div>Last Update: ${status.status_data.last_update ? new Date(status.status_data.last_update).toLocaleTimeString() : 'N/A'}</div>
                        </div>
                    `;
                }
                
                if (status.prices_data) {
                    const hasRealPrices = status.prices_data.btc > 0 || status.prices_data.eth > 0;
                    const priceStatus = hasRealPrices ? 'status-good' : 'status-warning';
                    const priceMessage = hasRealPrices ? '✅ Returning real prices' : '⚠️ Returning zero prices (data collection issue)';
                    
                    html += `
                        <div class="info-box">
                            <h4>Price Data:</h4>
                            <div class="${priceStatus}">${priceMessage}</div>
                            <div>API Tier: ${status.prices_data.api_tier}</div>
                            <div>Fear & Greed: ${status.prices_data.fear_greed || 'N/A'}</div>
                        </div>
                    `;
                }
            } else {
                html += `
                    <div class="info-box">
                        <span class="status-bad">❌ AgentCeli API Not Running</span>
                        <div>Error: ${status.error || 'Connection failed'}</div>
                    </div>
                `;
            }
            
            container.innerHTML = html;
        }
        
        function updateTimestamp(timestamp) {
            document.getElementById('timestamp').textContent = 
                'Last updated: ' + new Date(timestamp).toLocaleString();
        }
        
        // Initialize and auto-refresh
        refreshData();
        setInterval(refreshData, 15000); // Refresh every 15 seconds
    </script>
</body>
</html>
'''

if __name__ == "__main__":
    print("📊 Starting Simple API Viewer...")
    print("🌐 URL: http://localhost:8091")
    print("💰 Shows real crypto prices from Binance")
    print("🐙 Shows your AgentCeli API status")
    print("🎛️ Your main dashboard: http://localhost:9000")
    
    app.run(host='127.0.0.1', port=8091, debug=False)