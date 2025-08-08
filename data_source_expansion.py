#!/usr/bin/env python3
"""
Data Source Expansion - Including Santiment Integration
"""
"""
AgentCeli Data Source Expansion Module
Allows easy addition of new data sources and API connections
"""

import json
import time
import sys
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

# Import requests properly (avoid local file conflict)
if "/Users/julius/Desktop/AgentCeli" in sys.path:
    sys.path.remove("/Users/julius/Desktop/AgentCeli")

import requests as http_requests

class DataSourceInterface(ABC):
    """Base interface for all data sources"""
    
    @abstractmethod
    def connect(self):
        """Establish connection to data source"""
        pass
    
    @abstractmethod
    def fetch_data(self):
        """Fetch data from source"""
        pass
    
    @abstractmethod
    def get_cost_estimate(self):
        """Get cost estimate for API calls"""
        pass

class KrakenAPI(DataSourceInterface):
    """Kraken exchange API integration"""
    
    def __init__(self, config=None):
        self.base_url = "https://api.kraken.com/0/public"
        self.config = config or {}
        self.last_request = 0
        self.rate_limit = 1  # 1 second between requests
        
    def connect(self):
        """Test Kraken API connection"""
        try:
            response = requests.get(f"{self.base_url}/SystemStatus", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('result', {}).get('status') == 'online'
        except:
            return False
        return False
    
    def fetch_data(self):
        """Fetch crypto prices from Kraken"""
        self._rate_limit()
        
        try:
            # Get ticker data
            pairs = "BTCUSD,ETHUSD,XRPUSD,SOLUSD"
            response = requests.get(f"{self.base_url}/Ticker?pair={pairs}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'result' in data:
                    result = {}
                    for pair, info in data['result'].items():
                        # Map Kraken pair names to standard symbols
                        if 'XXBTZUSD' in pair or 'BTCUSD' in pair:
                            symbol = 'BTC'
                        elif 'XETHZUSD' in pair or 'ETHUSD' in pair:
                            symbol = 'ETH'
                        elif 'XXRPZUSD' in pair or 'XRPUSD' in pair:
                            symbol = 'XRP'
                        elif 'SOLUSD' in pair:
                            symbol = 'SOL'
                        else:
                            continue
                            
                        result[symbol] = {
                            'price': float(info['c'][0]),  # Last trade price
                            'volume_24h': float(info['v'][1]),  # 24h volume
                            'change_24h': self._calculate_change(info),
                            'source': 'kraken_free',
                            'timestamp': datetime.now().isoformat()
                        }
                    
                    return result
                    
        except Exception as e:
            print(f"Kraken API error: {e}")
            return None
    
    def _calculate_change(self, ticker_info):
        """Calculate 24h percentage change"""
        try:
            current = float(ticker_info['c'][0])
            yesterday = float(ticker_info['o'])
            return ((current - yesterday) / yesterday) * 100
        except:
            return 0.0
    
    def _rate_limit(self):
        """Ensure rate limiting"""
        now = time.time()
        if now - self.last_request < self.rate_limit:
            time.sleep(self.rate_limit - (now - self.last_request))
        self.last_request = time.time()
    
    def get_cost_estimate(self):
        """Kraken public API is free"""
        return 0.0

class CoinbaseAdvancedAPI(DataSourceInterface):
    """Coinbase Advanced Trade API"""
    
    def __init__(self, config=None):
        self.base_url = "https://api.exchange.coinbase.com"
        self.config = config or {}
        self.rate_limit = 1
        self.last_request = 0
        
    def connect(self):
        """Test Coinbase API connection"""
        try:
            response = http_requests.get(f"{self.base_url}/time", timeout=5)
            return response.status_code == 200
        except:
            return False

class SantimentWhaleAPI(DataSourceInterface):
    """Santiment Whale Alerts API - Direct Integration"""
    
    def __init__(self, config=None):
        self.api_key = "7zelhlvci5blrymf_o5vruhdpz42smn7t"
        self.endpoint = "https://api.santiment.net/graphql"
        self.config = config or {}
        
        self.headers = {
            "Authorization": f"Apikey {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Target metrics and assets
        self.metrics = [
            "whale_transaction_count_1m_usd_to_inf",
            "exchange_inflow",
            "exchange_outflow", 
            "sentiment_balance_total"
        ]
        
        self.assets = ["bitcoin", "ethereum", "ripple", "solana"]
        
    def connect(self):
        """Test Santiment API connection"""
        try:
            test_query = '{ getMetric(metric: "price_usd") { metadata { availableAssets } } }'
            payload = {"query": test_query}
            
            response = http_requests.post(
                self.endpoint,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=10
            )
            
            return response.status_code == 200
        except:
            return False
    
    def build_query(self, metric, assets, from_date, to_date, interval="1d"):
        """Build GraphQL query for Santiment"""
        asset_list = json.dumps(assets)
        
        return f'''
        query {{
            getMetric(metric: "{metric}") {{
                timeseriesDataPerSlugJson(
                    selector: {{ slugs: {asset_list} }},
                    from: "{from_date}",
                    to: "{to_date}",
                    interval: "{interval}"
                )
            }}
        }}
        '''.strip()
    
    def fetch_data(self):
        """Fetch whale data from Santiment"""
        # Get yesterday's data (1 day interval)
        to_date = datetime.now().strftime("%Y-%m-%dT00:00:00Z")
        from_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
        
        result = {
            "source": "santiment",
            "timestamp": datetime.now().isoformat(),
            "whale_data": {}
        }
        
        # Asset mapping for output
        asset_map = {
            "bitcoin": "BTC",
            "ethereum": "ETH",
            "ripple": "XRP", 
            "solana": "SOL"
        }
        
        # Initialize asset data
        for symbol in asset_map.values():
            result["whale_data"][symbol] = {}
        
        # Fetch each metric
        for metric in self.metrics:
            try:
                query = self.build_query(metric, self.assets, from_date, to_date)
                payload = {"query": query}
                
                response = http_requests.post(
                    self.endpoint,
                    headers=self.headers,
                    data=json.dumps(payload),
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "data" in data and data["data"]["getMetric"]:
                        metric_data = data["data"]["getMetric"]["timeseriesDataPerSlugJson"]
                        
                        # Process each asset
                        for santiment_asset, symbol in asset_map.items():
                            if santiment_asset in metric_data and metric_data[santiment_asset]:
                                try:
                                    timeseries = json.loads(metric_data[santiment_asset])
                                    if timeseries:
                                        latest_value = timeseries[-1].get("value", 0)
                                        result["whale_data"][symbol][metric] = latest_value
                                    else:
                                        result["whale_data"][symbol][metric] = 0
                                except:
                                    result["whale_data"][symbol][metric] = 0
                            else:
                                result["whale_data"][symbol][metric] = 0
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"Santiment metric {metric} failed: {e}")
                continue
        
        return result
    
    def get_cost_estimate(self):
        """Estimate API costs - already paid"""
        return 0.0  # APIs already paid, no additional cost to AgentCeli
        
        try:
            for symbol in symbols:
                response = requests.get(f"{self.base_url}/products/{symbol}/ticker", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    base_symbol = symbol.split('-')[0]
                    
                    result[base_symbol] = {
                        'price': float(data['price']),
                        'volume_24h': float(data['volume']),
                        'change_24h': self._calculate_change(data),
                        'source': 'coinbase_free',
                        'timestamp': datetime.now().isoformat()
                    }
                
                time.sleep(0.1)  # Small delay between requests
                
            return result if result else None
            
        except Exception as e:
            print(f"Coinbase API error: {e}")
            return None
    
    def _calculate_change(self, ticker_data):
        """Calculate 24h percentage change"""
        try:
            current = float(ticker_data['price'])
            # Coinbase doesn't provide 24h open, so we use a rough estimate
            return 0.0  # Would need historical data for accurate calculation
        except:
            return 0.0
    
    def _rate_limit(self):
        """Ensure rate limiting"""
        now = time.time()
        if now - self.last_request < self.rate_limit:
            time.sleep(self.rate_limit - (now - self.last_request))
        self.last_request = time.time()
    
    def get_cost_estimate(self):
        """Coinbase public API is free"""
        return 0.0

class AlphaVantageAPI(DataSourceInterface):
    """Alpha Vantage API for crypto and forex data"""
    
    def __init__(self, config=None):
        self.base_url = "https://www.alphavantage.co/query"
        self.config = config or {}
        self.api_key = self.config.get('api_key')
        self.rate_limit = 12  # 5 calls per minute for free tier
        self.last_request = 0
        
    def connect(self):
        """Test Alpha Vantage API connection"""
        if not self.api_key:
            return False
            
        try:
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': 'IBM',
                'apikey': self.api_key
            }
            response = requests.get(self.base_url, params=params, timeout=5)
            return response.status_code == 200 and 'Error Message' not in response.text
        except:
            return False
    
    def fetch_data(self):
        """Fetch crypto data from Alpha Vantage"""
        if not self.api_key:
            return None
            
        self._rate_limit()
        
        try:
            # Alpha Vantage uses different function for crypto
            symbols = ['BTC', 'ETH']  # Limited crypto support
            result = {}
            
            for symbol in symbols:
                params = {
                    'function': 'CURRENCY_EXCHANGE_RATE',
                    'from_currency': symbol,
                    'to_currency': 'USD',
                    'apikey': self.api_key
                }
                
                response = requests.get(self.base_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'Realtime Currency Exchange Rate' in data:
                        rate_data = data['Realtime Currency Exchange Rate']
                        
                        result[symbol] = {
                            'price': float(rate_data['5. Exchange Rate']),
                            'volume_24h': 0,  # Not available
                            'change_24h': 0,  # Not available in this endpoint
                            'source': 'alphavantage_paid',
                            'timestamp': rate_data['6. Last Refreshed']
                        }
                
                time.sleep(12)  # Rate limit for free tier
            
            return result if result else None
            
        except Exception as e:
            print(f"Alpha Vantage API error: {e}")
            return None
    
    def _rate_limit(self):
        """Ensure rate limiting"""
        now = time.time()
        if now - self.last_request < self.rate_limit:
            time.sleep(self.rate_limit - (now - self.last_request))
        self.last_request = time.time()
    
    def get_cost_estimate(self):
        """Alpha Vantage free tier: 5 calls/minute, 500 calls/day"""
        return 0.0  # Free tier, but limited

class DataSourceManager:
    """Manages all data sources for AgentCeli"""
    
    def __init__(self):
        self.sources = {}
        self.active_sources = []
        self.source_classes = {
            'kraken': KrakenAPI,
            'coinbase_advanced': CoinbaseAdvancedAPI,
            'alphavantage': AlphaVantageAPI
        }
        
    def register_source(self, name, source_class):
        """Register a new data source class"""
        self.source_classes[name] = source_class
        print(f"✅ Registered data source: {name}")
    
    def add_source(self, name, source_type, config=None):
        """Add and configure a data source"""
        if source_type not in self.source_classes:
            print(f"❌ Unknown source type: {source_type}")
            return False
        
        try:
            source_class = self.source_classes[source_type]
            source_instance = source_class(config)
            
            # Test connection
            if source_instance.connect():
                self.sources[name] = source_instance
                print(f"✅ Added data source: {name}")
                return True
            else:
                print(f"❌ Failed to connect to {name}")
                return False
                
        except Exception as e:
            print(f"❌ Error adding source {name}: {e}")
            return False
    
    def enable_source(self, name):
        """Enable a data source"""
        if name in self.sources and name not in self.active_sources:
            self.active_sources.append(name)
            print(f"✅ Enabled data source: {name}")
        else:
            print(f"❌ Cannot enable source: {name}")
    
    def disable_source(self, name):
        """Disable a data source"""
        if name in self.active_sources:
            self.active_sources.remove(name)
            print(f"⏹️ Disabled data source: {name}")
    
    def fetch_all_data(self):
        """Fetch data from all active sources"""
        all_data = {}
        total_cost = 0.0
        
        for source_name in self.active_sources:
            if source_name in self.sources:
                try:
                    source = self.sources[source_name]
                    data = source.fetch_data()
                    
                    if data:
                        all_data[source_name] = data
                        total_cost += source.get_cost_estimate()
                        print(f"✅ Fetched data from {source_name}")
                    else:
                        print(f"⚠️ No data from {source_name}")
                        
                except Exception as e:
                    print(f"❌ Error fetching from {source_name}: {e}")
        
        return {
            'sources': all_data,
            'total_cost': total_cost,
            'timestamp': datetime.now().isoformat(),
            'active_sources': len(self.active_sources)
        }
    
    def get_source_status(self):
        """Get status of all sources"""
        status = {
            'total_sources': len(self.sources),
            'active_sources': len(self.active_sources),
            'available_types': list(self.source_classes.keys()),
            'sources': {}
        }
        
        for name, source in self.sources.items():
            status['sources'][name] = {
                'active': name in self.active_sources,
                'connected': source.connect(),
                'cost_estimate': source.get_cost_estimate()
            }
        
        return status
    
    def add_default_sources(self):
        """Add commonly used free data sources"""
        print("🔌 Adding default data sources...")
        
        # Add Kraken
        self.add_source('kraken', 'kraken')
        
        # Add Coinbase Advanced
        self.add_source('coinbase_advanced', 'coinbase_advanced')
        
        # Enable free sources by default
        self.enable_source('kraken')
        self.enable_source('coinbase_advanced')
        
        print("✅ Default sources added and enabled")

# Example usage and testing
if __name__ == "__main__":
    # Initialize manager
    manager = DataSourceManager()
    
    # Add default sources
    manager.add_default_sources()
    
    # Test data fetching
    print("\n🧪 Testing data sources...")
    data = manager.fetch_all_data()
    
    print(f"\n📊 Results:")
    print(f"Active sources: {data['active_sources']}")
    print(f"Total cost: ${data['total_cost']:.4f}")
    
    for source_name, source_data in data['sources'].items():
        print(f"\n{source_name}:")
        for symbol, info in source_data.items():
            print(f"  {symbol}: ${info['price']:.2f}")
    
    # Show status
    print(f"\n📈 Source Status:")
    status = manager.get_source_status()
    print(json.dumps(status, indent=2))