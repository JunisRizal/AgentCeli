#!/usr/bin/env python3
"""
AgentCeli Data Bridge for Agents-main3
Copy this file to your Agents-main3 repository to access AgentCeli's crypto data
"""

import requests
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import sqlite3

class AgentCeliBridge:
    def __init__(self, agentceli_path="/Users/julius/Desktop/AgentCeli"):
        """Initialize bridge to AgentCeli data"""
        self.agentceli_path = Path(agentceli_path)
        self.api_url = "http://localhost:8080"
        self.data_path = self.agentceli_path / "correlation_data"
        self.db_path = self.data_path / "hybrid_crypto_data.db"
        
        print("🌉 AgentCeli Bridge initialized for Agents-main3")
    
    def get_live_prices(self):
        """Get current crypto prices from AgentCeli"""
        try:
            # Method 1: API (fastest)
            response = requests.get(f"{self.api_url}/api/prices", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Live prices: BTC=${data['btc']:,.2f}, ETH=${data['eth']:,.2f}")
                return data
        except Exception as e:
            print(f"⚠️ API failed: {e}")
        
        # Method 2: File fallback
        try:
            json_file = self.data_path / "hybrid_latest.json"
            if json_file.exists():
                with open(json_file) as f:
                    data = json.load(f)
                print("✅ Prices loaded from file")
                return data
        except Exception as e:
            print(f"❌ File access failed: {e}")
        
        return None
    
    def get_historical_data(self, hours=24, symbols=['BTC', 'ETH', 'SOL', 'XRP']):
        """Get historical data for analysis"""
        try:
            if not self.db_path.exists():
                print("⚠️ No historical database found")
                return None
            
            conn = sqlite3.connect(self.db_path)
            
            # Get data for specified symbols and timeframe
            placeholders = ','.join(['?' for _ in symbols])
            query = f"""
            SELECT 
                timestamp,
                symbol,
                price_usd as price,
                volume_24h,
                change_24h,
                fear_greed
            FROM live_prices 
            WHERE symbol IN ({placeholders})
            AND timestamp > datetime('now', '-{hours} hours')
            ORDER BY timestamp DESC
            """
            
            df = pd.read_sql_query(query, conn, params=symbols)
            conn.close()
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                print(f"✅ Historical data: {len(df)} records from last {hours} hours")
                return df
            else:
                print("⚠️ No historical data available")
                return None
                
        except Exception as e:
            print(f"❌ Database error: {e}")
            return None
    
    def get_market_summary(self):
        """Get market overview and sentiment data"""
        try:
            response = requests.get(f"{self.api_url}/api/market", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ Market summary retrieved")
                return data
        except Exception as e:
            print(f"❌ Market data failed: {e}")
        
        return None
    
    def export_for_analysis(self, filename="agentceli_data_export.json"):
        """Export current data for your analysis"""
        try:
            # Get comprehensive data
            live_prices = self.get_live_prices()
            historical_data = self.get_historical_data(hours=168)  # 7 days
            market_summary = self.get_market_summary()
            
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "source": "AgentCeli",
                "live_prices": live_prices,
                "market_summary": market_summary,
                "historical_data": historical_data.to_dict('records') if historical_data is not None else None
            }
            
            # Save to Agents-main3 directory
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            print(f"✅ Data exported to {filename}")
            return export_data
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return None
    
    def monitor_connection(self):
        """Test connection to AgentCeli system"""
        print("🔍 Testing AgentCeli connection...")
        
        # Test API
        try:
            response = requests.get(f"{self.api_url}/api/status", timeout=3)
            if response.status_code == 200:
                print("✅ HTTP API: Connected")
                api_ok = True
            else:
                print("❌ HTTP API: Failed")
                api_ok = False
        except:
            print("❌ HTTP API: Not available")
            api_ok = False
        
        # Test files
        json_file = self.data_path / "hybrid_latest.json"
        csv_file = self.data_path / "hybrid_latest.csv"
        
        files_ok = json_file.exists() and csv_file.exists()
        if files_ok:
            print("✅ Data files: Available")
        else:
            print("❌ Data files: Missing")
        
        # Test database
        db_ok = self.db_path.exists()
        if db_ok:
            print("✅ Database: Available")
        else:
            print("❌ Database: Missing")
        
        overall_status = api_ok or files_ok or db_ok
        print(f"🔗 Overall connection: {'✅ OK' if overall_status else '❌ FAILED'}")
        
        return overall_status

def main():
    """Demo usage for Agents-main3"""
    print("🚀 AgentCeli Bridge Demo for Agents-main3")
    print("=" * 50)
    
    # Initialize bridge
    bridge = AgentCeliBridge()
    
    # Test connection
    if not bridge.monitor_connection():
        print("❌ Cannot connect to AgentCeli - make sure it's running!")
        return
    
    # Get live data
    live_data = bridge.get_live_prices() 
    if live_data:
        print(f"\n💰 Current Prices:")
        print(f"  BTC: ${live_data.get('btc', 0):,.2f}")
        print(f"  ETH: ${live_data.get('eth', 0):,.2f}")
        print(f"  SOL: ${live_data.get('sol', 0):,.2f}")
        print(f"  XRP: ${live_data.get('xrp', 0):,.4f}")
        print(f"  Fear & Greed: {live_data.get('fear_greed', 'N/A')}")
    
    # Get historical analysis data
    historical = bridge.get_historical_data(hours=24)
    if historical is not None:
        print(f"\n📊 Historical Analysis:")
        btc_data = historical[historical['symbol'] == 'BTC']
        if len(btc_data) > 0:
            price_change = ((btc_data['price'].iloc[0] - btc_data['price'].iloc[-1]) / btc_data['price'].iloc[-1]) * 100
            print(f"  BTC 24h change: {price_change:.2f}%")
            print(f"  Records available: {len(historical)} data points")
    
    # Export for your analysis
    export_data = bridge.export_for_analysis("agents_main3_crypto_data.json")
    if export_data:
        print(f"\n📁 Data exported for Agents-main3 analysis")
    
    print(f"\n💡 Integration Examples:")
    print(f"  # In your Agents-main3 code:")
    print(f"  from agentceli_bridge_for_agents_main3 import AgentCeliBridge")
    print(f"  bridge = AgentCeliBridge()")
    print(f"  data = bridge.get_live_prices()")

if __name__ == "__main__":
    main()