#!/usr/bin/env python3
"""
Erweiterter Kryptowährungs-Daten-Agent
Fokus auf JSON-Verarbeitung und Datenanalyse
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from pathlib import Path

class AdvancedCryptoAgent:
    def __init__(self, config_file: str = "config.json"):
        self.config = self.load_config(config_file)
        self.base_url = self.config["api_settings"]["base_url"]
        self.rate_limit = self.config["api_settings"]["rate_limit_delay"]
        
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'application/json',
            'User-Agent': 'AdvancedCryptoAgent/2.0'
        })
        
        # Erstelle Ausgabeordner
        self.output_dir = Path("crypto_data")
        self.output_dir.mkdir(exist_ok=True)
        
    def load_config(self, config_file: str) -> Dict:
        """Lädt Konfiguration aus JSON-Datei"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Konfigurationsdatei {config_file} nicht gefunden. Verwende Standardwerte.")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Standardkonfiguration"""
        return {
            "api_settings": {
                "base_url": "https://api.coingecko.com/api/v3",
                "rate_limit_delay": 1.2,
                "max_days_free_api": 365,
                "default_currency": "usd"
            },
            "target_coins": [
                {"id": "bitcoin", "symbol": "BTC", "name": "Bitcoin", "priority": 1},
                {"id": "ethereum", "symbol": "ETH", "name": "Ethereum", "priority": 2}
            ],
            "output_settings": {
                "save_raw_json": True,
                "save_processed_json": True,
                "create_csv": True
            }
        }
    
    def fetch_json_data(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Generische Methode zum Abrufen von JSON-Daten"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=params or {})
            response.raise_for_status()
            
            json_data = response.json()
            print(f"✅ JSON-Daten von {endpoint} erfolgreich abgerufen")
            return json_data
            
        except requests.RequestException as e:
            print(f"❌ Fehler beim Abrufen von {endpoint}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON-Parsing-Fehler: {e}")
            return None
    
    def process_historical_json(self, coin_id: str, date: str) -> Optional[Dict]:
        """Verarbeitet historische JSON-Daten für einen Coin"""
        endpoint = f"coins/{coin_id}/history"
        params = {"date": date, "localization": "false"}
        
        raw_data = self.fetch_json_data(endpoint, params)
        if not raw_data:
            return None
        
        # JSON-Datenverarbeitung
        processed_data = {
            "metadata": {
                "coin_id": raw_data.get("id"),
                "symbol": raw_data.get("symbol", "").upper(),
                "name": raw_data.get("name"),
                "date": date,
                "processed_at": datetime.now().isoformat(),
                "data_source": "coingecko_api"
            },
            "market_data": self.extract_market_data(raw_data),
            "community_data": self.extract_community_data(raw_data),
            "developer_data": self.extract_developer_data(raw_data),
            "raw_json_size": len(json.dumps(raw_data))
        }
        
        # Speichere sowohl Roh- als auch verarbeitete Daten
        if self.config["output_settings"]["save_raw_json"]:
            self.save_json(raw_data, f"raw_{coin_id}_{date.replace('-', '_')}.json")
        
        if self.config["output_settings"]["save_processed_json"]:
            self.save_json(processed_data, f"processed_{coin_id}_{date.replace('-', '_')}.json")
        
        return processed_data
    
    def extract_market_data(self, raw_json: Dict) -> Dict:
        """Extrahiert Marktdaten aus rohen JSON-Daten"""
        market_data = raw_json.get("market_data", {})
        
        return {
            "current_price": {
                "usd": market_data.get("current_price", {}).get("usd"),
                "eur": market_data.get("current_price", {}).get("eur"),
                "btc": market_data.get("current_price", {}).get("btc")
            },
            "market_cap": {
                "usd": market_data.get("market_cap", {}).get("usd"),
                "eur": market_data.get("market_cap", {}).get("eur")
            },
            "total_volume": {
                "usd": market_data.get("total_volume", {}).get("usd"),
                "eur": market_data.get("total_volume", {}).get("eur")
            },
            "market_cap_rank": raw_json.get("market_cap_rank"),
            "coingecko_rank": raw_json.get("coingecko_rank"),
            "coingecko_score": raw_json.get("coingecko_score")
        }
    
    def extract_community_data(self, raw_json: Dict) -> Dict:
        """Extrahiert Community-Daten aus JSON"""
        community_data = raw_json.get("community_data", {})
        
        return {
            "reddit_subscribers": community_data.get("reddit_subscribers"),
            "reddit_active_48h": community_data.get("reddit_accounts_active_48h"),
            "reddit_posts_48h": community_data.get("reddit_average_posts_48h"),
            "reddit_comments_48h": community_data.get("reddit_average_comments_48h"),
            "facebook_likes": community_data.get("facebook_likes")
        }
    
    def extract_developer_data(self, raw_json: Dict) -> Dict:
        """Extrahiert Entwickler-Daten aus JSON"""
        dev_data = raw_json.get("developer_data", {})
        
        return {
            "github_forks": dev_data.get("forks"),
            "github_stars": dev_data.get("stars"),
            "github_subscribers": dev_data.get("subscribers"),
            "github_total_issues": dev_data.get("total_issues"),
            "github_closed_issues": dev_data.get("closed_issues"),
            "github_commits_4w": dev_data.get("commit_count_4_weeks")
        }
    
    def save_json(self, data: Dict, filename: str):
        """Speichert JSON-Daten mit schöner Formatierung"""
        filepath = self.output_dir / filename
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
            print(f"💾 JSON gespeichert: {filepath}")
        except Exception as e:
            print(f"❌ Fehler beim Speichern von {filename}: {e}")
    
    def create_summary_json(self, processed_data_list: List[Dict]) -> Dict:
        """Erstellt eine Zusammenfassung aller verarbeiteten Daten"""
        summary = {
            "summary_metadata": {
                "total_coins": len(processed_data_list),
                "generated_at": datetime.now().isoformat(),
                "agent_version": "2.0"
            },
            "coins_overview": [],
            "market_summary": {
                "total_market_cap_usd": 0,
                "total_volume_usd": 0,
                "average_price_usd": 0
            }
        }
        
        total_price = 0
        valid_prices = 0
        
        for data in processed_data_list:
            coin_overview = {
                "coin_id": data["metadata"]["coin_id"],
                "symbol": data["metadata"]["symbol"],
                "name": data["metadata"]["name"],
                "price_usd": data["market_data"]["current_price"]["usd"],
                "market_cap_usd": data["market_data"]["market_cap"]["usd"],
                "volume_usd": data["market_data"]["total_volume"]["usd"]
            }
            summary["coins_overview"].append(coin_overview)
            
            # Berechne Gesamtwerte
            if coin_overview["market_cap_usd"]:
                summary["market_summary"]["total_market_cap_usd"] += coin_overview["market_cap_usd"]
            if coin_overview["volume_usd"]:
                summary["market_summary"]["total_volume_usd"] += coin_overview["volume_usd"]
            if coin_overview["price_usd"]:
                total_price += coin_overview["price_usd"]
                valid_prices += 1
        
        if valid_prices > 0:
            summary["market_summary"]["average_price_usd"] = total_price / valid_prices
        
        return summary
    
    def run_batch_analysis(self, date: str = None) -> Dict:
        """Führt Batch-Analyse für alle konfigurierten Coins durch"""
        if not date:
            date = (datetime.now() - timedelta(days=1)).strftime('%d-%m-%Y')
        
        print(f"🚀 Starte Batch-Analyse für {date}")
        print("=" * 60)
        
        processed_data_list = []
        target_coins = self.config["target_coins"]
        
        for i, coin_config in enumerate(target_coins):
            coin_id = coin_config["id"]
            print(f"🔄 [{i+1}/{len(target_coins)}] Verarbeite {coin_config['name']} ({coin_id})")
            
            # Rate limiting
            if i > 0:
                time.sleep(self.rate_limit)
            
            processed_data = self.process_historical_json(coin_id, date)
            if processed_data:
                processed_data_list.append(processed_data)
        
        # Erstelle Zusammenfassung
        summary = self.create_summary_json(processed_data_list)
        self.save_json(summary, f"summary_{date.replace('-', '_')}.json")
        
        # Erstelle CSV wenn gewünscht
        if self.config["output_settings"].get("create_csv", False):
            self.create_csv_export(processed_data_list, date)
        
        print(f"\n✅ Batch-Analyse abgeschlossen! {len(processed_data_list)} Coins verarbeitet.")
        return summary
    
    def create_csv_export(self, processed_data_list: List[Dict], date: str):
        """Exportiert Daten als CSV"""
        try:
            rows = []
            for data in processed_data_list:
                row = {
                    'date': date,
                    'coin_id': data["metadata"]["coin_id"],
                    'symbol': data["metadata"]["symbol"],
                    'name': data["metadata"]["name"],
                    'price_usd': data["market_data"]["current_price"]["usd"],
                    'price_eur': data["market_data"]["current_price"]["eur"],
                    'price_btc': data["market_data"]["current_price"]["btc"],
                    'market_cap_usd': data["market_data"]["market_cap"]["usd"],
                    'volume_usd': data["market_data"]["total_volume"]["usd"],
                    'reddit_subscribers': data["community_data"]["reddit_subscribers"],
                    'github_stars': data["developer_data"]["github_stars"]
                }
                rows.append(row)
            
            df = pd.DataFrame(rows)
            csv_path = self.output_dir / f"crypto_data_{date.replace('-', '_')}.csv"
            df.to_csv(csv_path, index=False)
            print(f"📊 CSV exportiert: {csv_path}")
            
        except Exception as e:
            print(f"❌ Fehler beim CSV-Export: {e}")

def main():
    """Hauptfunktion"""
    agent = AdvancedCryptoAgent()
    
    # Führe Batch-Analyse durch
    summary = agent.run_batch_analysis()
    
    print("\n📋 Zusammenfassung:")
    print(f"Coins verarbeitet: {summary['summary_metadata']['total_coins']}")
    print(f"Gesamte Marktkapitalisierung: ${summary['market_summary']['total_market_cap_usd']:,.2f}")
    print(f"Gesamtes Handelsvolumen: ${summary['market_summary']['total_volume_usd']:,.2f}")
    
    print(f"\n📁 Alle Dateien gespeichert in: {Path('crypto_data').absolute()}")

if __name__ == "__main__":
    main()

