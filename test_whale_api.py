#!/usr/bin/env python3
"""
Test script for Whale Alert API
"""

import sys
if "/Users/julius/Desktop/AgentCeli" in sys.path:
    sys.path.remove("/Users/julius/Desktop/AgentCeli")

import requests as http_requests
import json

def test_whale_alert_api(api_key=None):
    """Test the Whale Alert API status endpoint"""
    
    if not api_key:
        print("⚠️ No API key provided. Testing without authentication.")
        print("Usage: python3 test_whale_api.py YOUR_API_KEY")
        print()
    
    # Test status endpoint
    url = "https://api.whale-alert.io/v1/status"
    params = {}
    
    if api_key:
        params['api_key'] = api_key
    
    try:
        print(f"🌐 Testing: {url}")
        response = http_requests.get(url, params=params, timeout=10)
        
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response:")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Request failed: {e}")

if __name__ == "__main__":
    api_key = sys.argv[1] if len(sys.argv) > 1 else None
    test_whale_alert_api(api_key)