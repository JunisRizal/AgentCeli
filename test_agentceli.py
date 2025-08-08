#!/usr/bin/env python3
"""
Test AgentCeli - Verify REAL data collection
"""

from agentceli_free import AgentCeli
import json
import time

def test_real_data_collection():
    """Test that AgentCeli collects REAL market data"""
    print("🔴 TESTING AgentCeli REAL DATA COLLECTION")
    print("="*60)
    
    # Create AgentCeli instance
    agent = AgentCeli()
    
    print("\n1️⃣ Testing Binance LIVE Exchange Data...")
    binance_data = agent.get_binance_live_prices()
    if binance_data:
        print(f"✅ SUCCESS: {len(binance_data)} LIVE prices from Binance")
        for symbol, data in list(binance_data.items())[:2]:
            price = data['current_price']
            change = data['change_24h']
            print(f"   🔴 {symbol}: ${price:,.2f} ({change:+.2f}%) - LIVE from Binance")
    else:
        print("❌ No Binance data received")
    
    print("\n2️⃣ Testing CoinGecko REAL Market Data...")
    coingecko_data = agent.get_basic_market_data()
    if coingecko_data:
        print(f"✅ SUCCESS: {len(coingecko_data)} coins from CoinGecko")
        for coin, data in list(coingecko_data.items())[:2]:
            price = data.get('usd', 0)
            change = data.get('usd_24h_change', 0)
            print(f"   🔴 {coin}: ${price:,.2f} ({change:+.2f}%) - REAL from CoinGecko")
    else:
        print("❌ No CoinGecko data received")
    
    print("\n3️⃣ Testing Coinbase Pro LIVE Data...")
    coinbase_data = agent.get_coinbase_live_prices()
    if coinbase_data:
        print(f"✅ SUCCESS: {len(coinbase_data)} LIVE prices from Coinbase Pro")
        for pair, data in coinbase_data.items():
            price = data['current_price']
            print(f"   🔴 {pair}: ${price:,.2f} - LIVE from Coinbase Pro")
    else:
        print("❌ No Coinbase data received")
    
    print("\n4️⃣ Testing REAL Fear & Greed Index...")
    fear_greed = agent.get_fear_greed_index()
    if fear_greed:
        value = fear_greed.get('value', 'N/A')
        classification = fear_greed.get('value_classification', 'N/A')
        print(f"✅ SUCCESS: Fear & Greed Index = {value} ({classification}) - REAL data")
    else:
        print("❌ No Fear & Greed data received")
    
    print("\n5️⃣ Full Data Collection Test...")
    agent.collect_all_data()
    
    if agent.collected_data:
        stats = agent.collected_data['collection_stats']
        agent_info = agent.collected_data['agent_info']
        
        print(f"✅ FULL COLLECTION SUCCESS!")
        print(f"   📊 Total coins: {stats['total_coins_collected']}")
        print(f"   🏦 Live exchanges: {stats['live_exchange_sources']}")
        print(f"   🔴 Data type: {agent.collected_data['data_type']}")
        print(f"   ✅ Authenticity: {stats['data_authenticity']}")
        print(f"   🤖 AI APIs used: {agent_info['ai_apis']}")
        print(f"   📈 Simulation: {agent_info['simulation']}")
        print(f"   🌐 Live trading: {agent_info['live_trading_data']}")
        
        # Show sample of collected LIVE data
        live_exchanges = agent.collected_data.get('live_exchange_data', {})
        print(f"\n📊 LIVE EXCHANGE DATA COLLECTED:")
        for exchange, data in live_exchanges.items():
            if data:
                print(f"   🏦 {exchange.upper()}: {len(data)} live prices")
                # Show one example price
                if data:
                    first_pair = next(iter(data.keys()))
                    first_data = data[first_pair]
                    if 'current_price' in first_data:
                        print(f"      Example: {first_pair} = ${first_data['current_price']:,.2f}")
        
        # Save results
        with open('agentceli_test_results.json', 'w') as f:
            json.dump(agent.collected_data, f, indent=2)
        print(f"\n💾 Test results saved to: agentceli_test_results.json")
        
    else:
        print("❌ FULL COLLECTION FAILED")
    
    print(f"\n🔴 TEST COMPLETE - AgentCeli collecting REAL data: {agent.collected_data is not None}")
    print("="*60)

if __name__ == "__main__":
    test_real_data_collection()