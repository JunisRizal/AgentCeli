#!/usr/bin/env python3
"""
AgentCeli Liquidation Heatmap
Real-time liquidation data visualization with heatmap interface
"""

import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template_string, jsonify
import threading

class LiquidationHeatmap:
    def __init__(self, config_file="agentceli_config.json"):
        """Initialize liquidation heatmap system"""
        self.config = self.load_config(config_file)
        self.liquidation_data = {}
        self.last_update = None
        self.is_running = False
        
        # Setup CoinGlass API
        self.setup_coinglass_api()
        
        # Flask app for heatmap display
        self.app = Flask(__name__)
        self.setup_routes()
        
        print("🔥 Liquidation Heatmap initialized")
    
    def load_config(self, config_file):
        """Load configuration"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                print("✅ Config loaded for liquidation heatmap")
                return config
        except Exception as e:
            print(f"❌ Config error: {e}")
            return {}
    
    def setup_coinglass_api(self):
        """Setup CoinGlass API session"""
        self.coinglass_url = "https://open-api-v3.coinglass.com"
        self.session = requests.Session()
        
        # Get CoinGlass key from config
        coinglass_config = self.config.get('data_sources', {}).get('paid_apis', {}).get('coinglass', {})
        coinglass_key = coinglass_config.get('key')
        
        if coinglass_key:
            self.session.headers['coinglassSecret'] = coinglass_key
            print("💰 CoinGlass Pro API configured")
        else:
            print("🆓 Using CoinGlass free API (limited)")
    
    def get_liquidation_heatmap_data(self):
        """Get liquidation data for heatmap visualization"""
        try:
            # Get liquidation data for major coins
            symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'MATIC', 'LTC']
            liquidation_map = {
                'timestamp': datetime.now().isoformat(),
                'heatmap_data': {},
                'total_liquidations_24h': 0,
                'major_liquidations': []
            }
            
            print("🔥 Fetching liquidation data for heatmap...")
            
            for symbol in symbols:
                liq_data = self.get_symbol_liquidations(symbol)
                if liq_data:
                    liquidation_map['heatmap_data'][symbol] = liq_data
                    
                    # Add to total liquidations
                    if 'liquidations_24h' in liq_data:
                        liquidation_map['total_liquidations_24h'] += liq_data['liquidations_24h']
                    
                    # Track major liquidations (>$1M)
                    if liq_data.get('liquidations_24h', 0) > 1000000:
                        liquidation_map['major_liquidations'].append({
                            'symbol': symbol,
                            'amount': liq_data['liquidations_24h'],
                            'long_short_ratio': liq_data.get('long_short_ratio', 0)
                        })
                
                time.sleep(0.5)  # Rate limiting
            
            print(f"🔥 Liquidation heatmap data collected: {len(liquidation_map['heatmap_data'])} symbols")
            return liquidation_map
            
        except Exception as e:
            print(f"❌ Liquidation heatmap error: {e}")
            return None
    
    def get_symbol_liquidations(self, symbol):
        """Get liquidation data for specific symbol"""
        try:
            # Liquidation history endpoint
            url = f"{self.coinglass_url}/api/futures/liquidation/coin/history"
            params = {
                'symbol': symbol,
                'timeType': '24h',
                'limit': 100
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'data' in data:
                    liquidations = data['data']
                    
                    # Calculate metrics for heatmap
                    total_longs = sum(float(item.get('longLiquidation', 0)) for item in liquidations)
                    total_shorts = sum(float(item.get('shortLiquidation', 0)) for item in liquidations)
                    total_liquidations = total_longs + total_shorts
                    
                    # Calculate intensity for heatmap color
                    intensity = min(100, (total_liquidations / 10000000) * 100)  # Normalize to 0-100
                    
                    result = {
                        'liquidations_24h': total_liquidations,
                        'long_liquidations': total_longs,
                        'short_liquidations': total_shorts,
                        'long_short_ratio': (total_longs / total_shorts) if total_shorts > 0 else 999,
                        'intensity': intensity,
                        'color_intensity': intensity,
                        'latest_data': liquidations[:5] if liquidations else []
                    }
                    
                    print(f"✅ {symbol}: ${total_liquidations:,.0f} liquidated (24h)")
                    return result
            
            elif response.status_code == 429:
                print(f"⚠️ Rate limited for {symbol}")
                return None
                
        except Exception as e:
            print(f"❌ {symbol} liquidation error: {e}")
            
        return None
    
    def get_fear_greed_liquidation_correlation(self):
        """Correlate Fear & Greed with liquidation intensity"""
        try:
            # Get Fear & Greed
            fg_url = "https://api.alternative.me/fng/"
            response = requests.get(fg_url, timeout=10)
            
            if response.status_code == 200:
                fg_data = response.json()
                if fg_data and 'data' in fg_data:
                    fg_value = int(fg_data['data'][0]['value'])
                    fg_class = fg_data['data'][0]['value_classification']
                    
                    # Correlate with liquidation intensity
                    correlation = {
                        'fear_greed_value': fg_value,
                        'fear_greed_class': fg_class,
                        'liquidation_risk': 'HIGH' if fg_value > 80 or fg_value < 20 else 'MEDIUM' if fg_value > 60 or fg_value < 40 else 'LOW',
                        'market_sentiment': 'EXTREME_GREED' if fg_value > 80 else 'GREED' if fg_value > 60 else 'NEUTRAL' if fg_value > 40 else 'FEAR' if fg_value > 20 else 'EXTREME_FEAR'
                    }
                    
                    return correlation
                    
        except Exception as e:
            print(f"❌ Fear & Greed correlation error: {e}")
            
        return None
    
    def save_liquidation_data(self, data):
        """Save liquidation data to file"""
        if not data:
            return
            
        # Save to liquidation_data directory
        liquidation_dir = Path("liquidation_data")
        liquidation_dir.mkdir(exist_ok=True)
        
        # Save latest data
        latest_file = liquidation_dir / "liquidation_heatmap_latest.json"
        with open(latest_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Save timestamped backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = liquidation_dir / f"liquidation_heatmap_{timestamp}.json"
        with open(backup_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print("💾 Liquidation heatmap data saved")
    
    def update_liquidation_data(self):
        """Update all liquidation data"""
        print("🔥 Updating liquidation heatmap data...")
        
        # Get heatmap data
        heatmap_data = self.get_liquidation_heatmap_data()
        
        # Get correlation data
        correlation_data = self.get_fear_greed_liquidation_correlation()
        
        # Combine data
        if heatmap_data:
            heatmap_data['correlation'] = correlation_data
            self.liquidation_data = heatmap_data
            self.last_update = datetime.now()
            
            # Save data
            self.save_liquidation_data(heatmap_data)
            
            print(f"✅ Liquidation heatmap updated: ${heatmap_data['total_liquidations_24h']:,.0f} total liquidations")
            return True
        
        return False
    
    def setup_routes(self):
        """Setup Flask routes for heatmap interface"""
        
        @self.app.route('/')
        def heatmap_dashboard():
            return render_template_string(HEATMAP_TEMPLATE)
        
        @self.app.route('/api/liquidation/heatmap')
        def get_heatmap_data():
            if not self.liquidation_data:
                return jsonify({'error': 'No liquidation data available'}), 404
            
            return jsonify(self.liquidation_data)
        
        @self.app.route('/api/liquidation/status')
        def liquidation_status():
            return jsonify({
                'status': 'active' if self.is_running else 'stopped',
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'data_available': bool(self.liquidation_data),
                'total_symbols': len(self.liquidation_data.get('heatmap_data', {}))
            })
    
    def run_liquidation_monitor(self, port=8085, update_interval=300):
        """Run liquidation heatmap monitor"""
        print("🔥 Starting Liquidation Heatmap Monitor")
        print("="*50)
        print(f"🌐 Heatmap Dashboard: http://localhost:{port}")
        print(f"📊 API Endpoint: http://localhost:{port}/api/liquidation/heatmap")
        print(f"⏱️ Update Interval: {update_interval}s")
        print()
        
        self.is_running = True
        
        def update_loop():
            while self.is_running:
                try:
                    self.update_liquidation_data()
                    time.sleep(update_interval)
                except Exception as e:
                    print(f"❌ Update error: {e}")
                    time.sleep(60)
        
        # Initial update
        self.update_liquidation_data()
        
        # Start background updates
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
        
        # Start Flask app
        try:
            self.app.run(host='0.0.0.0', port=port, debug=False)
        except KeyboardInterrupt:
            self.is_running = False
            print("\n🔥 Liquidation Heatmap stopped")

# HTML template for heatmap visualization
HEATMAP_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🔥 AgentCeli Liquidation Heatmap</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e1e2e 0%, #2d1b69 100%);
            color: white;
            margin: 0;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            background: linear-gradient(45deg, #ff6b6b, #feca57, #48dbfb);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .stats-row {
            display: flex;
            justify-content: space-around;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            min-width: 150px;
            margin: 10px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        .heatmap-container {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .heatmap-cell {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 2px solid transparent;
            position: relative;
            overflow: hidden;
        }
        
        .heatmap-cell::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            opacity: 0.3;
            border-radius: 15px;
        }
        
        .heatmap-cell.low::before { background: linear-gradient(135deg, #27ae60, #2ecc71); }
        .heatmap-cell.medium::before { background: linear-gradient(135deg, #f39c12, #e67e22); }
        .heatmap-cell.high::before { background: linear-gradient(135deg, #e74c3c, #c0392b); }
        .heatmap-cell.extreme::before { background: linear-gradient(135deg, #8e44ad, #9b59b6); }
        
        .heatmap-cell:hover {
            transform: scale(1.05);
            border-color: rgba(255, 255, 255, 0.5);
        }
        
        .cell-content {
            position: relative;
            z-index: 1;
        }
        
        .symbol {
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .liquidation-amount {
            font-size: 1.2em;
            margin-bottom: 5px;
        }
        
        .ratio {
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        .correlation-panel {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            margin-top: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .update-info {
            text-align: center;
            margin-top: 20px;
            opacity: 0.7;
            font-size: 0.9em;
        }
        
        @media (max-width: 768px) {
            .heatmap-container {
                grid-template-columns: repeat(2, 1fr);
            }
            .stats-row {
                flex-direction: column;
                align-items: center;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔥 Liquidation Heatmap</h1>
        <p>Real-time cryptocurrency liquidation monitoring</p>
    </div>
    
    <div class="stats-row">
        <div class="stat-card">
            <div class="stat-value" id="total-liquidations">-</div>
            <div class="stat-label">Total 24h Liquidations</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="major-liquidations">-</div>
            <div class="stat-label">Major Liquidations</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="fear-greed">-</div>
            <div class="stat-label">Fear & Greed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="liquidation-risk">-</div>
            <div class="stat-label">Liquidation Risk</div>
        </div>
    </div>
    
    <div class="heatmap-container" id="heatmap">
        <!-- Heatmap cells will be populated by JavaScript -->
    </div>
    
    <div class="correlation-panel">
        <h3>📊 Market Correlation Analysis</h3>
        <div id="correlation-details">Loading correlation data...</div>
    </div>
    
    <div class="update-info">
        <p>Last Update: <span id="last-update">-</span></p>
        <p>Updates every 5 minutes | Data from CoinGlass & AgentCeli</p>
    </div>

    <script>
        let liquidationData = {};
        
        function updateHeatmap() {
            fetch('/api/liquidation/heatmap')
                .then(response => response.json())
                .then(data => {
                    liquidationData = data;
                    renderHeatmap(data);
                    updateStats(data);
                    updateCorrelation(data);
                })
                .catch(error => {
                    console.error('Error fetching liquidation data:', error);
                    document.getElementById('heatmap').innerHTML = '<p style="text-align: center; color: #ff6b6b;">Error loading liquidation data</p>';
                });
        }
        
        function renderHeatmap(data) {
            const heatmapContainer = document.getElementById('heatmap');
            heatmapContainer.innerHTML = '';
            
            const heatmapData = data.heatmap_data || {};
            
            for (const [symbol, symbolData] of Object.entries(heatmapData)) {
                const cell = document.createElement('div');
                cell.className = 'heatmap-cell';
                
                // Determine intensity class
                const intensity = symbolData.intensity || 0;
                if (intensity > 75) cell.classList.add('extreme');
                else if (intensity > 50) cell.classList.add('high');
                else if (intensity > 25) cell.classList.add('medium');
                else cell.classList.add('low');
                
                const liquidationAmount = symbolData.liquidations_24h || 0;
                const ratio = symbolData.long_short_ratio || 0;
                
                cell.innerHTML = `
                    <div class="cell-content">
                        <div class="symbol">${symbol}</div>
                        <div class="liquidation-amount">$${(liquidationAmount / 1000000).toFixed(1)}M</div>
                        <div class="ratio">L/S: ${ratio.toFixed(2)}</div>
                    </div>
                `;
                
                cell.onclick = () => showSymbolDetails(symbol, symbolData);
                heatmapContainer.appendChild(cell);
            }
        }
        
        function updateStats(data) {
            document.getElementById('total-liquidations').textContent = 
                '$' + (data.total_liquidations_24h / 1000000).toFixed(1) + 'M';
            
            document.getElementById('major-liquidations').textContent = 
                data.major_liquidations ? data.major_liquidations.length : '0';
            
            if (data.correlation) {
                document.getElementById('fear-greed').textContent = 
                    data.correlation.fear_greed_value || '-';
                document.getElementById('liquidation-risk').textContent = 
                    data.correlation.liquidation_risk || '-';
            }
            
            document.getElementById('last-update').textContent = 
                new Date(data.timestamp).toLocaleTimeString();
        }
        
        function updateCorrelation(data) {
            const correlationDiv = document.getElementById('correlation-details');
            
            if (data.correlation) {
                const corr = data.correlation;
                correlationDiv.innerHTML = `
                    <p><strong>Fear & Greed:</strong> ${corr.fear_greed_value} (${corr.fear_greed_class})</p>
                    <p><strong>Market Sentiment:</strong> ${corr.market_sentiment}</p>
                    <p><strong>Liquidation Risk:</strong> ${corr.liquidation_risk}</p>
                    <p><strong>Analysis:</strong> ${corr.liquidation_risk === 'HIGH' ? 
                        'High liquidation risk due to extreme market sentiment' : 
                        'Moderate liquidation conditions'}</p>
                `;
            } else {
                correlationDiv.innerHTML = '<p>Correlation data not available</p>';
            }
        }
        
        function showSymbolDetails(symbol, data) {
            alert(`${symbol} Liquidation Details:\\n\\n` +
                  `24h Liquidations: $${(data.liquidations_24h / 1000000).toFixed(2)}M\\n` +
                  `Long Liquidations: $${(data.long_liquidations / 1000000).toFixed(2)}M\\n` +
                  `Short Liquidations: $${(data.short_liquidations / 1000000).toFixed(2)}M\\n` +
                  `Long/Short Ratio: ${data.long_short_ratio.toFixed(2)}\\n` +
                  `Intensity: ${data.intensity.toFixed(1)}%`);
        }
        
        // Auto-update every 30 seconds
        updateHeatmap();
        setInterval(updateHeatmap, 30000);
    </script>
</body>
</html>
"""

def main():
    """Start liquidation heatmap monitor"""
    heatmap = LiquidationHeatmap()
    
    print("\n🔥 AgentCeli Liquidation Heatmap")
    print("=" * 40)
    print("Features:")
    print("  📊 Real-time liquidation data")
    print("  🌡️ Color-coded intensity heatmap")
    print("  📈 Fear & Greed correlation")
    print("  💰 Long/Short liquidation ratios")
    print("  ⚡ Auto-updating every 5 minutes")
    print()
    
    try:
        heatmap.run_liquidation_monitor()
    except KeyboardInterrupt:
        heatmap.is_running = False
        print("\n🔥 Liquidation Heatmap stopped")

if __name__ == "__main__":
    main()