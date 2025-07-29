#!/usr/bin/env python3
"""
AgentCeli Data Delivery Methods
Simple ways to send REAL crypto data to your website or correlation system
"""

import json
import requests
import sqlite3
from datetime import datetime
from pathlib import Path

class DataDelivery:
    def __init__(self):
        self.output_dir = Path("delivery_output")
        self.output_dir.mkdir(exist_ok=True)
    
    def send_to_website(self, data: dict, website_url: str):
        """Send data to your website via HTTP POST"""
        try:
            # Prepare payload
            payload = {
                'timestamp': data.get('timestamp'),
                'source': 'AgentCeli_REAL_DATA',
                'btc_price': self.get_btc_price(data),
                'eth_price': self.get_eth_price(data),
                'sol_price': self.get_sol_price(data),
                'xrp_price': self.get_xrp_price(data),
                'fear_greed': data.get('fear_greed_index', {}).get('value'),
                'market_cap': data.get('market_metrics', {}).get('global_metrics', {}).get('total_market_cap_usd'),
                'data_authenticity': 'VERIFIED_LIVE'
            }
            
            response = requests.post(website_url, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"✅ Data sent to website: {website_url}")
                return True
            else:
                print(f"⚠️ Website returned status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send to website: {e}")
            return False
    
    def save_for_correlation_system(self, data: dict):
        """Save data in format for correlation analysis"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create correlation data structure
        correlation_data = {
            'timestamp': data.get('timestamp'),
            'prices': {
                'BTC': self.get_btc_price(data),
                'ETH': self.get_eth_price(data), 
                'SOL': self.get_sol_price(data),
                'XRP': self.get_xrp_price(data)
            },
            'volumes': {
                'BTC': self.get_btc_volume(data),
                'ETH': self.get_eth_volume(data),
                'SOL': self.get_sol_volume(data),
                'XRP': self.get_xrp_volume(data)
            },
            'changes_24h': {
                'BTC': self.get_btc_change(data),
                'ETH': self.get_eth_change(data),
                'SOL': self.get_sol_change(data),
                'XRP': self.get_xrp_change(data)
            },
            'market_metrics': {
                'fear_greed_index': data.get('fear_greed_index', {}).get('value'),
                'total_market_cap': data.get('market_metrics', {}).get('global_metrics', {}).get('total_market_cap_usd'),
                'coins_up': data.get('market_metrics', {}).get('coins_above_zero'),
                'coins_down': data.get('market_metrics', {}).get('coins_below_zero')
            },
            'data_source': 'AgentCeli_LIVE_EXCHANGES'
        }
        
        # Save as JSON
        json_file = self.output_dir / f"correlation_data_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(correlation_data, f, indent=2)
        
        # Save as CSV for easy import
        csv_file = self.output_dir / f"correlation_data_{timestamp}.csv"
        with open(csv_file, 'w') as f:
            f.write("timestamp,symbol,price,volume,change_24h,fear_greed\n")
            for symbol in ['BTC', 'ETH', 'SOL', 'XRP']:
                f.write(f"{data.get('timestamp')},{symbol},{correlation_data['prices'][symbol]},{correlation_data['volumes'][symbol]},{correlation_data['changes_24h'][symbol]},{correlation_data['market_metrics']['fear_greed_index']}\n")
        
        print(f"📊 Correlation data saved:")
        print(f"   JSON: {json_file}")
        print(f"   CSV: {csv_file}")
        
        return str(json_file), str(csv_file)
    
    def create_simple_api(self, data: dict, port: int = 8080):
        """Create simple HTTP server to serve data"""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import json
        
        class DataHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/crypto-data':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    api_data = {
                        'status': 'live',
                        'timestamp': data.get('timestamp'),
                        'btc': self.server.delivery.get_btc_price(data),
                        'eth': self.server.delivery.get_eth_price(data),
                        'sol': self.server.delivery.get_sol_price(data),
                        'xrp': self.server.delivery.get_xrp_price(data),
                        'fear_greed': data.get('fear_greed_index', {}).get('value'),
                        'source': 'AgentCeli_REAL_DATA'
                    }
                    
                    self.wfile.write(json.dumps(api_data).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
        
        server = HTTPServer(('localhost', port), DataHandler)
        server.delivery = self
        print(f"🌐 Simple API running on http://localhost:{port}/crypto-data")
        return server
    
    # Helper methods to extract prices from different sources
    def get_btc_price(self, data: dict) -> float:
        # Try live exchange data first
        live_data = data.get('live_exchange_data', {})
        
        if 'binance' in live_data and 'BTCUSDT' in live_data['binance']:
            return live_data['binance']['BTCUSDT']['current_price']
        elif 'coinbase' in live_data and 'BTC-USD' in live_data['coinbase']:
            return live_data['coinbase']['BTC-USD']['current_price']
        elif 'bitcoin' in data.get('coins', {}):
            return data['coins']['bitcoin']['price_usd']
        
        return 0.0
    
    def get_eth_price(self, data: dict) -> float:
        live_data = data.get('live_exchange_data', {})
        
        if 'binance' in live_data and 'ETHUSDT' in live_data['binance']:
            return live_data['binance']['ETHUSDT']['current_price']
        elif 'coinbase' in live_data and 'ETH-USD' in live_data['coinbase']:
            return live_data['coinbase']['ETH-USD']['current_price']
        elif 'ethereum' in data.get('coins', {}):
            return data['coins']['ethereum']['price_usd']
        
        return 0.0
    
    def get_sol_price(self, data: dict) -> float:
        live_data = data.get('live_exchange_data', {})
        
        if 'binance' in live_data and 'SOLUSDT' in live_data['binance']:
            return live_data['binance']['SOLUSDT']['current_price']
        elif 'coinbase' in live_data and 'SOL-USD' in live_data['coinbase']:
            return live_data['coinbase']['SOL-USD']['current_price']
        elif 'solana' in data.get('coins', {}):
            return data['coins']['solana']['price_usd']
        
        return 0.0
    
    def get_xrp_price(self, data: dict) -> float:
        live_data = data.get('live_exchange_data', {})
        
        if 'binance' in live_data and 'XRPUSDT' in live_data['binance']:
            return live_data['binance']['XRPUSDT']['current_price']
        elif 'coinbase' in live_data and 'XRP-USD' in live_data['coinbase']:
            return live_data['coinbase']['XRP-USD']['current_price']
        elif 'xrp' in data.get('coins', {}):
            return data['coins']['xrp']['price_usd']
        
        return 0.0
    
    def get_btc_volume(self, data: dict) -> float:
        live_data = data.get('live_exchange_data', {})
        if 'binance' in live_data and 'BTCUSDT' in live_data['binance']:
            return live_data['binance']['BTCUSDT']['volume_24h']
        return 0.0
    
    def get_eth_volume(self, data: dict) -> float:
        live_data = data.get('live_exchange_data', {})
        if 'binance' in live_data and 'ETHUSDT' in live_data['binance']:
            return live_data['binance']['ETHUSDT']['volume_24h']
        return 0.0
    
    def get_sol_volume(self, data: dict) -> float:
        live_data = data.get('live_exchange_data', {})
        if 'binance' in live_data and 'SOLUSDT' in live_data['binance']:
            return live_data['binance']['SOLUSDT']['volume_24h']
        return 0.0
    
    def get_xrp_volume(self, data: dict) -> float:
        live_data = data.get('live_exchange_data', {})
        if 'binance' in live_data and 'XRPUSDT' in live_data['binance']:
            return live_data['binance']['XRPUSDT']['volume_24h']
        return 0.0
    
    def get_btc_change(self, data: dict) -> float:
        live_data = data.get('live_exchange_data', {})
        if 'binance' in live_data and 'BTCUSDT' in live_data['binance']:
            return live_data['binance']['BTCUSDT']['change_24h']
        return 0.0
    
    def get_eth_change(self, data: dict) -> float:
        live_data = data.get('live_exchange_data', {})
        if 'binance' in live_data and 'ETHUSDT' in live_data['binance']:
            return live_data['binance']['ETHUSDT']['change_24h']
        return 0.0
    
    def get_sol_change(self, data: dict) -> float:
        live_data = data.get('live_exchange_data', {})
        if 'binance' in live_data and 'SOLUSDT' in live_data['binance']:
            return live_data['binance']['SOLUSDT']['change_24h']
        return 0.0
    
    def get_xrp_change(self, data: dict) -> float:
        live_data = data.get('live_exchange_data', {})
        if 'binance' in live_data and 'XRPUSDT' in live_data['binance']:
            return live_data['binance']['XRPUSDT']['change_24h']
        return 0.0

# Test the delivery methods
if __name__ == "__main__":
    # Load test data
    try:
        with open('agentceli_test_results.json', 'r') as f:
            test_data = json.load(f)
        
        delivery = DataDelivery()
        
        print("🚀 Testing AgentCeli Data Delivery")
        print("="*40)
        
        # Test 1: Save for correlation system
        json_file, csv_file = delivery.save_for_correlation_system(test_data)
        
        # Test 2: Show extracted prices
        print(f"\n📊 EXTRACTED PRICES:")
        print(f"   BTC: ${delivery.get_btc_price(test_data):,.2f}")
        print(f"   ETH: ${delivery.get_eth_price(test_data):,.2f}")
        print(f"   SOL: ${delivery.get_sol_price(test_data):,.2f}")
        print(f"   XRP: ${delivery.get_xrp_price(test_data):,.2f}")
        
        # Test 3: Website payload example
        print(f"\n🌐 WEBSITE PAYLOAD EXAMPLE:")
        payload = {
            'timestamp': test_data.get('timestamp'),
            'btc_price': delivery.get_btc_price(test_data),
            'eth_price': delivery.get_eth_price(test_data),
            'sol_price': delivery.get_sol_price(test_data),
            'fear_greed': test_data.get('fear_greed_index', {}).get('value')
        }
        print(json.dumps(payload, indent=2))
        
    except FileNotFoundError:
        print("❌ No test data found. Run test_agentceli.py first!")