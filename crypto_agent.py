#!/usr/bin/env python3
"""Simple cryptocurrency data helper using CoinGecko."""

import requests
from typing import List, Dict, Optional

class CryptoDataAgent:
    """Fetch basic coin lists and historical data."""

    def __init__(self) -> None:
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
        self.session.headers.update({
            "accept": "application/json",
            "User-Agent": "CryptoDataAgent/1.0",
        })

    def get_coins_list(self) -> List[Dict]:
        """Return available coins with IDs."""
        try:
            response = self.session.get(f"{self.base_url}/coins/list")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching coin list: {e}")
            return []

    def get_historical_data(self, coin_id: str, date: str) -> Optional[Dict]:
        """Get historical data for a coin on a given date (dd-mm-yyyy)."""
        try:
            response = self.session.get(
                f"{self.base_url}/coins/{coin_id}/history",
                params={"date": date},
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching historical data: {e}")
            return None

def main() -> None:
    agent = CryptoDataAgent()
    coins = agent.get_coins_list()[:5]
    print(f"Retrieved {len(coins)} coins")
    data = agent.get_historical_data("bitcoin", "30-12-2024")
    if data:
        print("Sample historical data for Bitcoin:")
        print(data.get("market_data", {}))

if __name__ == "__main__":
    main()
