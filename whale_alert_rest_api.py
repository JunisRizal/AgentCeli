#!/usr/bin/env python3
"""
Whale Alert Leviathan REST API Integration for AgentCeli
Fetches whale transaction data via REST API endpoints
"""

import json
import time
import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Import requests properly (avoid local file conflict)
if "/Users/julius/Desktop/AgentCeli" in sys.path:
    sys.path.remove("/Users/julius/Desktop/AgentCeli")

import requests as http_requests

class WhaleAlertRestAPI:
    def __init__(self, config_file="agentceli_config.json", api_key=None):
        self.base_dir = Path(__file__).parent
        self.config = self.load_config(config_file)
        self.api_key = api_key or self.get_api_key_from_config()
        
        # API endpoints
        self.base_url = "https://leviathan.whale-alert.io/v1"
        self.endpoints = {
            "transactions": "/transactions",
            "status": "/status",
            "blockchain": "/blockchain"
        }
        
        # CSV files
        self.transactions_csv = self.base_dir / "whale_transactions_rest.csv"
        
        self.setup_logging()
        self.setup_csv_files()
        
        if not self.api_key:
            self.logger.warning("⚠️ No API key configured. Some endpoints may not work.")
    
    def load_config(self, config_file):
        """Load AgentCeli configuration"""
        try:
            with open(self.base_dir / config_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def get_api_key_from_config(self):
        """Get Whale Alert API key from config"""
        try:
            return self.config.get("data_sources", {}).get("paid_apis", {}).get("whale_alert", {}).get("key")
        except:
            return None
    
    def setup_logging(self):
        """Setup logging"""
        log_file = self.base_dir / "logs" / "whale_alert_rest.log"
        log_file.parent.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - WHALE_REST - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_csv_files(self):
        """Setup CSV files with headers if they don't exist"""
        if not self.transactions_csv.exists():
            with open(self.transactions_csv, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "id", "blockchain", "symbol", "transaction_type", "hash",
                    "from_address", "from_owner", "from_owner_type",
                    "to_address", "to_owner", "to_owner_type",
                    "timestamp", "amount", "amount_usd", "transaction_count"
                ])
            self.logger.info(f"📄 Created transactions CSV: {self.transactions_csv}")
    
    def make_request(self, endpoint, params=None):
        """Make API request with proper authentication"""
        url = f"{self.base_url}{endpoint}"
        
        # Add API key to parameters
        if params is None:
            params = {}
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        try:
            self.logger.info(f"🌐 Making request to: {url}")
            response = http_requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                self.logger.error("🔑 Authentication failed - check your API key")
                return None
            elif response.status_code == 429:
                self.logger.warning("⏱️ Rate limit exceeded")
                return None
            else:
                self.logger.error(f"❌ API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            return None
    
    def get_transactions(self, start_time=None, end_time=None, min_value=None, currency=None, limit=100):
        """Get whale transactions from the API"""
        params = {}
        
        # Time range parameters
        if start_time:
            if isinstance(start_time, datetime):
                params['start'] = int(start_time.timestamp())
            else:
                params['start'] = start_time
        
        if end_time:
            if isinstance(end_time, datetime):
                params['end'] = int(end_time.timestamp())
            else:
                params['end'] = end_time
        
        # Filter parameters
        if min_value:
            params['min_value'] = min_value
        
        if currency:
            params['currency'] = currency
        
        if limit:
            params['limit'] = limit
        
        return self.make_request(self.endpoints["transactions"], params)
    
    def get_recent_transactions(self, hours_back=1, min_value_usd=1000000, currency=None):
        """Get recent whale transactions"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        self.logger.info(f"🐋 Fetching transactions from {start_time} to {end_time}")
        self.logger.info(f"💰 Minimum value: ${min_value_usd:,}")
        if currency:
            self.logger.info(f"🪙 Currency filter: {currency}")
        
        return self.get_transactions(
            start_time=start_time,
            end_time=end_time,
            min_value=min_value_usd,
            currency=currency
        )
    
    def log_transactions_to_csv(self, transactions_data):
        """Log transaction data to CSV"""
        if not transactions_data or 'transactions' not in transactions_data:
            self.logger.warning("No transaction data to log")
            return 0
        
        transactions = transactions_data['transactions']
        logged_count = 0
        
        with open(self.transactions_csv, "a", newline="") as f:
            writer = csv.writer(f)
            
            for tx in transactions:
                try:
                    # Extract transaction details
                    tx_id = tx.get('id', '')
                    blockchain = tx.get('blockchain', '')
                    symbol = tx.get('symbol', '')
                    tx_type = tx.get('transaction_type', '')
                    tx_hash = tx.get('hash', '')
                    
                    # From details
                    from_data = tx.get('from', {})
                    from_address = from_data.get('address', '')
                    from_owner = from_data.get('owner', '')
                    from_owner_type = from_data.get('owner_type', '')
                    
                    # To details
                    to_data = tx.get('to', {})
                    to_address = to_data.get('address', '')
                    to_owner = to_data.get('owner', '')
                    to_owner_type = to_data.get('owner_type', '')
                    
                    # Transaction data
                    timestamp = tx.get('timestamp', '')
                    amount = tx.get('amount', 0)
                    amount_usd = tx.get('amount_usd', 0)
                    tx_count = tx.get('transaction_count', 1)
                    
                    # Write to CSV
                    writer.writerow([
                        tx_id, blockchain, symbol, tx_type, tx_hash,
                        from_address, from_owner, from_owner_type,
                        to_address, to_owner, to_owner_type,
                        timestamp, amount, amount_usd, tx_count
                    ])
                    
                    logged_count += 1
                    
                    # Log significant transactions
                    if amount_usd >= 1000000:  # $1M+
                        self.logger.info(
                            f"🐋 LARGE TX: {amount:,.2f} {symbol} "
                            f"(${amount_usd:,.2f}) on {blockchain} - "
                            f"{from_owner} → {to_owner}"
                        )
                
                except Exception as e:
                    self.logger.error(f"Failed to log transaction: {e}")
        
        self.logger.info(f"📊 Logged {logged_count} transactions to CSV")
        return logged_count
    
    def get_api_status(self):
        """Check API status and limits"""
        return self.make_request(self.endpoints["status"])
    
    def get_supported_blockchains(self):
        """Get list of supported blockchains"""
        return self.make_request(self.endpoints["blockchain"])
    
    def run_collection_cycle(self, hours_back=1, min_value_usd=1000000, currency=None):
        """Run a complete data collection cycle"""
        self.logger.info("🚀 Starting Whale Alert REST API collection cycle")
        
        # Check API status first
        status = self.get_api_status()
        if status:
            self.logger.info(f"📡 API Status: {status}")
        
        # Fetch recent transactions
        transactions = self.get_recent_transactions(hours_back, min_value_usd, currency)
        
        if transactions:
            # Log to CSV
            count = self.log_transactions_to_csv(transactions)
            
            # Create summary
            summary = {
                "timestamp": datetime.now().isoformat(),
                "transactions_collected": count,
                "time_range_hours": hours_back,
                "min_value_usd": min_value_usd,
                "api_status": status
            }
            
            # Save summary
            summary_file = self.base_dir / "whale_alert_rest_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            self.logger.info(f"✅ Collection complete. Summary saved to {summary_file}")
            return summary
        else:
            self.logger.error("❌ Failed to fetch transactions")
            return None

def main():
    """Main execution"""
    collector = WhaleAlertRestAPI()
    
    print("🐋 Whale Alert REST API Collector")
    print("=" * 40)
    
    # Run collection cycle
    result = collector.run_collection_cycle(
        hours_back=24,  # Last 24 hours
        min_value_usd=1000000,  # $1M minimum
        currency="btc"  # Bitcoin only
    )
    
    if result:
        print(f"\n📊 COLLECTION SUMMARY:")
        print(f"  Transactions: {result['transactions_collected']}")
        print(f"  Time Range: {result['time_range_hours']} hours")
        print(f"  Min Value: ${result['min_value_usd']:,}")
        print(f"  Timestamp: {result['timestamp']}")

if __name__ == "__main__":
    main()