#!/usr/bin/env python3
"""
AgentCeli Data Kraken 🐙
Collects LIVE crypto data and distributes to:
- Websites (HTTP API)
- Correlation Systems (Files + Database)
"""

from flask import Flask, jsonify, send_file
from agentceli_free import AgentCeli
import sqlite3
import json
import csv
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
import io

class AgentCeliKraken:
    def __init__(self):
        """Initialize the Data Kraken"""
        print("🐙 Initializing AgentCeli Data Kraken...")
        
        # Core data collector
        self.agent = AgentCeli()
        
        # Output directories
        self.correlation_dir = Path("correlation_data")
        self.correlation_dir.mkdir(exist_ok=True)
        
        # Database for correlation systems
        self.db_path = self.correlation_dir / "crypto_timeseries.db"
        self.setup_database()
        
        # Flask API for websites
        self.app = Flask(__name__)
        self.setup_website_api()
        
        # Control flags
        self.is_running = False
        self.update_interval = 300  # 5 minutes
        
        print("🐙 AgentCeli Data Kraken ready!")
    
    def setup_database(self):
        """Setup database for correlation systems"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Time series table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                price_usd REAL,
                volume_24h REAL,
                change_24h_percent REAL,
                exchange TEXT,
                fear_greed_index INTEGER
            )
        ''')
        
        # Market metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                total_market_cap REAL,
                total_volume_24h REAL,
                coins_up INTEGER,
                coins_down INTEGER,
                fear_greed_index INTEGER,
                fear_greed_classification TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("📊 Database initialized for correlation systems")
    
    def collect_and_distribute(self):
        """Core function: Collect data and distribute to all systems"""
        print(f"🐙 Kraken collecting data at {datetime.now().strftime('%H:%M:%S')}")
        
        # Collect LIVE data
        self.agent.collect_all_data()
        
        if not self.agent.collected_data:
            print("❌ No data collected")
            return
        
        # Distribute to correlation systems (files + database)
        self.save_for_correlation_systems()
        
        # Website API data is automatically available via self.agent.collected_data
        
        print("🐙 Data distributed to all systems!")
    
    def save_for_correlation_systems(self):
        """Save data for correlation analysis"""
        timestamp = datetime.now()
        data = self.agent.collected_data
        
        # 1. Save to database (time series)
        self.save_to_database(data, timestamp)
        
        # 2. Save latest CSV (for immediate analysis)
        self.save_latest_csv(data, timestamp)
        
        # 3. Save JSON time series (for detailed analysis)
        self.save_json_timeseries(data, timestamp)
        
        # 4. Archive hourly (for historical correlation)
        if timestamp.minute == 0:  # Every hour
            self.create_hourly_archive(timestamp)
    
    def save_to_database(self, data, timestamp):
        """Save to database for correlation systems"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        ts_str = timestamp.isoformat()
        fear_greed = data.get('fear_greed_index', {})
        fg_value = fear_greed.get('value') if fear_greed else None
        
        # Save individual coin prices
        live_exchanges = data.get('live_exchange_data', {})
        
        for exchange, exchange_data in live_exchanges.items():
            for pair, pair_data in exchange_data.items():
                # Map to standard symbols
                symbol = pair.replace('USDT', '').replace('-USD', '')
                if symbol in ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE']:
                    cursor.execute('''
                        INSERT INTO price_history 
                        (timestamp, symbol, price_usd, volume_24h, change_24h_percent, exchange, fear_greed_index)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        ts_str, symbol, 
                        pair_data.get('current_price'),
                        pair_data.get('volume_24h'),
                        pair_data.get('change_24h'),
                        exchange,
                        fg_value
                    ))
        
        # Save market metrics
        market_metrics = data.get('market_metrics', {})
        global_metrics = market_metrics.get('global_metrics', {})
        
        cursor.execute('''
            INSERT INTO market_metrics 
            (timestamp, total_market_cap, total_volume_24h, coins_up, coins_down, fear_greed_index, fear_greed_classification)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            ts_str,
            global_metrics.get('total_market_cap_usd'),
            global_metrics.get('total_volume_24h_usd'),
            market_metrics.get('coins_above_zero'),
            market_metrics.get('coins_below_zero'),
            fg_value,
            fear_greed.get('value_classification') if fear_greed else None
        ))
        
        conn.commit()
        conn.close()
        print("💾 Data saved to correlation database")
    
    def save_latest_csv(self, data, timestamp):
        """Save latest data as CSV for correlation systems"""
        csv_file = self.correlation_dir / "latest_prices.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'symbol', 'price_usd', 'volume_24h', 'change_24h', 'fear_greed'])
            
            fear_greed_value = data.get('fear_greed_index', {}).get('value', 0)
            live_exchanges = data.get('live_exchange_data', {})
            
            # Extract data from Binance (most complete)
            binance_data = live_exchanges.get('binance', {})
            
            coins = [
                ('BTC', binance_data.get('BTCUSDT', {})),
                ('ETH', binance_data.get('ETHUSDT', {})),
                ('SOL', binance_data.get('SOLUSDT', {})),
                ('XRP', binance_data.get('XRPUSDT', {}))
            ]
            
            for symbol, coin_data in coins:
                if coin_data:
                    writer.writerow([
                        timestamp.isoformat(),
                        symbol,
                        coin_data.get('current_price', 0),
                        coin_data.get('volume_24h', 0),
                        coin_data.get('change_24h', 0),
                        fear_greed_value
                    ])
        
        print("📊 Latest CSV saved for correlation analysis")
    
    def save_json_timeseries(self, data, timestamp):
        """Save JSON time series for detailed correlation analysis"""
        json_file = self.correlation_dir / "timeseries_data.jsonl"  # JSON Lines format
        
        # Create correlation-ready data point
        data_point = {
            'timestamp': timestamp.isoformat(),
            'prices': {},
            'volumes': {},
            'changes': {},
            'market_cap': data.get('market_metrics', {}).get('global_metrics', {}).get('total_market_cap_usd'),
            'fear_greed': data.get('fear_greed_index', {}).get('value')
        }
        
        # Extract prices from live data
        live_exchanges = data.get('live_exchange_data', {})
        binance_data = live_exchanges.get('binance', {})
        
        for pair, pair_data in binance_data.items():
            symbol = pair.replace('USDT', '')
            if symbol in ['BTC', 'ETH', 'SOL', 'XRP']:
                data_point['prices'][symbol] = pair_data.get('current_price')
                data_point['volumes'][symbol] = pair_data.get('volume_24h')
                data_point['changes'][symbol] = pair_data.get('change_24h')
        
        # Append to JSONL file
        with open(json_file, 'a') as f:
            f.write(json.dumps(data_point) + '\n')
        
        print("📈 JSON time series updated")
    
    def create_hourly_archive(self, timestamp):
        """Create hourly archive for historical correlation"""
        hour_str = timestamp.strftime('%Y%m%d_%H')
        archive_file = self.correlation_dir / f"archive_{hour_str}.json"
        
        if self.agent.collected_data:
            with open(archive_file, 'w') as f:
                json.dump(self.agent.collected_data, f, indent=2)
            print(f"📁 Hourly archive created: {archive_file}")
    
    def setup_website_api(self):
        """Setup HTTP API for websites"""
        
        @self.app.route('/api/status')
        def status():
            """Health check for websites"""
            return jsonify({
                'status': 'kraken_active',
                'last_update': self.agent.last_update.isoformat() if self.agent.last_update else None,
                'data_available': bool(self.agent.collected_data),
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/prices')
        def get_prices():
            """Live prices for websites"""
            if not self.agent.collected_data:
                return jsonify({'error': 'No data available'}), 404
            
            live_data = self.agent.collected_data.get('live_exchange_data', {}).get('binance', {})
            
            return jsonify({
                'timestamp': self.agent.collected_data.get('timestamp'),
                'source': 'AgentCeli_Kraken',
                'btc': live_data.get('BTCUSDT', {}).get('current_price', 0),
                'eth': live_data.get('ETHUSDT', {}).get('current_price', 0),
                'sol': live_data.get('SOLUSDT', {}).get('current_price', 0),
                'xrp': live_data.get('XRPUSDT', {}).get('current_price', 0),
                'fear_greed': self.agent.collected_data.get('fear_greed_index', {}).get('value'),
                'market_cap': self.agent.collected_data.get('market_metrics', {}).get('global_metrics', {}).get('total_market_cap_usd')
            })
        
        @self.app.route('/api/btc')
        def get_btc_only():
            """Just BTC - fastest for websites"""
            if not self.agent.collected_data:
                return jsonify({'error': 'No data'}), 404
            
            btc_data = self.agent.collected_data.get('live_exchange_data', {}).get('binance', {}).get('BTCUSDT', {})
            
            return jsonify({
                'symbol': 'BTC',
                'price': btc_data.get('current_price', 0),
                'change_24h': btc_data.get('change_24h', 0),
                'volume': btc_data.get('volume_24h', 0),
                'timestamp': self.agent.collected_data.get('timestamp')
            })
        
        @self.app.route('/api/market')
        def get_market():
            """Market summary for websites"""
            if not self.agent.collected_data:
                return jsonify({'error': 'No data'}), 404
            
            market_metrics = self.agent.collected_data.get('market_metrics', {})
            fear_greed = self.agent.collected_data.get('fear_greed_index', {})
            
            return jsonify({
                'market_cap': market_metrics.get('global_metrics', {}).get('total_market_cap_usd'),
                'fear_greed': {
                    'value': fear_greed.get('value'),
                    'classification': fear_greed.get('value_classification')
                },
                'coins_up': market_metrics.get('coins_above_zero', 0),
                'coins_down': market_metrics.get('coins_below_zero', 0),
                'timestamp': self.agent.collected_data.get('timestamp')
            })
        
        @self.app.route('/correlation/csv')
        def download_csv():
            """Download latest CSV for correlation systems"""
            csv_file = self.correlation_dir / "latest_prices.csv"
            if csv_file.exists():
                return send_file(csv_file, as_attachment=True, download_name='crypto_data.csv')
            return jsonify({'error': 'No CSV available'}), 404
    
    def start_kraken(self):
        """Start the Data Kraken"""
        if self.is_running:
            print("⚠️ Kraken already running")
            return
        
        self.is_running = True
        print("🐙 Starting AgentCeli Data Kraken...")
        
        # Initial data collection
        self.collect_and_distribute()
        
        # Background data collection
        def collection_loop():
            while self.is_running:
                try:
                    time.sleep(self.update_interval)
                    self.collect_and_distribute()
                except Exception as e:
                    print(f"❌ Collection error: {e}")
        
        collection_thread = threading.Thread(target=collection_loop, daemon=True)
        collection_thread.start()
        
        print("✅ Data Kraken active!")
    
    def run_hybrid_server(self, port=8080):
        """Run hybrid server: API for websites + file system for correlation"""
        print("🐙 AgentCeli Data Kraken - HYBRID MODE")
        print("="*50)
        print("🌐 WEBSITES can call:")
        print(f"   GET http://localhost:{port}/api/prices   - Live prices")
        print(f"   GET http://localhost:{port}/api/btc      - Just BTC")
        print(f"   GET http://localhost:{port}/api/market   - Market data")
        print(f"   GET http://localhost:{port}/api/status   - Health check")
        print()
        print("📊 CORRELATION SYSTEMS can use:")
        print(f"   File: correlation_data/latest_prices.csv")
        print(f"   File: correlation_data/timeseries_data.jsonl")
        print(f"   Database: correlation_data/crypto_timeseries.db")
        print(f"   HTTP: http://localhost:{port}/correlation/csv")
        print()
        print("🔴 Data Source: LIVE exchanges (Binance, Coinbase, Kraken)")
        print(f"⏱️ Updates every {self.update_interval//60} minutes")
        
        # Start data collection
        self.start_kraken()
        
        # Start web server
        self.app.run(host='0.0.0.0', port=port, debug=False)

def main():
    """Start AgentCeli Data Kraken"""
    kraken = AgentCeliKraken()
    
    try:
        kraken.run_hybrid_server()
    except KeyboardInterrupt:
        kraken.is_running = False
        print("\n🐙 AgentCeli Data Kraken stopped")

if __name__ == "__main__":
    main()