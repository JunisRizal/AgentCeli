#!/usr/bin/env python3
"""
Enhanced AgentCeli Liquidation Heatmap
Combines multiple data sources for comprehensive liquidation visualization
Uses: Price volatility, volume spikes, whale movements, Fear & Greed
"""

import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template_string, jsonify
import threading
import sqlite3

class EnhancedLiquidationHeatmap:
    def __init__(self, config_file="agentceli_config.json"):
        """Initialize enhanced liquidation heatmap"""
        self.config = self.load_config(config_file)
        self.liquidation_data = {}
        self.last_update = None
        self.is_running = False
        
        # Data sources
        self.correlation_db = Path("correlation_data/hybrid_crypto_data.db")
        self.santiment_dir = Path("santiment_data")
        
        # Flask app
        self.app = Flask(__name__)
        self.setup_routes()
        
        print("🔥 Enhanced Liquidation Heatmap initialized")
    
    def load_config(self, config_file):
        """Load configuration"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Config error: {e}")
            return {}
    
    def get_volatility_liquidation_risk(self):
        """Calculate liquidation risk from price volatility"""
        try:
            # Read latest AgentCeli data
            latest_file = Path("correlation_data/hybrid_latest.json")
            if not latest_file.exists():
                return {}
            
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            volatility_risk = {}
            binance_data = data.get('sources', {}).get('binance', {})
            
            for pair, pair_data in binance_data.items():
                symbol = pair.replace('USDT', '')
                change_24h = abs(pair_data.get('change_24h', 0))
                volume = pair_data.get('volume_24h', 0)
                price = pair_data.get('price', 0)
                
                # Calculate volatility-based liquidation risk
                volatility_score = min(100, change_24h * 10)  # Scale to 0-100
                volume_score = min(100, (volume / 1000000) * 20)  # Volume impact
                
                # Combine for risk assessment
                risk_score = (volatility_score * 0.6) + (volume_score * 0.4)
                
                volatility_risk[symbol] = {
                    'volatility_score': volatility_score,
                    'volume_score': volume_score,
                    'liquidation_risk_score': risk_score,
                    'price_change_24h': pair_data.get('change_24h', 0),
                    'current_price': price,
                    'volume_24h': volume
                }
            
            return volatility_risk
            
        except Exception as e:
            print(f"❌ Volatility risk error: {e}")
            return {}
    
    def get_whale_movement_impact(self):
        """Analyze whale movements for liquidation correlation"""
        whale_impact = {}
        
        try:
            # Check for whale alert data
            whale_file = self.santiment_dir / "whale_alerts_latest.json"
            if whale_file.exists():
                with open(whale_file, 'r') as f:
                    whale_data = json.load(f)
                
                alerts = whale_data.get('alerts', [])
                whale_impact['whale_alerts_count'] = len(alerts)
                whale_impact['whale_activity_level'] = 'HIGH' if len(alerts) > 10 else 'MEDIUM' if len(alerts) > 5 else 'LOW'
            
            # Check exchange flows
            flows_file = self.santiment_dir / "multi_asset_flows_latest.json"
            if flows_file.exists():
                with open(flows_file, 'r') as f:
                    flows_data = json.load(f)
                
                # Analyze recent flows for each asset
                assets = flows_data.get('assets', {})
                for symbol, asset_data in assets.items():
                    inflows = asset_data.get('inflows', [])
                    outflows = asset_data.get('outflows', [])
                    
                    # Get recent data (last 7 days)
                    recent_inflows = [f for f in inflows[-7:] if f.get('value', 0) > 0]
                    recent_outflows = [f for f in outflows[-7:] if f.get('value', 0) > 0]
                    
                    total_inflow = sum(f.get('value', 0) for f in recent_inflows)
                    total_outflow = sum(f.get('value', 0) for f in recent_outflows)
                    
                    # Calculate flow-based liquidation risk
                    net_flow = total_outflow - total_inflow  # Negative = more inflow (bearish)
                    flow_intensity = abs(net_flow) / 1000000  # Scale down
                    
                    whale_impact[symbol] = {
                        'total_inflow_7d': total_inflow,
                        'total_outflow_7d': total_outflow,
                        'net_flow': net_flow,
                        'flow_intensity': min(100, flow_intensity),
                        'liquidation_pressure': 'HIGH' if net_flow > 50000000 else 'MEDIUM' if net_flow > 10000000 else 'LOW'
                    }
            
            return whale_impact
            
        except Exception as e:
            print(f"❌ Whale movement error: {e}")
            return {}
    
    def get_fear_greed_liquidation_multiplier(self):
        """Get Fear & Greed based liquidation risk multiplier"""
        try:
            # Read from AgentCeli data
            latest_file = Path("correlation_data/hybrid_latest.json")
            if latest_file.exists():
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                
                fg_data = data.get('fear_greed', {})
                fg_value = int(fg_data.get('value', 50))
                
                # Calculate liquidation multiplier based on F&G
                if fg_value > 80:  # Extreme Greed
                    multiplier = 2.0
                    risk_level = "EXTREME_HIGH"
                elif fg_value > 70:  # Greed
                    multiplier = 1.5
                    risk_level = "HIGH"
                elif fg_value > 30:  # Neutral
                    multiplier = 1.0
                    risk_level = "MEDIUM"
                elif fg_value > 20:  # Fear
                    multiplier = 1.3
                    risk_level = "HIGH"
                else:  # Extreme Fear
                    multiplier = 1.8
                    risk_level = "EXTREME_HIGH"
                
                return {
                    'fear_greed_value': fg_value,
                    'fear_greed_class': fg_data.get('value_classification', 'Unknown'),
                    'liquidation_multiplier': multiplier,
                    'risk_level': risk_level,
                    'market_sentiment': self.classify_sentiment(fg_value)
                }
        
        except Exception as e:
            print(f"❌ Fear & Greed error: {e}")
        
        return {'liquidation_multiplier': 1.0, 'risk_level': 'MEDIUM'}
    
    def classify_sentiment(self, fg_value):
        """Classify market sentiment"""
        if fg_value > 80: return "EXTREME_GREED"
        elif fg_value > 70: return "GREED"
        elif fg_value > 60: return "OPTIMISM"
        elif fg_value > 40: return "NEUTRAL"
        elif fg_value > 30: return "CAUTION"
        elif fg_value > 20: return "FEAR"
        else: return "EXTREME_FEAR"
    
    def calculate_enhanced_liquidation_heatmap(self):
        """Calculate comprehensive liquidation heatmap"""
        print("🔥 Calculating enhanced liquidation heatmap...")
        
        # Get all data sources
        volatility_data = self.get_volatility_liquidation_risk()
        whale_data = self.get_whale_movement_impact()
        fg_multiplier_data = self.get_fear_greed_liquidation_multiplier()
        
        heatmap = {
            'timestamp': datetime.now().isoformat(),
            'method': 'enhanced_multi_source',
            'liquidation_heatmap': {},
            'market_overview': {
                'fear_greed': fg_multiplier_data,
                'whale_activity': whale_data.get('whale_activity_level', 'LOW'),
                'total_symbols_analyzed': len(volatility_data)
            },
            'risk_factors': []
        }
        
        # Calculate composite liquidation risk for each symbol
        for symbol, vol_data in volatility_data.items():
            whale_info = whale_data.get(symbol, {})
            
            # Base risk from volatility
            base_risk = vol_data['liquidation_risk_score']
            
            # Whale movement modifier
            whale_modifier = 1.0
            if whale_info:
                flow_intensity = whale_info.get('flow_intensity', 0)
                whale_modifier = 1.0 + (flow_intensity / 100)
            
            # Fear & Greed multiplier
            fg_multiplier = fg_multiplier_data.get('liquidation_multiplier', 1.0)
            
            # Final liquidation risk score
            final_risk = min(100, base_risk * whale_modifier * fg_multiplier)
            
            # Classify risk level
            if final_risk > 80:
                risk_class = "EXTREME"
                color_intensity = 100
            elif final_risk > 60:
                risk_class = "HIGH"
                color_intensity = 80
            elif final_risk > 40:
                risk_class = "MEDIUM"
                color_intensity = 60
            else:
                risk_class = "LOW"
                color_intensity = 30
            
            heatmap['liquidation_heatmap'][symbol] = {
                'liquidation_risk_score': final_risk,
                'risk_class': risk_class,
                'color_intensity': color_intensity,
                'price_change_24h': vol_data['price_change_24h'],
                'current_price': vol_data['current_price'],
                'volume_24h': vol_data['volume_24h'],
                'volatility_component': vol_data['volatility_score'],
                'whale_component': whale_info.get('flow_intensity', 0),
                'fear_greed_multiplier': fg_multiplier,
                'whale_flow_pressure': whale_info.get('liquidation_pressure', 'LOW'),
                'estimated_liquidation_zones': self.estimate_liquidation_zones(vol_data['current_price'], final_risk)
            }
        
        # Add market-wide risk factors
        avg_risk = sum(data['liquidation_risk_score'] for data in heatmap['liquidation_heatmap'].values()) / len(heatmap['liquidation_heatmap']) if heatmap['liquidation_heatmap'] else 0
        
        heatmap['market_overview']['average_liquidation_risk'] = avg_risk
        heatmap['market_overview']['high_risk_symbols'] = len([s for s, d in heatmap['liquidation_heatmap'].items() if d['liquidation_risk_score'] > 70])
        
        # Risk factors summary
        if fg_multiplier_data.get('risk_level') == 'EXTREME_HIGH':
            heatmap['risk_factors'].append("Extreme market sentiment increasing liquidation risk")
        if whale_data.get('whale_activity_level') == 'HIGH':
            heatmap['risk_factors'].append("High whale activity detected")
        if avg_risk > 70:
            heatmap['risk_factors'].append("Multiple assets showing high liquidation risk")
        
        print(f"🔥 Enhanced heatmap calculated: {len(heatmap['liquidation_heatmap'])} symbols, avg risk: {avg_risk:.1f}")
        return heatmap
    
    def estimate_liquidation_zones(self, current_price, risk_score):
        """Estimate potential liquidation zones"""
        # Rough estimation based on typical leverage levels
        zones = {
            'high_leverage_long': current_price * 0.85,  # 85% for 10x leverage longs
            'medium_leverage_long': current_price * 0.75,  # 75% for 5x leverage longs
            'high_leverage_short': current_price * 1.15,  # 115% for 10x leverage shorts
            'medium_leverage_short': current_price * 1.25   # 125% for 5x leverage shorts
        }
        
        # Adjust based on risk score
        risk_factor = risk_score / 100
        zones['adjusted_support'] = current_price * (0.9 - risk_factor * 0.1)
        zones['adjusted_resistance'] = current_price * (1.1 + risk_factor * 0.1)
        
        return zones
    
    def save_heatmap_data(self, data):
        """Save heatmap data"""
        if not data:
            return
        
        # Create liquidation_data directory
        liquidation_dir = Path("liquidation_data")
        liquidation_dir.mkdir(exist_ok=True)
        
        # Save latest
        latest_file = liquidation_dir / "enhanced_liquidation_heatmap_latest.json"
        with open(latest_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Save timestamped backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = liquidation_dir / f"enhanced_liquidation_heatmap_{timestamp}.json"
        with open(backup_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print("💾 Enhanced liquidation heatmap saved")
    
    def update_heatmap_data(self):
        """Update heatmap data"""
        try:
            heatmap_data = self.calculate_enhanced_liquidation_heatmap()
            if heatmap_data:
                self.liquidation_data = heatmap_data
                self.last_update = datetime.now()
                self.save_heatmap_data(heatmap_data)
                
                avg_risk = heatmap_data['market_overview']['average_liquidation_risk']
                high_risk = heatmap_data['market_overview']['high_risk_symbols']
                print(f"✅ Enhanced heatmap updated: {avg_risk:.1f} avg risk, {high_risk} high-risk symbols")
                return True
        
        except Exception as e:
            print(f"❌ Heatmap update error: {e}")
        
        return False
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def heatmap_dashboard():
            return render_template_string(ENHANCED_HEATMAP_TEMPLATE)
        
        @self.app.route('/api/liquidation/enhanced')
        def get_enhanced_heatmap():
            if not self.liquidation_data:
                return jsonify({'error': 'No heatmap data available'}), 404
            return jsonify(self.liquidation_data)
        
        @self.app.route('/api/liquidation/status')
        def heatmap_status():
            return jsonify({
                'status': 'active' if self.is_running else 'stopped',
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'method': 'enhanced_multi_source',
                'data_sources': ['volatility', 'whale_flows', 'fear_greed'],
                'symbols_tracked': len(self.liquidation_data.get('liquidation_heatmap', {}))
            })
    
    def run_enhanced_heatmap(self, port=8086, update_interval=300):
        """Run enhanced liquidation heatmap"""
        print("🔥 Enhanced Liquidation Heatmap Monitor")
        print("=" * 50)
        print(f"🌐 Dashboard: http://localhost:{port}")
        print(f"📊 API: http://localhost:{port}/api/liquidation/enhanced")
        print(f"🔄 Data Sources: Volatility + Whale Flows + Fear & Greed")
        print(f"⏱️ Update Interval: {update_interval}s")
        print()
        
        self.is_running = True
        
        def update_loop():
            while self.is_running:
                try:
                    self.update_heatmap_data()
                    time.sleep(update_interval)
                except Exception as e:
                    print(f"❌ Update error: {e}")
                    time.sleep(60)
        
        # Initial update
        self.update_heatmap_data()
        
        # Background updates
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
        
        # Start Flask
        try:
            self.app.run(host='0.0.0.0', port=port, debug=False)
        except KeyboardInterrupt:
            self.is_running = False
            print("\n🔥 Enhanced Liquidation Heatmap stopped")

# Enhanced HTML template
ENHANCED_HEATMAP_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🔥 Enhanced Liquidation Heatmap - AgentCeli</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a0033 50%, #2d1b69 100%);
            color: white;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            background: linear-gradient(45deg, #ff3333, #ff6b6b, #feca57, #ff9f43);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 30px rgba(255, 51, 51, 0.5);
        }
        
        .method-info {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            border-left: 4px solid #ff6b6b;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(15px);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.15);
        }
        
        .stat-value {
            font-size: 2.2em;
            font-weight: bold;
            margin-bottom: 8px;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        .heatmap-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .heatmap-cell {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 25px;
            text-align: center;
            cursor: pointer;
            transition: all 0.4s ease;
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
            opacity: 0.4;
            border-radius: 20px;
            transition: opacity 0.3s ease;
        }
        
        .heatmap-cell:hover::before { opacity: 0.6; }
        
        .heatmap-cell.LOW::before { 
            background: linear-gradient(135deg, #27ae60, #2ecc71, #58d68d); 
        }
        .heatmap-cell.MEDIUM::before { 
            background: linear-gradient(135deg, #f39c12, #e67e22, #f4d03f); 
        }
        .heatmap-cell.HIGH::before { 
            background: linear-gradient(135deg, #e74c3c, #c0392b, #ff5733); 
        }
        .heatmap-cell.EXTREME::before { 
            background: linear-gradient(135deg, #8e44ad, #9b59b6, #e91e63); 
            animation: pulse 2s ease-in-out infinite alternate;
        }
        
        @keyframes pulse {
            from { opacity: 0.4; }
            to { opacity: 0.8; }
        }
        
        .heatmap-cell:hover {
            transform: scale(1.05) rotateY(5deg);
            border-color: rgba(255, 255, 255, 0.5);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        
        .cell-content {
            position: relative;
            z-index: 1;
        }
        
        .symbol {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .risk-score {
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .price-info {
            font-size: 1.1em;
            margin-bottom: 5px;
        }
        
        .change-24h {
            font-size: 1em;
            font-weight: bold;
        }
        
        .positive { color: #2ecc71; }
        .negative { color: #e74c3c; }
        
        .risk-factors {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            margin-top: 30px;
            border-left: 4px solid #e74c3c;
        }
        
        .liquidation-zones {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            margin-top: 20px;
            border-left: 4px solid #f39c12;
        }
        
        .update-info {
            text-align: center;
            margin-top: 30px;
            opacity: 0.7;
            font-size: 0.9em;
        }
        
        .legend {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 50%;
        }
        
        .legend-low { background: linear-gradient(135deg, #27ae60, #2ecc71); }
        .legend-medium { background: linear-gradient(135deg, #f39c12, #e67e22); }
        .legend-high { background: linear-gradient(135deg, #e74c3c, #c0392b); }
        .legend-extreme { background: linear-gradient(135deg, #8e44ad, #9b59b6); }
        
        @media (max-width: 768px) {
            .heatmap-container {
                grid-template-columns: repeat(2, 1fr);
            }
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔥 Enhanced Liquidation Heatmap</h1>
        <p>Multi-source liquidation risk analysis powered by AgentCeli</p>
    </div>
    
    <div class="method-info">
        <strong>📊 Analysis Method:</strong> Combined volatility analysis, whale flow monitoring, and market sentiment correlation
        <br><strong>🔄 Data Sources:</strong> Binance prices, Santiment whale flows, Fear & Greed index
    </div>
    
    <div class="legend">
        <div class="legend-item">
            <div class="legend-color legend-low"></div>
            <span>Low Risk (0-40)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color legend-medium"></div>
            <span>Medium Risk (40-60)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color legend-high"></div>
            <span>High Risk (60-80)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color legend-extreme"></div>
            <span>Extreme Risk (80+)</span>
        </div>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value" id="avg-risk">-</div>
            <div class="stat-label">Average Risk Score</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="high-risk-count">-</div>
            <div class="stat-label">High Risk Assets</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="fear-greed">-</div>
            <div class="stat-label">Fear & Greed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="whale-activity">-</div>
            <div class="stat-label">Whale Activity</div>
        </div>
    </div>
    
    <div class="heatmap-container" id="heatmap">
        <!-- Heatmap cells populated by JavaScript -->
    </div>
    
    <div class="risk-factors">
        <h3>⚠️ Current Risk Factors</h3>
        <div id="risk-factors-list">Loading risk analysis...</div>
    </div>
    
    <div class="liquidation-zones" id="liquidation-zones-panel" style="display: none;">
        <h3>🎯 Liquidation Zones</h3>
        <div id="liquidation-zones-content"></div>
    </div>
    
    <div class="update-info">
        <p>Last Update: <span id="last-update">-</span></p>
        <p>Enhanced multi-source analysis | Updates every 5 minutes</p>
    </div>

    <script>
        let heatmapData = {};
        
        function updateHeatmap() {
            fetch('/api/liquidation/enhanced')
                .then(response => response.json())
                .then(data => {
                    heatmapData = data;
                    renderEnhancedHeatmap(data);
                    updateStats(data);
                    updateRiskFactors(data);
                })
                .catch(error => {
                    console.error('Error fetching enhanced heatmap:', error);
                    document.getElementById('heatmap').innerHTML = 
                        '<p style="text-align: center; color: #ff6b6b;">Error loading enhanced heatmap data</p>';
                });
        }
        
        function renderEnhancedHeatmap(data) {
            const heatmapContainer = document.getElementById('heatmap');
            heatmapContainer.innerHTML = '';
            
            const heatmapData = data.liquidation_heatmap || {};
            
            for (const [symbol, symbolData] of Object.entries(heatmapData)) {
                const cell = document.createElement('div');
                cell.className = `heatmap-cell ${symbolData.risk_class}`;
                
                const changeClass = symbolData.price_change_24h >= 0 ? 'positive' : 'negative';
                const changeSymbol = symbolData.price_change_24h >= 0 ? '+' : '';
                
                cell.innerHTML = `
                    <div class="cell-content">
                        <div class="symbol">${symbol}</div>
                        <div class="risk-score">${symbolData.liquidation_risk_score.toFixed(1)}</div>
                        <div class="price-info">$${symbolData.current_price.toLocaleString()}</div>
                        <div class="change-24h ${changeClass}">
                            ${changeSymbol}${symbolData.price_change_24h.toFixed(2)}%
                        </div>
                    </div>
                `;
                
                cell.onclick = () => showSymbolDetails(symbol, symbolData);
                heatmapContainer.appendChild(cell);
            }
        }
        
        function updateStats(data) {
            const overview = data.market_overview || {};
            
            document.getElementById('avg-risk').textContent = 
                (overview.average_liquidation_risk || 0).toFixed(1);
            
            document.getElementById('high-risk-count').textContent = 
                overview.high_risk_symbols || '0';
            
            if (overview.fear_greed) {
                document.getElementById('fear-greed').textContent = 
                    overview.fear_greed.fear_greed_value || '-';
            }
            
            document.getElementById('whale-activity').textContent = 
                overview.whale_activity || 'LOW';
            
            document.getElementById('last-update').textContent = 
                new Date(data.timestamp).toLocaleTimeString();
        }
        
        function updateRiskFactors(data) {
            const riskFactorsDiv = document.getElementById('risk-factors-list');
            const riskFactors = data.risk_factors || [];
            
            if (riskFactors.length > 0) {
                riskFactorsDiv.innerHTML = riskFactors.map(factor => 
                    `<p>⚠️ ${factor}</p>`
                ).join('');
            } else {
                riskFactorsDiv.innerHTML = '<p>✅ No major risk factors detected</p>';
            }
        }
        
        function showSymbolDetails(symbol, data) {
            const zones = data.estimated_liquidation_zones || {};
            
            const details = `
                ${symbol} Liquidation Risk Analysis
                
                🔥 Risk Score: ${data.liquidation_risk_score.toFixed(1)}/100 (${data.risk_class})
                📊 Current Price: $${data.current_price.toLocaleString()}
                📈 24h Change: ${data.price_change_24h.toFixed(2)}%
                📊 Volume 24h: ${(data.volume_24h / 1000000).toFixed(1)}M
                
                Risk Components:
                🌊 Volatility: ${data.volatility_component.toFixed(1)}
                🐋 Whale Flows: ${data.whale_component.toFixed(1)}
                😨 F&G Multiplier: ${data.fear_greed_multiplier.toFixed(2)}x
                
                Estimated Liquidation Zones:
                📉 Support: $${zones.adjusted_support ? zones.adjusted_support.toFixed(2) : 'N/A'}
                📈 Resistance: $${zones.adjusted_resistance ? zones.adjusted_resistance.toFixed(2) : 'N/A'}
            `;
            
            alert(details);
        }
        
        // Auto-update every 30 seconds
        updateHeatmap();
        setInterval(updateHeatmap, 30000);
    </script>
</body>
</html>
"""

def main():
    """Start enhanced liquidation heatmap"""
    heatmap = EnhancedLiquidationHeatmap()
    
    print("\n🔥 Enhanced Liquidation Heatmap - AgentCeli")
    print("=" * 50)
    print("Features:")
    print("  📊 Multi-source risk analysis")
    print("  🌊 Volatility-based liquidation estimates")
    print("  🐋 Whale movement correlation")
    print("  😨 Fear & Greed sentiment integration")
    print("  🎯 Estimated liquidation zones")
    print("  ⚡ Real-time heatmap visualization")
    print()
    
    try:
        heatmap.run_enhanced_heatmap()
    except KeyboardInterrupt:
        heatmap.is_running = False
        print("\n🔥 Enhanced Liquidation Heatmap stopped")

if __name__ == "__main__":
    main()