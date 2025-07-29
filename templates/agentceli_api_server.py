#!/usr/bin/env python3
"""
AgentCeli HTTP API Server
Provides REAL crypto data via HTTP API for websites and correlation analysis
"""

from flask import Flask, jsonify, request, send_file
from agentceli_free import AgentCeli
from delivery_methods import DataDelivery
import json
import threading
import time
from datetime import datetime
import csv
import io
from pathlib import Path

class AgentCeliAPIServer:
    def __init__(self, update_interval=300):  # 5 minutes
        self.agent = AgentCeli()
        self.delivery = DataDelivery()
        self.update_interval = update_interval
        self.is_running = False
        
        # Flask app
        self.app = Flask(__name__)
        self.setup_routes()
        
        # Auto-collect data
        self.start_data_collection()
        
        print("🚀 AgentCeli HTTP API Server initialized")
        print(f"⏱️ Data updates every {update_interval} seconds")
    
    def start_data_collection(self):
        """Start automatic data collection in background"""
        if self.is_running:
            return
        
        self.is_running = True
        
        def collect_loop():
            print("🔄 Starting automatic data collection...")
            while self.is_running:
                try:
                    self.agent.collect_all_data()
                    print(f"✅ Data updated at {datetime.now().strftime('%H:%M:%S')}")
                except Exception as e:
                    print(f"❌ Collection error: {e}")
                
                time.sleep(self.update_interval)
        
        collection_thread = threading.Thread(target=collect_loop, daemon=True)
        collection_thread.start()
        
        # Initial collection
        self.agent.collect_all_data()
    
    def setup_routes(self):
        """Setup HTTP API endpoints"""
        
        @self.app.route('/')
        def home():
            return jsonify({
                'status': 'AgentCeli API Server Running',
                'version': '2.0_HTTP_API',
                'data_type': 'LIVE_REAL_CRYPTO_DATA',
                'endpoints': {
                    'all_data': '/api/all',
                    'prices_only': '/api/prices',
                    'specific_coin': '/api/price/<symbol>',
                    'market_summary': '/api/market',
                    'correlation_data': '/api/correlation',
                    'csv_export': '/api/export/csv',
                    'health_check': '/api/health'
                },
                'data_sources': ['Binance_LIVE', 'Coinbase_LIVE', 'Kraken_LIVE', 'CoinGecko'],
                'ai_apis': 'NONE'
            })
        
        @self.app.route('/api/health')
        def health_check():
            """Health check for monitoring"""
            return jsonify({
                'status': 'healthy',
                'last_update': self.agent.last_update.isoformat() if self.agent.last_update else None,
                'data_available': bool(self.agent.collected_data),
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/all')
        def get_all_data():
            """Complete dataset - for correlation analysis"""
            if not self.agent.collected_data:
                return jsonify({'error': 'No data available'}), 404
            
            return jsonify({
                'success': True,
                'timestamp': self.agent.collected_data.get('timestamp'),
                'data_type': 'COMPLETE_LIVE_DATASET',
                'data': self.agent.collected_data
            })
        
        @self.app.route('/api/prices')
        def get_prices_only():
            """Simplified prices - perfect for websites"""
            if not self.agent.collected_data:
                return jsonify({'error': 'No data available'}), 404
            
            prices = {
                'timestamp': self.agent.collected_data.get('timestamp'),
                'btc_usd': self.delivery.get_btc_price(self.agent.collected_data),
                'eth_usd': self.delivery.get_eth_price(self.agent.collected_data),
                'sol_usd': self.delivery.get_sol_price(self.agent.collected_data),
                'xrp_usd': self.delivery.get_xrp_price(self.agent.collected_data),
                'fear_greed_index': self.agent.collected_data.get('fear_greed_index', {}).get('value'),
                'market_cap_usd': self.agent.collected_data.get('market_metrics', {}).get('global_metrics', {}).get('total_market_cap_usd'),
                'data_source': 'AgentCeli_LIVE_EXCHANGES'
            }
            
            return jsonify(prices)
        
        @self.app.route('/api/price/<symbol>')
        def get_specific_price(symbol):
            """Get specific coin price from all exchanges"""
            if not self.agent.collected_data:
                return jsonify({'error': 'No data available'}), 404
            
            symbol = symbol.upper()
            exchanges = {}
            
            # Check all exchanges
            live_data = self.agent.collected_data.get('live_exchange_data', {})
            for exchange, exchange_data in live_data.items():
                for pair, pair_data in exchange_data.items():
                    if symbol in pair:
                        exchanges[f'{exchange}_live'] = {
                            'pair': pair,
                            'price': pair_data.get('current_price'),
                            'change_24h': pair_data.get('change_24h'),
                            'volume_24h': pair_data.get('volume_24h')
                        }
            
            if not exchanges:
                return jsonify({'error': f'No data for {symbol}'}), 404
            
            return jsonify({
                'symbol': symbol,
                'exchanges': exchanges,
                'timestamp': self.agent.collected_data.get('timestamp')
            })
        
        @self.app.route('/api/market')
        def get_market_summary():
            """Market summary - great for dashboards"""
            if not self.agent.collected_data:
                return jsonify({'error': 'No data available'}), 404
            
            market_metrics = self.agent.collected_data.get('market_metrics', {})
            fear_greed = self.agent.collected_data.get('fear_greed_index', {})
            
            summary = {
                'timestamp': self.agent.collected_data.get('timestamp'),
                'market_cap_usd': market_metrics.get('global_metrics', {}).get('total_market_cap_usd'),
                'total_volume_24h_usd': market_metrics.get('global_metrics', {}).get('total_volume_24h_usd'),
                'fear_greed_index': {
                    'value': fear_greed.get('value'),
                    'classification': fear_greed.get('value_classification')
                },
                'coins_performance': {
                    'up': market_metrics.get('coins_above_zero', 0),
                    'down': market_metrics.get('coins_below_zero', 0)
                },
                'top_coins': {
                    'btc_price': self.delivery.get_btc_price(self.agent.collected_data),
                    'eth_price': self.delivery.get_eth_price(self.agent.collected_data),
                    'sol_price': self.delivery.get_sol_price(self.agent.collected_data),
                    'xrp_price': self.delivery.get_xrp_price(self.agent.collected_data)
                },
                'data_authenticity': 'VERIFIED_LIVE'
            }
            
            return jsonify(summary)
        
        @self.app.route('/api/correlation')
        def get_correlation_data():
            """Structured data for correlation analysis"""
            if not self.agent.collected_data:
                return jsonify({'error': 'No data available'}), 404
            
            correlation_data = {
                'timestamp': self.agent.collected_data.get('timestamp'),
                'analysis_ready': True,
                'coins': {
                    'BTC': {
                        'price': self.delivery.get_btc_price(self.agent.collected_data),
                        'volume_24h': self.delivery.get_btc_volume(self.agent.collected_data),
                        'change_24h_percent': self.delivery.get_btc_change(self.agent.collected_data)
                    },
                    'ETH': {
                        'price': self.delivery.get_eth_price(self.agent.collected_data),
                        'volume_24h': self.delivery.get_eth_volume(self.agent.collected_data),
                        'change_24h_percent': self.delivery.get_eth_change(self.agent.collected_data)
                    },
                    'SOL': {
                        'price': self.delivery.get_sol_price(self.agent.collected_data),
                        'volume_24h': self.delivery.get_sol_volume(self.agent.collected_data),
                        'change_24h_percent': self.delivery.get_sol_change(self.agent.collected_data)
                    },
                    'XRP': {
                        'price': self.delivery.get_xrp_price(self.agent.collected_data),
                        'volume_24h': self.delivery.get_xrp_volume(self.agent.collected_data),
                        'change_24h_percent': self.delivery.get_xrp_change(self.agent.collected_data)
                    }
                },
                'market_indicators': {
                    'fear_greed_index': self.agent.collected_data.get('fear_greed_index', {}).get('value'),
                    'total_market_cap': self.agent.collected_data.get('market_metrics', {}).get('global_metrics', {}).get('total_market_cap_usd'),
                    'market_dominance': self.agent.collected_data.get('market_metrics', {}).get('market_dominance', {})
                },
                'data_source': 'AgentCeli_LIVE_REAL_DATA'
            }
            
            return jsonify(correlation_data)
        
        @self.app.route('/api/export/csv')
        def export_csv():
            """Export correlation data as CSV"""
            if not self.agent.collected_data:
                return jsonify({'error': 'No data available'}), 404
            
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Headers
            writer.writerow(['timestamp', 'symbol', 'price_usd', 'volume_24h', 'change_24h_percent', 'fear_greed_index'])
            
            # Data rows
            timestamp = self.agent.collected_data.get('timestamp')
            fear_greed = self.agent.collected_data.get('fear_greed_index', {}).get('value', 0)
            
            coins_data = [
                ('BTC', self.delivery.get_btc_price(self.agent.collected_data), 
                 self.delivery.get_btc_volume(self.agent.collected_data), 
                 self.delivery.get_btc_change(self.agent.collected_data)),
                ('ETH', self.delivery.get_eth_price(self.agent.collected_data), 
                 self.delivery.get_eth_volume(self.agent.collected_data), 
                 self.delivery.get_eth_change(self.agent.collected_data)),
                ('SOL', self.delivery.get_sol_price(self.agent.collected_data), 
                 self.delivery.get_sol_volume(self.agent.collected_data), 
                 self.delivery.get_sol_change(self.agent.collected_data)),
                ('XRP', self.delivery.get_xrp_price(self.agent.collected_data), 
                 self.delivery.get_xrp_volume(self.agent.collected_data), 
                 self.delivery.get_xrp_change(self.agent.collected_data))
            ]
            
            for symbol, price, volume, change in coins_data:
                writer.writerow([timestamp, symbol, price, volume, change, fear_greed])
            
            # Create file-like object for download
            output.seek(0)
            file_data = io.BytesIO()
            file_data.write(output.getvalue().encode('utf-8'))
            file_data.seek(0)
            
            filename = f"agentceli_correlation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            return send_file(
                file_data,
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename
            )
    
    def run_server(self, host='0.0.0.0', port=8080, debug=False):
        """Start the HTTP API server"""
        print(f"🌐 AgentCeli HTTP API Server starting...")
        print(f"📡 Server: http://{host}:{port}")
        print(f"📊 Endpoints:")
        print(f"   GET /api/prices         - Simple prices for websites")
        print(f"   GET /api/correlation    - Data for correlation analysis") 
        print(f"   GET /api/market         - Market summary")
        print(f"   GET /api/export/csv     - Download CSV")
        print(f"   GET /api/health         - Health check")
        print(f"🔴 Data Source: LIVE exchanges (Binance, Coinbase, Kraken)")
        print(f"⚡ Auto-updates every {self.update_interval} seconds")
        
        self.app.run(host=host, port=port, debug=debug)

def main():
    """Start AgentCeli HTTP API Server"""
    print("🚀 AgentCeli HTTP API Server")
    print("="*50)
    print("Provides REAL crypto data via HTTP API")
    print("Perfect for:")
    print("  • Website integration")
    print("  • Correlation analysis") 
    print("  • External system access")
    print()
    
    # Configuration
    update_interval = int(input("Data update interval in seconds (default 300): ") or "300")
    port = int(input("Server port (default 8080): ") or "8080")
    
    # Create and start server
    server = AgentCeliAPIServer(update_interval=update_interval)
    
    try:
        server.run_server(port=port)
    except KeyboardInterrupt:
        server.is_running = False
        print("\n👋 AgentCeli HTTP API Server stopped")

if __name__ == "__main__":
    main()