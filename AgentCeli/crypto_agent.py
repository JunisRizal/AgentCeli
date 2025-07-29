        })
        
    def get_coins_list(self) -> List[Dict]:
        """Holt die Liste aller verfügbaren Coins mit IDs"""
        try:
            response = self.session.get(f"{self.base_url}/coins/list")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Fehler beim Abrufen der Coin-Liste: {e}")
            return []
    
    def get_historical_data(self, coin_id: str, date: str) -> Optional[Dict]:
        """
        Holt historische Daten für einen Coin an einem bestimmten Datum
        
        Args:
            coin_id: CoinGecko Coin ID (z.B. 'bitcoin')
            date: Datum im Format 'dd-mm-yyyy'
        