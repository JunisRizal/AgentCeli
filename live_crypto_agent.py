#!/usr/bin/env python3
"""
Live Kryptowährungs-Daten-Agent
Sammelt und stellt Live-Daten für 10-15 Coins bereit
"""

import requests
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from pathlib import Path
import schedule
from flask import Flask, jsonify, render_template_string

class LiveCryptoAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        
        # Session mit optionalem API-Key
        self.session = requests.Session()
        headers = {
            'accept': 'application/json',
            'User-Agent': 'LiveCryptoAgent/1.0'
        }
        
        if api_key:
            headers['x-cg-demo-api-key'] = api_key
            print("🔑 API-Key konfiguriert für erweiterte Limits")
        else:
            print("🆓 Kostenlose API ohne Anmeldung verwendet")
            
        self.session.headers.update(headers)
        
        # Top 15 Kryptowährungen
        self.target_coins = [
            'bitcoin', 'ethereum', 'tether', 'bnb', 'solana',
            'xrp', 'usd-coin', 'cardano', 'dogecoin', 'avalanche-2',
            'tron', 'chainlink', 'polkadot', 'polygon-ecosystem-token', 'shiba-inu'
        ]
        
        # Live-Daten-Speicher
        self.live_data = {}
        self.last_update = None
        self.update_interval = 60  # Sekunden
        self.is_running = False
        
        # Ausgabeordner
        self.output_dir = Path("live_crypto_data")
        self.output_dir.mkdir(exist_ok=True)
        
        # Flask App für Web-Interface
        self.app = Flask(__name__)
        self.setup_routes()
    
    def get_live_prices(self) -> Optional[Dict]:
        """Holt aktuelle Preise für alle Ziel-Coins"""
        try:
            # CoinGecko Simple Price API - bis zu 250 Coins pro Anfrage
            coin_ids = ','.join(self.target_coins)
            
            params = {
                'ids': coin_ids,
                'vs_currencies': 'usd,eur,btc',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true',
                'include_last_updated_at': 'true'
            }
            
            response = self.session.get(f"{self.base_url}/simple/price", params=params)
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ Live-Daten für {len(data)} Coins abgerufen")
            return data
            
        except requests.RequestException as e:
            print(f"❌ Fehler beim Abrufen der Live-Daten: {e}")
            return None
    
    def get_detailed_market_data(self) -> Optional[List[Dict]]:
        """Holt detaillierte Marktdaten"""
        try:
            coin_ids = ','.join(self.target_coins)
            
            params = {
                'ids': coin_ids,
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': 15,
                'page': 1,
                'sparkline': 'false',
                'price_change_percentage': '1h,24h,7d'
            }
            
            response = self.session.get(f"{self.base_url}/coins/markets", params=params)
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ Detaillierte Marktdaten für {len(data)} Coins abgerufen")
            return data
            
        except requests.RequestException as e:
            print(f"❌ Fehler beim Abrufen der Marktdaten: {e}")
            return None
    
    def process_live_data(self, price_data: Dict, market_data: List[Dict]) -> Dict:
        """Verarbeitet und kombiniert Live-Daten"""
        processed_data = {
            'timestamp': datetime.now().isoformat(),
            'update_interval_seconds': self.update_interval,
            'total_coins': len(self.target_coins),
            'coins': {},
            'market_summary': {
                'total_market_cap_usd': 0,
                'total_volume_24h_usd': 0,
                'average_24h_change': 0
            }
        }
        
        # Erstelle Lookup für Marktdaten
        market_lookup = {coin['id']: coin for coin in market_data} if market_data else {}
        
        total_change = 0
        valid_changes = 0
        
        for coin_id in self.target_coins:
            if coin_id in price_data:
                price_info = price_data[coin_id]
                market_info = market_lookup.get(coin_id, {})
                
                coin_data = {
                    'id': coin_id,
                    'name': market_info.get('name', coin_id.title()),
                    'symbol': market_info.get('symbol', '').upper(),
                    'current_price': {
                        'usd': price_info.get('usd'),
                        'eur': price_info.get('eur'),
                        'btc': price_info.get('btc')
                    },
                    'market_cap_usd': price_info.get('usd_market_cap'),
                    'volume_24h_usd': price_info.get('usd_24h_vol'),
                    'price_change_24h_percent': price_info.get('usd_24h_change'),
                    'price_change_1h_percent': market_info.get('price_change_percentage_1h_in_currency'),
                    'price_change_7d_percent': market_info.get('price_change_percentage_7d_in_currency'),
                    'market_cap_rank': market_info.get('market_cap_rank'),
                    'last_updated': price_info.get('last_updated_at'),
                    'image': market_info.get('image')
                }
                
                processed_data['coins'][coin_id] = coin_data
                
                # Summiere für Marktübersicht
                if coin_data['market_cap_usd']:
                    processed_data['market_summary']['total_market_cap_usd'] += coin_data['market_cap_usd']
                if coin_data['volume_24h_usd']:
                    processed_data['market_summary']['total_volume_24h_usd'] += coin_data['volume_24h_usd']
                if coin_data['price_change_24h_percent'] is not None:
                    total_change += coin_data['price_change_24h_percent']
                    valid_changes += 1
        
        if valid_changes > 0:
            processed_data['market_summary']['average_24h_change'] = total_change / valid_changes
        
        return processed_data
    
    def update_live_data(self):
        """Aktualisiert Live-Daten"""
        print(f"🔄 Aktualisiere Live-Daten um {datetime.now().strftime('%H:%M:%S')}")
        
        # Hole Daten
        price_data = self.get_live_prices()
        market_data = self.get_detailed_market_data()
        
        if price_data:
            # Verarbeite Daten
            self.live_data = self.process_live_data(price_data, market_data)
            self.last_update = datetime.now()
            
            # Speichere JSON
            self.save_live_data()
            
            print(f"✅ Live-Daten aktualisiert: {len(self.live_data['coins'])} Coins")
        else:
            print("❌ Live-Daten-Update fehlgeschlagen")
    
    def save_live_data(self):
        """Speichert aktuelle Live-Daten"""
        if not self.live_data:
            return
        
        # Aktuelle Daten
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        current_file = self.output_dir / "current_live_data.json"
        archive_file = self.output_dir / f"live_data_{timestamp}.json"
        
        try:
            # Speichere aktuelle Daten
            with open(current_file, 'w', encoding='utf-8') as f:
                json.dump(self.live_data, f, indent=2, ensure_ascii=False)
            
            # Archiviere Daten (alle 10 Minuten)
            if datetime.now().minute % 10 == 0:
                with open(archive_file, 'w', encoding='utf-8') as f:
                    json.dump(self.live_data, f, indent=2, ensure_ascii=False)
                print(f"📁 Daten archiviert: {archive_file}")
                
        except Exception as e:
            print(f"❌ Fehler beim Speichern: {e}")
    
    def start_live_monitoring(self):
        """Startet kontinuierliches Live-Monitoring"""
        if self.is_running:
            print("⚠️ Live-Monitoring läuft bereits")
            return
        
        self.is_running = True
        print(f"🚀 Live-Monitoring gestartet (Update alle {self.update_interval}s)")
        
        # Erste Aktualisierung
        self.update_live_data()
        
        # Schedule für regelmäßige Updates
        schedule.every(self.update_interval).seconds.do(self.update_live_data)
        
        # Background Thread für Scheduler
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        print("✅ Live-Monitoring aktiv")
    
    def stop_live_monitoring(self):
        """Stoppt Live-Monitoring"""
        self.is_running = False
        schedule.clear()
        print("🛑 Live-Monitoring gestoppt")
    
    def get_current_data(self) -> Dict:
        """Gibt aktuelle Live-Daten zurück"""
        if not self.live_data:
            return {"error": "Keine Live-Daten verfügbar"}
        
        return {
            "data": self.live_data,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "status": "active" if self.is_running else "stopped"
        }
    
    def setup_routes(self):
        """Konfiguriert Flask-Routen für Web-Interface"""
        
        @self.app.route('/')
        def dashboard():
            """Web-Dashboard für Live-Daten"""
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Live Crypto Dashboard</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                    .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                    .summary { background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                    .coins-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }
                    .coin-card { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                    .coin-header { display: flex; align-items: center; margin-bottom: 10px; }
                    .coin-icon { width: 32px; height: 32px; margin-right: 10px; border-radius: 50%; }
                    .price { font-size: 24px; font-weight: bold; color: #2c3e50; }
                    .change { padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold; }
                    .positive { background: #27ae60; }
                    .negative { background: #e74c3c; }
                    .neutral { background: #95a5a6; }
                    .last-update { color: #7f8c8d; font-size: 12px; }
                    .auto-refresh { margin: 10px 0; }
                </style>
                <script>
                    function refreshData() {
                        fetch('/api/data')
                            .then(response => response.json())
                            .then(data => {
                                if (data.data && data.data.coins) {
                                    updateDashboard(data);
                                }
                            })
                            .catch(error => console.error('Error:', error));
                    }
                    
                    function updateDashboard(data) {
                        document.getElementById('last-update').textContent = 
                            'Letztes Update: ' + new Date(data.last_update).toLocaleString();
                        
                        const summary = data.data.market_summary;
                        document.getElementById('total-cap').textContent = 
                            '$' + (summary.total_market_cap_usd / 1e12).toFixed(2) + 'T';
                        document.getElementById('total-volume').textContent = 
                            '$' + (summary.total_volume_24h_usd / 1e9).toFixed(2) + 'B';
                        document.getElementById('avg-change').textContent = 
                            summary.average_24h_change.toFixed(2) + '%';
                    }
                    
                    // Auto-refresh alle 60 Sekunden
                    setInterval(refreshData, 60000);
                    
                    // Initial load
                    window.onload = refreshData;
                </script>
            </head>
            <body>
                <div class="header">
                    <h1>🚀 Live Crypto Dashboard</h1>
                    <p>Real-time Kryptowährungsdaten für Top 15 Coins</p>
                    <div class="auto-refresh">
                        <span id="last-update">Lade Daten...</span>
                    </div>
                </div>
                
                <div class="summary">
                    <h3>📊 Marktübersicht</h3>
                    <p><strong>Gesamte Marktkapitalisierung:</strong> <span id="total-cap">-</span></p>
                    <p><strong>24h Handelsvolumen:</strong> <span id="total-volume">-</span></p>
                    <p><strong>Durchschnittliche 24h Änderung:</strong> <span id="avg-change">-</span></p>
                </div>
                
                <div id="coins-container">
                    <p>Lade Live-Daten...</p>
                </div>
            </body>
            </html>
            """
            return html_template
        
        @self.app.route('/api/data')
        def api_data():
            """API-Endpoint für Live-Daten"""
            return jsonify(self.get_current_data())
        
        @self.app.route('/api/coins/<coin_id>')
        def api_coin_data(coin_id):
            """API-Endpoint für einzelnen Coin"""
            if not self.live_data or coin_id not in self.live_data.get('coins', {}):
                return jsonify({"error": "Coin nicht gefunden"}), 404
            
            return jsonify({
                "coin": self.live_data['coins'][coin_id],
                "last_update": self.last_update.isoformat() if self.last_update else None
            })
    
    def start_web_server(self, host='0.0.0.0', port=5000):
        """Startet Web-Server für Dashboard"""
        print(f"🌐 Web-Dashboard startet auf http://{host}:{port}")
        self.app.run(host=host, port=port, debug=False)

def main():
    """Hauptfunktion"""
    print("🚀 Live Kryptowährungs-Daten-Agent")
    print("=" * 50)
    
    # Optional: API-Key aus Umgebungsvariable oder Eingabe
    api_key = None  # Für kostenlose Nutzung
    # api_key = input("API-Key (Enter für kostenlose Nutzung): ").strip() or None
    
    # Agent erstellen
    agent = LiveCryptoAgent(api_key=api_key)
    
    print("\n📋 Verfügbare Optionen:")
    print("1. Live-Monitoring starten")
    print("2. Einmalige Datenabfrage")
    print("3. Web-Dashboard starten")
    print("4. Beides (Monitoring + Dashboard)")
    
    choice = input("\nWählen Sie eine Option (1-4): ").strip()
    
    if choice == "1":
        agent.start_live_monitoring()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            agent.stop_live_monitoring()
            
    elif choice == "2":
        agent.update_live_data()
        if agent.live_data:
            print(f"\n📊 Aktuelle Daten für {len(agent.live_data['coins'])} Coins:")
            for coin_id, data in agent.live_data['coins'].items():
                price = data['current_price']['usd']
                change = data['price_change_24h_percent'] or 0
                print(f"{data['symbol']:>6}: ${price:>10.2f} ({change:+.2f}%)")
                
    elif choice == "3":
        # Einmalige Datenabfrage für Dashboard
        agent.update_live_data()
        agent.start_web_server()
        
    elif choice == "4":
        agent.start_live_monitoring()
        # Kurz warten für erste Daten
        time.sleep(3)
        
        # Web-Server in separatem Thread
        import threading
        web_thread = threading.Thread(target=agent.start_web_server, daemon=True)
        web_thread.start()
        
        print("✅ Live-Monitoring und Web-Dashboard aktiv")
        print("🌐 Dashboard: http://localhost:5000")
        print("📡 API: http://localhost:5000/api/data")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            agent.stop_live_monitoring()
    
    else:
        print("❌ Ungültige Auswahl")

if __name__ == "__main__":
    main()

