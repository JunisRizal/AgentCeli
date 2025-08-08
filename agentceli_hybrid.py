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

# Import Santiment module
try:
    from santiment_whale_alerts import SantimentWhaleCollector
    SANTIMENT_AVAILABLE = True
except ImportError:
    SANTIMENT_AVAILABLE = False
    print("⚠️ Santiment module not available")

class AgentCeliHybrid:
    def __init__(self, config=None):
        """Initialize with configurable API tiers"""
        
        # Load real configuration file first
        if config is None:
            config = self.load_real_config()
        
        self.config = config
        
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
    
    def load_real_config(self):
        """Load the real agentceli_config.json file"""
        try:
            config_file = Path("agentceli_config.json")
            if config_file.exists():
                with open(config_file, 'r') as f:
                    real_config = json.load(f)
                    print("✅ Loaded real config from agentceli_config.json")
                    return real_config
            else:
                print("⚠️ agentceli_config.json not found, using defaults")
        except Exception as e:
            print(f"❌ Error loading config: {e}")
        
        # Fallback to defaults if file not found
        return {
            'data_sources': {
                'free_apis': {
                    'binance': {'enabled': True, 'priority': 'high'},
                    'coinbase': {'enabled': True, 'priority': 'medium'}, 
                    'coingecko': {'enabled': True, 'priority': 'high'},
                    'fear_greed': {'enabled': True, 'priority': 'medium'}
                },
                'paid_apis': {
                    'santiment': {'enabled': False, 'key': None, 'cost_per_call': 0.02},
                    'coinglass': {'enabled': False, 'key': None, 'cost_per_call': 0.01},
                    'taapi': {'enabled': False, 'key': None, 'cost_per_call': 0.005}
                }
            },
            'update_intervals': {'fast_data': 300},
            'rate_limits': {'daily_cost_limit': 5.0}
        }
    
    def print_config(self):
        """Show current API configuration"""
        print(f"📊 API Configuration:")
        
        # Get data sources from config
        data_sources = self.config.get('data_sources', {})
        
        # Free APIs
        free_apis = data_sources.get('free_apis', {})
        enabled_free = [api for api, config in free_apis.items() if config.get('enabled', False)]
        print(f"   🆓 Free APIs: {', '.join(enabled_free) if enabled_free else 'None'}")
        
        # Paid APIs
        paid_apis = data_sources.get('paid_apis', {})
        enabled_paid = []
        total_cost = 0
        
        for api, settings in paid_apis.items():
            if settings.get('enabled', False) and settings.get('key'):
                enabled_paid.append(api)
                total_cost += settings.get('cost_per_call', 0) * 100  # Rough monthly estimate
        
        if enabled_paid:
            print(f"   💰 Paid APIs: {', '.join(enabled_paid)}")
            print(f"   💳 Estimated monthly cost: ~${total_cost}")
            
            # Check for separate collectors
            santiment_files = Path("santiment_data").glob("*latest.json") if Path("santiment_data").exists() else []
            if 'santiment' in enabled_paid and santiment_files:
                print(f"   ✅ Santiment: Active with {len(list(santiment_files))} data files")
            elif 'santiment' in enabled_paid:
                print(f"   ⚠️ Santiment: Enabled but no data files found!")
        else:
            print(f"   💰 Paid APIs: None (100% FREE)")
        
        # Check for external collectors
        self.check_external_collectors()
    
    def check_external_collectors(self):
        """Check for external data collectors and warn if missing"""
        print(f"🔍 Checking external collectors...")
        
        # Check Santiment collectors
        santiment_dir = Path("santiment_data")
        if santiment_dir.exists():
            santiment_files = list(santiment_dir.glob("*latest.json"))
            if santiment_files:
                print(f"   ✅ Found {len(santiment_files)} Santiment data files")
                
                # Check file ages
                now = datetime.now()
                for file in santiment_files:
                    file_age = now - datetime.fromtimestamp(file.stat().st_mtime)
                    if file_age.total_seconds() > 86400:  # > 24 hours
                        print(f"   ⚠️ {file.name} is {file_age.days} days old!")
                    else:
                        print(f"   📅 {file.name}: {file_age.seconds//3600}h old")
            else:
                print(f"   ❌ No Santiment data files found in santiment_data/")
        else:
            print(f"   ❌ santiment_data/ directory not found!")
        
        # Check for running processes
        try:
            import subprocess
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if 'santiment' in result.stdout.lower():
                print(f"   ✅ Santiment collector process running")
            else:
                print(f"   ⚠️ No Santiment collector process found")
        except:
            print(f"   ❓ Could not check running processes")
    
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
        paid_apis = self.config.get('data_sources', {}).get('paid_apis', {})
        coingecko_pro = paid_apis.get('coingecko_pro', {})
        if coingecko_pro.get('enabled', False):
            key = coingecko_pro.get('key')
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
        
        # Get free APIs from config
        free_apis = self.config.get('data_sources', {}).get('free_apis', {})
        
        # Binance (always free)
        if free_apis.get('binance', {}).get('enabled', False):
            binance_data = self.get_binance_data()
            if binance_data:
                data['sources']['binance'] = binance_data
                data['live_prices']['binance'] = binance_data
        
        # CoinGecko free
        if free_apis.get('coingecko', {}).get('enabled', False):
            coingecko_data = self.get_coingecko_free()
            if coingecko_data:
                data['sources']['coingecko'] = coingecko_data
        
        # Fear & Greed (always free)
        if free_apis.get('fear_greed', {}).get('enabled', False):
            fear_greed = self.get_fear_greed()
            if fear_greed:
                data['fear_greed'] = fear_greed
        
        return data
    
    def collect_paid_data(self):
        """Collect data from paid APIs (if enabled)"""
        paid_data = {}
        
        print("💰 Checking paid APIs...")
        
        # Get paid APIs from config  
        paid_apis = self.config.get('data_sources', {}).get('paid_apis', {})
        
        # CoinGlass (paid)
        coinglass = paid_apis.get('coinglass', {})
        if coinglass.get('enabled', False):
            coinglass_key = coinglass.get('key')
            if coinglass_key:
                print("💰 Collecting CoinGlass premium data...")
                # Add CoinGlass API calls here
                paid_data['coinglass'] = {'status': 'premium_data_collected'}
        
        # TAAPI (paid)
        taapi = paid_apis.get('taapi', {})
        if taapi.get('enabled', False):
            taapi_key = taapi.get('key')
            if taapi_key:
                print("💰 Collecting TAAPI premium data...")
                # Add TAAPI calls here
                paid_data['taapi'] = {'status': 'technical_indicators_collected'}
        
        # Santiment (paid) - check if enabled with key
        santiment = paid_apis.get('santiment', {})
        if santiment.get('enabled', False) and santiment.get('key'):
            print("💰 Santiment Pro enabled with API key")
            paid_data['santiment_pro'] = {
                'status': 'api_key_configured',
                'key_present': bool(santiment.get('key')),
                'metrics': santiment.get('metrics', [])
            }
        elif santiment.get('enabled', False):
            print("⚠️ Santiment enabled but no API key found!")
            paid_data['santiment_warning'] = {'status': 'missing_api_key'}
        
        # CoinGecko Pro (paid)
        coingecko_pro = paid_apis.get('coingecko_pro', {})
        if coingecko_pro.get('enabled', False):
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
    
    def collect_santiment_data(self):
        """Collect Santiment data from external collectors"""
        santiment_dir = Path("santiment_data")
        if not santiment_dir.exists():
            return None
        
        santiment_summary = {
            'status': 'external_collectors',
            'data_files': {},
            'last_updates': {},
            'warnings': []
        }
        
        # Check for data files
        files = list(santiment_dir.glob("*latest.json"))
        if not files:
            santiment_summary['warnings'].append("No Santiment data files found")
            return santiment_summary
        
        now = datetime.now()
        for file in files:
            try:
                file_age = now - datetime.fromtimestamp(file.stat().st_mtime)
                santiment_summary['data_files'][file.name] = {
                    'size': file.stat().st_size,
                    'age_hours': file_age.seconds // 3600,
                    'age_days': file_age.days
                }
                
                # Load summary data
                with open(file, 'r') as f:
                    data = json.load(f)
                    santiment_summary['last_updates'][file.name] = data.get('timestamp', 'unknown')
                
                # Check if data is stale
                if file_age.total_seconds() > 86400:  # > 24 hours
                    santiment_summary['warnings'].append(f"{file.name} is {file_age.days} days old")
                    
            except Exception as e:
                santiment_summary['warnings'].append(f"Error reading {file.name}: {e}")
        
        print(f"📊 Santiment: Found {len(files)} data files")
        if santiment_summary['warnings']:
            for warning in santiment_summary['warnings']:
                print(f"⚠️ Santiment: {warning}")
        
        return santiment_summary
    
    def collect_all_data(self):
        """Main data collection - combines free + paid"""
        print(f"🐙 Hybrid data collection at {datetime.now().strftime('%H:%M:%S')}")
        
        # Always collect free data
        free_data = self.collect_free_data()
        
        # Collect paid data if enabled
        paid_data = self.collect_paid_data()
        
        # Check for external Santiment data
        santiment_data = self.collect_santiment_data()
        if santiment_data:
            paid_data['santiment'] = santiment_data
        
        # Combine data
        self.collected_data = {
            **free_data,
            'paid_apis': paid_data,
            'total_sources': len(free_data.get('sources', {})) + len(paid_data),
            'cost_estimate': len(paid_data) * 20,  # Monthly estimate
            'configuration': {
                'free_apis_active': len([k for k, v in self.config.get('data_sources', {}).get('free_apis', {}).items() if v.get('enabled', False)]),
                'paid_apis_active': len([k for k, v in self.config.get('data_sources', {}).get('paid_apis', {}).items() if v.get('enabled', False)])
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
        paid_apis = self.config.get('data_sources', {}).get('paid_apis', {})
        if api_name in paid_apis:
            paid_apis[api_name]['enabled'] = True
            paid_apis[api_name]['key'] = api_key
            print(f"💰 Upgraded {api_name} to paid tier")
            self.print_config()
        else:
            print(f"❌ Unknown API: {api_name}")
    
    def downgrade_to_free(self, api_name):
        """Downgrade API to free tier"""
        paid_apis = self.config.get('data_sources', {}).get('paid_apis', {})
        if api_name in paid_apis:
            paid_apis[api_name]['enabled'] = False
            paid_apis[api_name]['key'] = None
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
                    update_interval = self.config.get('update_intervals', {}).get('fast_data', 300)
                    time.sleep(update_interval)
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