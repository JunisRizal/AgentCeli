#!/usr/bin/env python3
"""
AgentCeli - Data Collection Agent
Sammelt Kryptowährungs-Daten ohne AI-APIs (nur Internet-Zugang erforderlich)
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

class EnhancedCryptoAgent:
    def __init__(self, coingecko_api_key: Optional[str] = None, 
                 coinglass_api_key: Optional[str] = None,
                 taapi_key: Optional[str] = None):
        
        # API Keys (alle optional)
        self.coingecko_key = coingecko_api_key
        self.coinglass_key = coinglass_api_key
        self.taapi_key = taapi_key
        
        # API URLs
        self.coingecko_url = "https://api.coingecko.com/api/v3"
        self.coinglass_url = "https://open-api-v4.coinglass.com"
        self.taapi_url = "https://api.taapi.io"
        
        # Sessions für verschiedene APIs
        self.setup_sessions()
        
        # Konservative Rate Limits (Anfragen pro Minute)
        self.rate_limits = {
            'coingecko': 30,  # Konservativ (API erlaubt 50)
            'coinglass': 20,  # Konservativ für kostenlose Nutzung
            'taapi': 15       # Sehr konservativ (Free: 5000/Tag = ~3.5/Min)
        }
        
        # Tracking für Rate Limiting
        self.last_requests = {
            'coingecko': [],
            'coinglass': [],
            'taapi': []
        }
        
        # Top 10 Coins (reduziert für weniger API-Calls)
        self.target_coins = [
            'bitcoin', 'ethereum', 'tether', 'bnb', 'solana',
            'xrp', 'usd-coin', 'cardano', 'dogecoin', 'avalanche-2'
        ]
        
        # Daten-Speicher
        self.enhanced_data = {}
        self.last_update = None
        self.update_interval = 120  # 2 Minuten (konservativ)
        self.is_running = False
        
        # Ausgabeordner
        self.output_dir = Path("enhanced_crypto_data")
        self.output_dir.mkdir(exist_ok=True)
        
        # Flask App
        self.app = Flask(__name__)
        self.setup_routes()
    
    def setup_sessions(self):
        """Konfiguriert HTTP-Sessions für verschiedene APIs"""
        
        # CoinGecko Session
        self.cg_session = requests.Session()
        cg_headers = {
            'accept': 'application/json',
            'User-Agent': 'EnhancedCryptoAgent/1.0'
        }
        if self.coingecko_key:
            cg_headers['x-cg-demo-api-key'] = self.coingecko_key
        self.cg_session.headers.update(cg_headers)
        
        # CoinGlass Session
        self.glass_session = requests.Session()
        glass_headers = {
            'accept': 'application/json',
            'User-Agent': 'EnhancedCryptoAgent/1.0'
        }
        if self.coinglass_key:
            glass_headers['coinglassSecret'] = self.coinglass_key
        self.glass_session.headers.update(glass_headers)
        
        # TAAPI Session
        self.taapi_session = requests.Session()
        self.taapi_session.headers.update({
            'accept': 'application/json',
            'User-Agent': 'EnhancedCryptoAgent/1.0'
        })
    
    def check_rate_limit(self, api_name: str) -> bool:
        """Prüft Rate Limit für API"""
        now = time.time()
        minute_ago = now - 60
        
        # Entferne alte Requests
        self.last_requests[api_name] = [
            req_time for req_time in self.last_requests[api_name] 
            if req_time > minute_ago
        ]
        
        # Prüfe Limit
        current_requests = len(self.last_requests[api_name])
        limit = self.rate_limits[api_name]
        
        if current_requests >= limit:
            print(f"⚠️ Rate Limit für {api_name} erreicht ({current_requests}/{limit})")
            return False
        
        return True
    
    def record_request(self, api_name: str):
        """Zeichnet API-Request auf"""
        self.last_requests[api_name].append(time.time())
    
    def safe_api_call(self, api_name: str, session: requests.Session, 
                     url: str, params: Dict = None) -> Optional[Dict]:
        """Sichere API-Anfrage mit Rate Limiting"""
        
        if not self.check_rate_limit(api_name):
            return None
        
        try:
            response = session.get(url, params=params or {})
            response.raise_for_status()
            
            self.record_request(api_name)
            return response.json()
            
        except requests.RequestException as e:
            print(f"❌ {api_name} API Fehler: {e}")
            return None
    
    def get_basic_market_data(self) -> Optional[Dict]:
        """Holt Basis-Marktdaten von CoinGecko"""
        coin_ids = ','.join(self.target_coins)
        
        params = {
            'ids': coin_ids,
            'vs_currencies': 'usd,eur',
            'include_market_cap': 'true',
            'include_24hr_vol': 'true',
            'include_24hr_change': 'true',
            'include_last_updated_at': 'true'
        }
        
        url = f"{self.coingecko_url}/simple/price"
        data = self.safe_api_call('coingecko', self.cg_session, url, params)
        
        if data:
            print(f"✅ Basis-Marktdaten für {len(data)} Coins abgerufen")
        
        return data
    
    def get_global_market_data(self) -> Optional[Dict]:
        """Holt globale Marktdaten (Total Market Cap, etc.)"""
        url = f"{self.coingecko_url}/global"
        data = self.safe_api_call('coingecko', self.cg_session, url)
        
        if data:
            print("✅ Globale Marktdaten abgerufen")
        
        return data
    
    def get_liquidation_data(self) -> Optional[Dict]:
        """Holt Liquidationsdaten von CoinGlass (nur für BTC/ETH)"""
        if not self.check_rate_limit('coinglass'):
            return None
        
        # Nur für BTC und ETH um API-Calls zu sparen
        liquidation_data = {}
        
        for symbol in ['BTC', 'ETH']:
            url = f"{self.coinglass_url}/api/futures/liquidation/coin/history"
            params = {
                'symbol': symbol,
                'timeType': '1h',  # Letzte Stunde
                'limit': 1
            }
            
            data = self.safe_api_call('coinglass', self.glass_session, url, params)
            if data and 'data' in data:
                liquidation_data[symbol] = data['data']
                time.sleep(1)  # Pause zwischen Requests
        
        if liquidation_data:
            print(f"✅ Liquidationsdaten für {len(liquidation_data)} Coins abgerufen")
        
        return liquidation_data
    
    def get_fear_greed_index(self) -> Optional[Dict]:
        """Holt Fear & Greed Index"""
        url = "https://api.alternative.me/fng/"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and 'data' in data:
                print("✅ Fear & Greed Index abgerufen")
                return data['data'][0]
                
        except requests.RequestException as e:
            print(f"❌ Fear & Greed Index Fehler: {e}")
        
        return None
    
    def get_rsi_data(self, symbol: str = 'BTC/USDT') -> Optional[Dict]:
        """Holt RSI-Daten von TAAPI (nur für BTC)"""
        if not self.taapi_key or not self.check_rate_limit('taapi'):
            return None
        
        params = {
            'secret': self.taapi_key,
            'exchange': 'binance',
            'symbol': symbol,
            'interval': '1h'
        }
        
        url = f"{self.taapi_url}/rsi"
        data = self.safe_api_call('taapi', self.taapi_session, url, params)
        
        if data:
            print(f"✅ RSI-Daten für {symbol} abgerufen")
        
        return data
    
    def calculate_market_metrics(self, basic_data: Dict, global_data: Dict) -> Dict:
        """Berechnet erweiterte Marktmetriken"""
        metrics = {
            'total_market_cap_usd': 0,
            'total_volume_24h_usd': 0,
            'average_24h_change': 0,
            'coins_above_zero': 0,
            'coins_below_zero': 0,
            'market_dominance': {},
            'global_metrics': {}
        }
        
        if global_data and 'data' in global_data:
            global_info = global_data['data']
            metrics['global_metrics'] = {
                'total_market_cap_usd': global_info.get('total_market_cap', {}).get('usd'),
                'total_volume_24h_usd': global_info.get('total_volume', {}).get('usd'),
                'market_cap_percentage': global_info.get('market_cap_percentage', {}),
                'active_cryptocurrencies': global_info.get('active_cryptocurrencies'),
                'markets': global_info.get('markets')
            }
        
        total_change = 0
        valid_changes = 0
        
        for coin_id, data in basic_data.items():
            if data.get('usd_market_cap'):
                metrics['total_market_cap_usd'] += data['usd_market_cap']
            if data.get('usd_24h_vol'):
                metrics['total_volume_24h_usd'] += data['usd_24h_vol']
            
            change = data.get('usd_24h_change')
            if change is not None:
                total_change += change
                valid_changes += 1
                
                if change > 0:
                    metrics['coins_above_zero'] += 1
                else:
                    metrics['coins_below_zero'] += 1
        
        if valid_changes > 0:
            metrics['average_24h_change'] = total_change / valid_changes
        
        return metrics
    
    def update_enhanced_data(self):
        """Aktualisiert alle erweiterten Daten"""
        print(f"🔄 Aktualisiere erweiterte Daten um {datetime.now().strftime('%H:%M:%S')}")
        
        # Basis-Daten (immer)
        basic_data = self.get_basic_market_data()
        if not basic_data:
            print("❌ Basis-Daten konnten nicht abgerufen werden")
            return
        
        # Globale Daten (immer)
        global_data = self.get_global_market_data()
        
        # Erweiterte Daten (nur wenn APIs verfügbar)
        liquidation_data = self.get_liquidation_data()
        fear_greed = self.get_fear_greed_index()
        rsi_data = self.get_rsi_data() if self.taapi_key else None
        
        # Berechne Metriken
        market_metrics = self.calculate_market_metrics(basic_data, global_data)
        
        # Kombiniere alle Daten
        self.enhanced_data = {
            'timestamp': datetime.now().isoformat(),
            'update_interval_seconds': self.update_interval,
            'api_status': {
                'coingecko': 'active',
                'coinglass': 'active' if liquidation_data else 'limited',
                'taapi': 'active' if rsi_data else 'not_configured',
                'fear_greed': 'active' if fear_greed else 'limited'
            },
            'coins': self.process_coin_data(basic_data),
            'market_metrics': market_metrics,
            'liquidations': liquidation_data or {},
            'fear_greed_index': fear_greed,
            'technical_indicators': {
                'btc_rsi': rsi_data
            },
            'rate_limit_status': self.get_rate_limit_status()
        }
        
        self.last_update = datetime.now()
        self.save_enhanced_data()
        
        print(f"✅ Erweiterte Daten aktualisiert: {len(self.enhanced_data['coins'])} Coins")
    
    def process_coin_data(self, basic_data: Dict) -> Dict:
        """Verarbeitet Coin-Daten"""
        processed = {}
        
        for coin_id, data in basic_data.items():
            processed[coin_id] = {
                'id': coin_id,
                'price_usd': data.get('usd'),
                'price_eur': data.get('eur'),
                'market_cap_usd': data.get('usd_market_cap'),
                'volume_24h_usd': data.get('usd_24h_vol'),
                'change_24h_percent': data.get('usd_24h_change'),
                'last_updated': data.get('last_updated_at')
            }
        
        return processed
    
    def get_rate_limit_status(self) -> Dict:
        """Gibt aktuellen Rate Limit Status zurück"""
        status = {}
        
        for api_name in self.rate_limits:
            current_requests = len(self.last_requests[api_name])
            limit = self.rate_limits[api_name]
            
            status[api_name] = {
                'current_requests_per_minute': current_requests,
                'limit_per_minute': limit,
                'usage_percentage': round((current_requests / limit) * 100, 1),
                'available_requests': limit - current_requests
            }
        
        return status
    
    def save_enhanced_data(self):
        """Speichert erweiterte Daten"""
        if not self.enhanced_data:
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        current_file = self.output_dir / "current_enhanced_data.json"
        
        try:
            with open(current_file, 'w', encoding='utf-8') as f:
                json.dump(self.enhanced_data, f, indent=2, ensure_ascii=False)
            
            # Archiviere alle 30 Minuten
            if datetime.now().minute % 30 == 0:
                archive_file = self.output_dir / f"enhanced_data_{timestamp}.json"
                with open(archive_file, 'w', encoding='utf-8') as f:
                    json.dump(self.enhanced_data, f, indent=2, ensure_ascii=False)
                print(f"📁 Daten archiviert: {archive_file}")
                
        except Exception as e:
            print(f"❌ Fehler beim Speichern: {e}")
    
    def start_enhanced_monitoring(self):
        """Startet erweitertes Monitoring"""
        if self.is_running:
            print("⚠️ Enhanced Monitoring läuft bereits")
            return
        
        self.is_running = True
        print(f"🚀 Enhanced Monitoring gestartet (Update alle {self.update_interval}s)")
        print(f"📊 Überwachte Coins: {len(self.target_coins)}")
        print(f"🔑 APIs: CoinGecko{'✓' if self.coingecko_key else '(free)'}, "
              f"CoinGlass{'✓' if self.coinglass_key else '(free)'}, "
              f"TAAPI{'✓' if self.taapi_key else '✗'}")
        
        # Erste Aktualisierung
        self.update_enhanced_data()
        
        # Schedule für Updates
        schedule.every(self.update_interval).seconds.do(self.update_enhanced_data)
        
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        print("✅ Enhanced Monitoring aktiv")
    
    def setup_routes(self):
        """Flask-Routen für Web-Interface"""
        
        @self.app.route('/')
        def enhanced_dashboard():
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Enhanced Crypto Dashboard</title>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                    .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                    .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 20px; }
                    .metric-card { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                    .rate-limits { background: #ecf0f1; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
                    .api-status { display: flex; gap: 10px; margin: 10px 0; }
                    .status-badge { padding: 4px 8px; border-radius: 4px; color: white; font-size: 12px; }
                    .active { background: #27ae60; }
                    .limited { background: #f39c12; }
                    .inactive { background: #e74c3c; }
                </style>
                <script>
                    function refreshData() {
                        fetch('/api/enhanced')
                            .then(response => response.json())
                            .then(data => updateDashboard(data))
                            .catch(error => console.error('Error:', error));
                    }
                    
                    function updateDashboard(data) {
                        if (data.data) {
                            document.getElementById('last-update').textContent = 
                                'Letztes Update: ' + new Date(data.last_update).toLocaleString();
                        }
                    }
                    
                    setInterval(refreshData, 60000);
                    window.onload = refreshData;
                </script>
            </head>
            <body>
                <div class="header">
                    <h1>📊 Enhanced Crypto Dashboard</h1>
                    <p>Erweiterte Kryptowährungsdaten mit konservativen Rate Limits</p>
                    <div id="last-update">Lade Daten...</div>
                </div>
                
                <div class="rate-limits">
                    <h3>🚦 API Rate Limit Status</h3>
                    <div id="rate-status">Lade Status...</div>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <h4>💰 Marktkapitalisierung</h4>
                        <div id="market-cap">-</div>
                    </div>
                    <div class="metric-card">
                        <h4>😨 Fear & Greed Index</h4>
                        <div id="fear-greed">-</div>
                    </div>
                    <div class="metric-card">
                        <h4>💧 Liquidationen (24h)</h4>
                        <div id="liquidations">-</div>
                    </div>
                    <div class="metric-card">
                        <h4>📈 BTC RSI</h4>
                        <div id="btc-rsi">-</div>
                    </div>
                </div>
            </body>
            </html>
            """
        
        @self.app.route('/api/enhanced')
        def api_enhanced_data():
            return jsonify({
                "data": self.enhanced_data,
                "last_update": self.last_update.isoformat() if self.last_update else None,
                "status": "active" if self.is_running else "stopped"
            })

