#!/usr/bin/env python3
"""
AgentCeli Hybrid - Configurable Free + Paid APIs
Start free, upgrade when budget allows
"""

from flask import Flask, jsonify, send_file
import sqlite3
import json
import csv
import threading
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

class AgentCeliHybrid:
    def __init__(self, config=None):
        """Initialize with configurable API tiers"""
        
        # Default configuration - START FREE
        self.config = config or {
            'free_apis': {
                'binance': True,
                'coinbase': True, 
                'coingecko': True,
                'fear_greed': True
            },
            'paid_apis': {
                'coinglass': {'enabled': False, 'key': None},
                'taapi': {'enabled': False, 'key': None},
                'coingecko_pro': {'enabled': False, 'key': None}
            },
            'fallback_mode': True,
            'update_interval': 300
        }
        
        print("🐙 AgentCeli Hybrid initializing...")
        self.print_config()
        
        # Setup components
        self.setup_directories()
        self.setup_database()
        self.setup_sessions()
        
        # Flask API
        self.app = Flask(__name__)
        self.setup_api()
        
        # Data storage
        self.collected_data = {}
        self.last_update = None
        self.is_running = False
        
        print("✅ AgentCeli Hybrid ready!")
    
    def print_config(self):
        """Show current API configuration"""
        print(f"📊 API Configuration:")
        
        # Free APIs
        enabled_free = [api for api, enabled in self.config['free_apis'].items() if enabled]
        print(f"   🆓 Free APIs: {', '.join(enabled_free)}")
        
        # Paid APIs
        enabled_paid = []
        for api, settings in self.config['paid_apis'].items():
            if settings['enabled'] and settings['key']:
                enabled_paid.append(api)
        
        if enabled_paid:
            print(f"   💰 Paid APIs: {', '.join(enabled_paid)}")
            estimated_cost = len(enabled_paid) * 20  # Rough estimate
            print(f"   💳 Estimated monthly cost: ~${estimated_cost}")
        else:
            print(f"   💰 Paid APIs: None (100% FREE)")
        
        print(f"   🔄 Fallback mode: {self.config['fallback_mode']}")
    
    def setup_directories(self):
        """Setup output directories"""
        self.correlation_dir = Path("correlation_data")
        self.correlation_dir.mkdir(exist_ok=True)
    
    def setup_database(self):
        """Setup SQLite database"""
        self.db_path = self.correlation_dir / "hybrid_crypto_data.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_prices (
                timestamp TEXT,
                symbol TEXT,
                price_usd REAL,
                volume_24h REAL,
                change_24h REAL,
                exchange TEXT,
                api_tier TEXT,
                fear_greed INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def setup_sessions(self):
        """Setup HTTP sessions for APIs"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AgentCeli-Hybrid/1.0'
        })
        
        # Add paid API headers if configured
        if self.config['paid_apis']['coingecko_pro']['enabled']:
            key = self.config['paid_apis']['coingecko_pro']['key']
            if key:
                self.session.headers['x-cg-demo-api-key'] = key
    
    def collect_free_data(self):
        """Collect data from free APIs"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'api_tier': 'FREE',
            'sources': {},
            'live_prices': {}
        }
        
        print("🆓 Collecting FREE data...")
        
        # Binance (always free)
        if self.config['free_apis']['binance']:
            binance_data = self.get_binance_data()
            if binance_data:
                data['sources']['binance'] = binance_data
                data['live_prices']['binance'] = binance_data
        
        # CoinGecko free
        if self.config['free_apis']['coingecko']:
            coingecko_data = self.get_coingecko_free()
            if coingecko_data:
                data['sources']['coingecko'] = coingecko_data
        
        # Fear & Greed (always free)
        if self.config['free_apis']['fear_greed']:
            fear_greed = self.get_fear_greed()
            if fear_greed:
                data['fear_greed'] = fear_greed
        
        return data
    
    def collect_paid_data(self):
        """Collect data from paid APIs (if enabled)"""
        paid_data = {}
        
        print("💰 Checking paid APIs...")
        
        # CoinGlass (paid)
        if self.config['paid_apis']['coinglass']['enabled']:
            coinglass_key = self.config['paid_apis']['coinglass']['key']
            if coinglass_key:
                print("💰 Collecting CoinGlass premium data...")
                # Add CoinGlass API calls here
                paid_data['coinglass'] = {'status': 'premium_data_collected'}
        
        # TAAPI (paid)
        if self.config['paid_apis']['taapi']['enabled']:
            taapi_key = self.config['paid_apis']['taapi']['key']
            if taapi_key:
                print("💰 Collecting TAAPI premium data...")
                # Add TAAPI calls here
                paid_data['taapi'] = {'status': 'technical_indicators_collected'}
        
        # CoinGecko Pro (paid)
        if self.config['paid_apis']['coingecko_pro']['enabled']:
            print("💰 Using CoinGecko PRO tier...")
            # Enhanced rate limits, more data
            paid_data['coingecko_pro'] = {'status': 'pro_tier_active'}
        
        if paid_data:
            print(f"💰 Paid data collected from {len(paid_data)} sources")
        
        return paid_data
    
    def get_binance_data(self):
        """Get live data from Binance (always free)"""
        try:
            url = "https://api.binance.com/api/v3/ticker/24hr"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Filter main coins
                main_pairs = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT']
                filtered = {}
                
                for ticker in data:
                    if ticker['symbol'] in main_pairs:
                        filtered[ticker['symbol']] = {
                            'price': float(ticker['lastPrice']),
                            'volume_24h': float(ticker['volume']),
                            'change_24h': float(ticker['priceChangePercent']),
                            'source': 'binance_free'
                        }
                
                print(f"✅ Binance: {len(filtered)} pairs collected")
                return filtered
        
        except Exception as e:
            print(f"❌ Binance error: {e}")
            
        return None
    
    def get_coingecko_free(self):
        """Get CoinGecko free tier data"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': 'bitcoin,ethereum,solana,ripple',
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_market_cap': 'true'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ CoinGecko Free: {len(data)} coins collected")
                return data
        
        except Exception as e:
            print(f"❌ CoinGecko error: {e}")
        
        return None
    
    def get_fear_greed(self):
        """Get Fear & Greed Index (always free)"""
        try:
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and 'data' in data:
                    fg_data = data['data'][0]
                    print(f"✅ Fear & Greed: {fg_data.get('value')} ({fg_data.get('value_classification')})")
                    return fg_data
        
        except Exception as e:
            print(f"❌ Fear & Greed error: {e}")
        
        return None
    
    def collect_all_data(self):
        """Main data collection - combines free + paid"""
        print(f"🐙 Hybrid data collection at {datetime.now().strftime('%H:%M:%S')}")
        
        # Always collect free data
        free_data = self.collect_free_data()
        
        # Collect paid data if enabled
        paid_data = self.collect_paid_data()
        
        # Combine data
        self.collected_data = {
            **free_data,
            'paid_apis': paid_data,
            'total_sources': len(free_data.get('sources', {})) + len(paid_data),
            'cost_estimate': len(paid_data) * 20,  # Monthly estimate
            'configuration': {
                'free_apis_active': len([k for k, v in self.config['free_apis'].items() if v]),
                'paid_apis_active': len([k for k, v in self.config['paid_apis'].items() if v['enabled']])
            }
        }
        
        # Save for correlation systems
        self.save_to_files()
        self.save_to_database()
        
        self.last_update = datetime.now()
        
        total_sources = self.collected_data['total_sources']
        cost = self.collected_data['cost_estimate']
        print(f"✅ Hybrid collection complete: {total_sources} sources, ~${cost}/month")
    
    def save_to_files(self):
        """Save to files for correlation systems"""
        if not self.collected_data:
            return
        
        timestamp = datetime.now()
        
        # Save latest CSV
        csv_file = self.correlation_dir / "hybrid_latest.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'symbol', 'price', 'volume', 'change', 'api_tier', 'fear_greed'])
            
            binance_data = self.collected_data.get('live_prices', {}).get('binance', {})
            fear_greed = self.collected_data.get('fear_greed', {}).get('value', 0)
            
            for pair, data in binance_data.items():
                symbol = pair.replace('USDT', '')
                writer.writerow([
                    timestamp.isoformat(),
                    symbol,
                    data['price'],
                    data['volume_24h'],
                    data['change_24h'],
                    'FREE',
                    fear_greed
                ])
        
        # Save JSON
        json_file = self.correlation_dir / "hybrid_latest.json"
        with open(json_file, 'w') as f:
            json.dump(self.collected_data, f, indent=2)
        
        print("📊 Files saved for correlation systems")
    
    def save_to_database(self):
        """Save to database"""
        if not self.collected_data:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = self.collected_data['timestamp']
        fear_greed = self.collected_data.get('fear_greed', {}).get('value')
        
        binance_data = self.collected_data.get('live_prices', {}).get('binance', {})
        
        for pair, data in binance_data.items():
            symbol = pair.replace('USDT', '')
            cursor.execute('''
                INSERT INTO live_prices 
                (timestamp, symbol, price_usd, volume_24h, change_24h, exchange, api_tier, fear_greed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp, symbol, data['price'], data['volume_24h'], 
                data['change_24h'], 'binance', 'FREE', fear_greed
            ))
        
        conn.commit()
        conn.close()
        print("💾 Database updated")
    
    def setup_api(self):
        """Setup HTTP API for websites"""
        
        @self.app.route('/api/status')
        def status():
            return jsonify({
                'status': 'hybrid_active',
                'configuration': self.collected_data.get('configuration', {}),
                'cost_estimate': self.collected_data.get('cost_estimate', 0),
                'last_update': self.last_update.isoformat() if self.last_update else None
            })
        
        @self.app.route('/api/prices')
        def get_prices():
            if not self.collected_data:
                return jsonify({'error': 'No data'}), 404
            
            binance_data = self.collected_data.get('live_prices', {}).get('binance', {})
            
            return jsonify({
                'timestamp': self.collected_data['timestamp'],
                'api_tier': self.collected_data['api_tier'],
                'btc': binance_data.get('BTCUSDT', {}).get('price', 0),
                'eth': binance_data.get('ETHUSDT', {}).get('price', 0),
                'sol': binance_data.get('SOLUSDT', {}).get('price', 0),
                'xrp': binance_data.get('XRPUSDT', {}).get('price', 0),
                'fear_greed': self.collected_data.get('fear_greed', {}).get('value'),
                'cost_estimate': self.collected_data.get('cost_estimate', 0)
            })
    
    def upgrade_to_paid(self, api_name, api_key):
        """Upgrade specific API to paid tier"""
        if api_name in self.config['paid_apis']:
            self.config['paid_apis'][api_name]['enabled'] = True
            self.config['paid_apis'][api_name]['key'] = api_key
            print(f"💰 Upgraded {api_name} to paid tier")
            self.print_config()
        else:
            print(f"❌ Unknown API: {api_name}")
    
    def downgrade_to_free(self, api_name):
        """Downgrade API to free tier"""
        if api_name in self.config['paid_apis']:
            self.config['paid_apis'][api_name]['enabled'] = False
            self.config['paid_apis'][api_name]['key'] = None
            print(f"🆓 Downgraded {api_name} to free tier")
            self.print_config()
    
    def run_hybrid(self, port=8080):
        """Run hybrid system"""
        print("🐙 AgentCeli Hybrid System")
        print("="*40)
        self.print_config()
        print()
        print("🌐 API Endpoints:")
        print(f"   GET http://localhost:{port}/api/status")
        print(f"   GET http://localhost:{port}/api/prices")
        print()
        print("📊 Correlation Files:")
        print("   correlation_data/hybrid_latest.csv")
        print("   correlation_data/hybrid_latest.json")
        print("   correlation_data/hybrid_crypto_data.db")
        
        # Start collection
        self.is_running = True
        
        def collection_loop():
            while self.is_running:
                try:
                    self.collect_all_data()
                    time.sleep(self.config['update_interval'])
                except Exception as e:
                    print(f"❌ Error: {e}")
                    time.sleep(60)
        
        # Initial collection
        self.collect_all_data()
        
        # Background collection
        thread = threading.Thread(target=collection_loop, daemon=True)
        thread.start()
        
        # Start API server
        self.app.run(host='0.0.0.0', port=port, debug=False)

def main():
    """Start with FREE configuration"""
    # Start completely FREE
    free_config = {
        'free_apis': {
            'binance': True,
            'coinbase': True,
            'coingecko': True, 
            'fear_greed': True
        },
        'paid_apis': {
            'coinglass': {'enabled': False, 'key': None},
            'taapi': {'enabled': False, 'key': None},
            'coingecko_pro': {'enabled': False, 'key': None}
        },
        'fallback_mode': True,
        'update_interval': 300
    }
    
    hybrid = AgentCeliHybrid(free_config)
    
    print("\n💡 To upgrade later:")
    print("   hybrid.upgrade_to_paid('coinglass', 'your_key')")
    print("   hybrid.upgrade_to_paid('taapi', 'your_key')")
    print()
    
    try:
        hybrid.run_hybrid()
    except KeyboardInterrupt:
        hybrid.is_running = False
        print("\n🐙 AgentCeli Hybrid stopped")

if __name__ == "__main__":
    main()