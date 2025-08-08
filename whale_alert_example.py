#!/usr/bin/env python3
"""
Whale Alert Leviathan API Example
Based on the provided example code
"""

import sys
if "/Users/julius/Desktop/AgentCeli" in sys.path:
    sys.path.remove("/Users/julius/Desktop/AgentCeli")

import requests
import json

def get_whale_transactions(api_key, min_value=1000000, currency=None, limit=5):
    """Get whale transactions using the Leviathan API"""
    
    url = "https://leviathan.whale-alert.io/v1/transactions"
    
    params = {
        "api_key": api_key,
        "min_value": min_value,   # nur Transaktionen >1 Mio USD
        "limit": limit            # max. 5 Ergebnisse
    }
    
    if currency:
        params["currency"] = currency  # optional: btc, eth, usdt, usw.
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n🐋 Whale Alert – Top Transaktionen (Min: ${min_value:,}):")
            print("=" * 80)
            
            for tx in data.get("transactions", []):
                timestamp = tx.get('timestamp', 'N/A')
                amount = tx.get('amount', 0)
                symbol = tx.get('symbol', 'N/A')
                from_type = tx.get('from', {}).get('owner_type', 'unknown')
                to_type = tx.get('to', {}).get('owner_type', 'unknown')
                amount_usd = tx.get('amount_usd', 0)
                
                print(f"{timestamp} | {amount:,.2f} {symbol} | ${amount_usd:,.2f} | {from_type} → {to_type}")
            
            return data
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"💥 Request failed: {e}")
        return None

def main():
    """Main execution"""
    if len(sys.argv) < 2:
        print("Usage: python3 whale_alert_example.py YOUR_API_KEY [currency] [min_value]")
        print("Example: python3 whale_alert_example.py abc123 btc 500000")
        return
    
    api_key = sys.argv[1]
    currency = sys.argv[2] if len(sys.argv) > 2 else None
    min_value = int(sys.argv[3]) if len(sys.argv) > 3 else 1000000
    
    print(f"🔑 Using API Key: {api_key[:8]}...")
    if currency:
        print(f"🪙 Currency filter: {currency}")
    print(f"💰 Minimum value: ${min_value:,}")
    
    # Get transactions
    data = get_whale_transactions(api_key, min_value, currency, limit=10)
    
    if data:
        print(f"\n📊 Found {len(data.get('transactions', []))} transactions")
    else:
        print("❌ No data received")

if __name__ == "__main__":
    main()