def main():
    """Hauptfunktion"""
    print("🚀 Enhanced Kryptowährungs-Daten-Agent")
    print("=" * 60)
    print("⚠️ Konservative Rate Limits für nachhaltige API-Nutzung")
    print()
    
    # API-Keys (alle optional)
    print("🔑 API-Key Konfiguration (alle optional):")
    coingecko_key = input("CoinGecko Demo API Key (Enter für kostenlos): ").strip() or None
    coinglass_key = input("CoinGlass API Key (Enter für kostenlos): ").strip() or None
    taapi_key = input("TAAPI.IO API Key (Enter für überspringen): ").strip() or None
    
    print()
    if coingecko_key:
        print("✅ CoinGecko: Demo API")
    else:
        print("🆓 CoinGecko: Kostenlose API")
    
    if coinglass_key:
        print("✅ CoinGlass: API Key konfiguriert")
    else:
        print("🆓 CoinGlass: Kostenlose API (begrenzt)")
    
    if taapi_key:
        print("✅ TAAPI.IO: API Key konfiguriert")
    else:
        print("⏭️ TAAPI.IO: Übersprungen (keine technischen Indikatoren)")
    
    # Agent erstellen
    agent = EnhancedCryptoAgent(
        coingecko_api_key=coingecko_key,
        coinglass_api_key=coinglass_key,
        taapi_key=taapi_key
    )
    
    print("\n📋 Verfügbare Optionen:")
    print("1. Enhanced Monitoring starten")
    print("2. Einmalige erweiterte Datenabfrage")
    print("3. Enhanced Dashboard starten")
    print("4. Monitoring + Dashboard")
    
    choice = input("\nWählen Sie eine Option (1-4): ").strip()
    
    if choice == "1":
        agent.start_enhanced_monitoring()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            agent.is_running = False
            
    elif choice == "2":
        agent.update_enhanced_data()
        if agent.enhanced_data:
            print(f"\n📊 Enhanced Daten für {len(agent.enhanced_data['coins'])} Coins:")
            print(f"💰 Gesamte Marktkapitalisierung: ${agent.enhanced_data['market_metrics']['total_market_cap_usd']:,.0f}")
            print(f"📈 Durchschnittliche 24h Änderung: {agent.enhanced_data['market_metrics']['average_24h_change']:.2f}%")
            
            if agent.enhanced_data['fear_greed_index']:
                fg = agent.enhanced_data['fear_greed_index']
                print(f"😨 Fear & Greed Index: {fg['value']} ({fg['value_classification']})")
            
            print(f"\n🚦 Rate Limit Status:")
            for api, status in agent.enhanced_data['rate_limit_status'].items():
                print(f"  {api}: {status['current_requests_per_minute']}/{status['limit_per_minute']} ({status['usage_percentage']}%)")
                
    elif choice == "3":
        agent.update_enhanced_data()
        agent.app.run(host='0.0.0.0', port=5001, debug=False)
        
    elif choice == "4":
        agent.start_enhanced_monitoring()
        time.sleep(3)
        
        import threading
        web_thread = threading.Thread(target=lambda: agent.app.run(host='0.0.0.0', port=5001, debug=False), daemon=True)
        web_thread.start()
        
        print("✅ Enhanced Monitoring und Dashboard aktiv")
        print("🌐 Dashboard: http://localhost:5001")
        print("📡 API: http://localhost:5001/api/enhanced")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            agent.is_running = False
    
    else:
        print("❌ Ungültige Auswahl")

if __name__ == "__main__":
    main()

