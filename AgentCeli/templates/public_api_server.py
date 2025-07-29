#!/usr/bin/env python3
"""
Public API Server for AgentCeli
CORS-enabled server for external website integration
"""

from flask import Flask, jsonify
from flask_cors import CORS
import requests
import json
from pathlib import Path

app = Flask(__name__)
CORS(app, origins=["*"])  # Allow all origins - configure as needed

BASE_DIR = Path(__file__).parent

def get_global_market_cap():
    """Get total cryptocurrency market cap from CoinGecko"""
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/global",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data["data"]["total_market_cap"]["usd"]
    except:
        pass
    return None

@app.route('/api/crypto/latest', methods=['GET'])
def get_latest_crypto():
    """Get latest crypto data with CORS enabled"""
    try:
        # Read from AgentCeli data files
        json_file = BASE_DIR / "correlation_data" / "hybrid_latest.json"
        
        if json_file.exists():
            with open(json_file) as f:
                data = json.load(f)
            
            # Simplified response for websites
            response = {
                "success": True,
                "source": "AgentCeli",
                "timestamp": data["timestamp"],
                "prices": {
                    "BTC": {
                        "price": data["live_prices"]["binance"]["BTCUSDT"]["price"],
                        "change_24h": data["live_prices"]["binance"]["BTCUSDT"]["change_24h"]
                    },
                    "ETH": {
                        "price": data["live_prices"]["binance"]["ETHUSDT"]["price"],
                        "change_24h": data["live_prices"]["binance"]["ETHUSDT"]["change_24h"]
                    },
                    "SOL": {
                        "price": data["live_prices"]["binance"]["SOLUSDT"]["price"],
                        "change_24h": data["live_prices"]["binance"]["SOLUSDT"]["change_24h"]
                    },
                    "XRP": {
                        "price": data["live_prices"]["binance"]["XRPUSDT"]["price"],
                        "change_24h": data["live_prices"]["binance"]["XRPUSDT"]["change_24h"]
                    }
                },
                "market": {
                    "fear_greed_index": int(data["fear_greed"]["value"]),
                    "fear_greed_label": data["fear_greed"]["value_classification"],
                    "total_crypto_market_cap": get_global_market_cap(),
                    "individual_market_caps": {
                        "BTC": data["sources"]["coingecko"]["bitcoin"]["usd_market_cap"],
                        "ETH": data["sources"]["coingecko"]["ethereum"]["usd_market_cap"],
                        "SOL": data["sources"]["coingecko"]["solana"]["usd_market_cap"],
                        "XRP": data["sources"]["coingecko"]["ripple"]["usd_market_cap"]
                    },
                    "agentceli_tracked_total": (
                        data["sources"]["coingecko"]["bitcoin"]["usd_market_cap"] +
                        data["sources"]["coingecko"]["ethereum"]["usd_market_cap"] +
                        data["sources"]["coingecko"]["solana"]["usd_market_cap"] +
                        data["sources"]["coingecko"]["ripple"]["usd_market_cap"]
                    )
                }
            }
            
            return jsonify(response)
        else:
            return jsonify({
                "success": False,
                "error": "No data available"
            }), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/crypto/prices', methods=['GET'])
def get_simple_prices():
    """Get simple price data - just numbers"""
    try:
        json_file = BASE_DIR / "correlation_data" / "hybrid_latest.json"
        
        if json_file.exists():
            with open(json_file) as f:
                data = json.load(f)
            
            return jsonify({
                "btc": data["live_prices"]["binance"]["BTCUSDT"]["price"],
                "eth": data["live_prices"]["binance"]["ETHUSDT"]["price"], 
                "sol": data["live_prices"]["binance"]["SOLUSDT"]["price"],
                "xrp": data["live_prices"]["binance"]["XRPUSDT"]["price"],
                "fear_greed": int(data["fear_greed"]["value"]),
                "timestamp": data["timestamp"]
            })
        else:
            return jsonify({"error": "No data"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "ok",
        "service": "AgentCeli Public API",
        "timestamp": "live"
    })

if __name__ == '__main__':
    print("🌍 Starting AgentCeli Public API Server...")
    print("📡 CORS enabled for all origins")
    print("🔗 Your website can access:")
    print("   - http://localhost:8082/api/crypto/latest")
    print("   - http://localhost:8082/api/crypto/prices")
    
    app.run(host='0.0.0.0', port=8082, debug=False)