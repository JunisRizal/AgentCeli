#!/usr/bin/env python3
"""
AgentCeli Monitoring Dashboard
Umfassendes Dashboard für alle Systemaktivitäten mit funktionaler Backend-Verbindung
"""

from flask import Flask, jsonify, render_template, request
import json
import sqlite3
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import threading
import requests
import glob
import logging

app = Flask(__name__)

class AgentCeliMonitor:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.setup_logging()
        self.refresh_interval = 30  # seconds
        self.cached_data = {}
        self.last_update = {}
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_system_status(self):
        """Systemstatus und laufende Prozesse"""
        try:
            import psutil
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'agentceli' in cmdline.lower() or 'python' in cmdline and any(
                        agent_file in cmdline for agent_file in [
                            'agentceli_hybrid.py', 'liquidation_analyzer.py', 
                            'whale_alert', 'santiment'
                        ]
                    ):
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'command': cmdline[:80] + '...' if len(cmdline) > 80 else cmdline,
                            'status': 'running'
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return processes
        except ImportError:
            # Fallback ohne psutil
            import subprocess
            try:
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                lines = result.stdout.split('\n')
                processes = []
                for line in lines:
                    if 'agentceli' in line.lower() or ('python' in line and any(
                        agent in line for agent in ['hybrid', 'liquidation', 'whale', 'santiment']
                    )):
                        parts = line.split()
                        if len(parts) > 10:
                            processes.append({
                                'pid': parts[1],
                                'name': parts[10],
                                'command': ' '.join(parts[10:])[:80],
                                'status': 'running'
                            })
                return processes
            except Exception as e:
                self.logger.error(f"Process check failed: {e}")
                return []
    
    def get_api_sources_detail(self):
        """Detaillierte API-Quellen Status mit Daten und Timing"""
        
        # Lade Konfiguration
        try:
            with open(self.base_dir / 'agentceli_config.json', 'r') as f:
                config = json.load(f)
        except:
            config = {}
            
        # Lade aktuelle Daten
        current_data = self.get_current_crypto_data()
        
        # Standard Update-Intervalle aus Config (in Sekunden)
        intervals = config.get('update_intervals', {
            'fast_data': 300,    # 5 Minuten
            'slow_data': 900,    # 15 Minuten
            'very_slow': 3600    # 1 Stunde
        })
        
        api_sources = []
        
        # Binance API
        binance_enabled = config.get('data_sources', {}).get('free_apis', {}).get('binance', {}).get('enabled', False)
        try:
            start_time = time.time()
            response = requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT', timeout=5)
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                data = response.json()
                price = float(data['lastPrice'])
                change = float(data['priceChangePercent'])
                
                api_sources.append({
                    'name': 'Binance',
                    'status': 'aktiv' if binance_enabled else 'konfiguriert',
                    'active': binance_enabled,
                    'value': f"${price:,.0f} BTC",
                    'change': f"{change:+.2f}%",
                    'data_type': 'Preise & Volumen',
                    'last_update': datetime.now().strftime('%d.%m.%Y %H:%M Uhr'),
                    'next_request': (datetime.now() + timedelta(seconds=intervals['fast_data'])).strftime('%H:%M Uhr'),
                    'interval': f"{intervals['fast_data']//60} Min",
                    'response_time': f"{response_time}ms"
                })
        except:
            api_sources.append({
                'name': 'Binance',
                'status': 'inaktiv',
                'active': False,
                'value': 'Keine Daten',
                'data_type': 'Preise & Volumen',
                'last_update': 'Nie',
                'next_request': 'Gestoppt',
                'interval': 'N/A',
                'error': 'Verbindungsfehler'
            })
            
        # CoinGecko API  
        coingecko_enabled = config.get('data_sources', {}).get('free_apis', {}).get('coingecko', {}).get('enabled', False)
        try:
            start_time = time.time()
            response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true', timeout=5)
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                data = response.json()
                btc_price = data.get('bitcoin', {}).get('usd', 0)
                btc_change = data.get('bitcoin', {}).get('usd_24h_change', 0)
                
                api_sources.append({
                    'name': 'CoinGecko',
                    'status': 'aktiv' if coingecko_enabled else 'konfiguriert',
                    'active': coingecko_enabled,
                    'value': f"${btc_price:,.0f} BTC",
                    'change': f"{btc_change:+.2f}%",
                    'data_type': 'Market Data',
                    'last_update': datetime.now().strftime('%d.%m.%Y %H:%M Uhr'),
                    'next_request': (datetime.now() + timedelta(seconds=intervals['fast_data'])).strftime('%H:%M Uhr'),
                    'interval': f"{intervals['fast_data']//60} Min",
                    'response_time': f"{response_time}ms"
                })
        except:
            api_sources.append({
                'name': 'CoinGecko',
                'status': 'inaktiv',
                'active': False,
                'value': 'Keine Daten',
                'data_type': 'Market Data',
                'last_update': 'Nie',
                'next_request': 'Gestoppt',
                'interval': 'N/A',
                'error': 'Verbindungsfehler'
            })
            
        # Fear & Greed Index
        fear_greed_enabled = config.get('data_sources', {}).get('free_apis', {}).get('fear_greed', {}).get('enabled', False)
        try:
            start_time = time.time()
            response = requests.get('https://api.alternative.me/fng/', timeout=5)
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    fng_value = data['data'][0]['value']
                    fng_class = data['data'][0]['value_classification']
                    
                    api_sources.append({
                        'name': 'Fear & Greed Index',
                        'status': 'aktiv' if fear_greed_enabled else 'konfiguriert',
                        'active': fear_greed_enabled,
                        'value': f"{fng_value}/100",
                        'change': fng_class,
                        'data_type': 'Markt-Sentiment',
                        'last_update': datetime.now().strftime('%d.%m.%Y %H:%M Uhr'),
                        'next_request': (datetime.now() + timedelta(seconds=intervals['very_slow'])).strftime('%H:%M Uhr'),
                        'interval': f"{intervals['very_slow']//60} Min",
                        'response_time': f"{response_time}ms"
                    })
        except:
            api_sources.append({
                'name': 'Fear & Greed Index',
                'status': 'inaktiv',
                'active': False,
                'value': 'Keine Daten',
                'data_type': 'Markt-Sentiment',
                'last_update': 'Nie',
                'next_request': 'Gestoppt',
                'interval': 'N/A',
                'error': 'Verbindungsfehler'
            })
            
        # Santiment API
        santiment_config = config.get('data_sources', {}).get('paid_apis', {}).get('santiment', {})
        santiment_enabled = santiment_config.get('enabled', False)
        
        # Check for Santiment data files
        santiment_data = current_data.get('paid_apis', {}).get('santiment', {})
        last_updates = santiment_data.get('last_updates', {})
        
        if last_updates:
            # Find most recent update
            latest_file = max(last_updates.keys(), key=lambda k: last_updates[k])
            latest_update = last_updates[latest_file]
            latest_dt = datetime.fromisoformat(latest_update.replace('Z', ''))
            
            api_sources.append({
                'name': 'Santiment Pro',
                'status': 'aktiv' if santiment_enabled else 'konfiguriert',
                'active': santiment_enabled,
                'value': f"{len(last_updates)} Metriken",
                'change': f"Letzter: {latest_file}",
                'data_type': 'Whale & Exchange Flows',
                'last_update': latest_dt.strftime('%d.%m.%Y %H:%M Uhr'),
                'next_request': (datetime.now() + timedelta(seconds=intervals['slow_data'])).strftime('%H:%M Uhr'),
                'interval': f"{intervals['slow_data']//60} Min",
                'response_time': 'Cache'
            })
        else:
            api_sources.append({
                'name': 'Santiment Pro',
                'status': 'inaktiv' if santiment_enabled else 'nicht konfiguriert',
                'active': False,
                'value': 'Keine Daten',
                'data_type': 'Whale & Exchange Flows',
                'last_update': 'Nie',
                'next_request': 'Gestoppt' if santiment_enabled else 'Nicht konfiguriert',
                'interval': 'N/A'
            })
            
        # Liquidation Heatmap (Interne Berechnung)
        liquidation_file = self.base_dir / 'liquidation_data/liquidation_analysis_latest.json'
        if liquidation_file.exists():
            try:
                stat = os.stat(liquidation_file)
                last_modified = datetime.fromtimestamp(stat.st_mtime)
                
                with open(liquidation_file, 'r') as f:
                    liq_data = json.load(f)
                
                # Extract some key metrics
                if isinstance(liq_data, dict) and 'analysis' in liq_data:
                    analysis = liq_data['analysis']
                    if 'BTC' in analysis:
                        btc_risk = analysis['BTC'].get('risk_score', 0)
                        api_sources.append({
                            'name': 'Liquidation Heatmap',
                            'status': 'aktiv',
                            'active': True,
                            'value': f"Risk: {btc_risk:.1f}/100",
                            'change': f"BTC Liquidation Risk",
                            'data_type': 'Risk Analysis',
                            'last_update': last_modified.strftime('%d.%m.%Y %H:%M Uhr'),
                            'next_request': (datetime.now() + timedelta(seconds=intervals['fast_data'])).strftime('%H:%M Uhr'),
                            'interval': f"{intervals['fast_data']//60} Min",
                            'response_time': 'Berechnung'
                        })
            except:
                pass
        
        return api_sources
    
    def get_data_status(self):
        """Aktuelle Datenfiles und deren Status"""
        data_files = []
        
        # JSON Data Files
        json_patterns = [
            'correlation_data/*.json',
            'liquidation_data/*.json',
            '*.json'
        ]
        
        for pattern in json_patterns:
            files = glob.glob(str(self.base_dir / pattern))
            for file_path in files[:10]:  # Limit to 10 most recent
                try:
                    stat = os.stat(file_path)
                    with open(file_path, 'r') as f:
                        content = json.load(f)
                    
                    file_info = {
                        'name': os.path.basename(file_path),
                        'path': file_path.replace(str(self.base_dir), ''),
                        'size': f"{stat.st_size / 1024:.1f} KB",
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'records': len(content) if isinstance(content, (list, dict)) else 1,
                        'type': 'json',
                        'status': 'valid'
                    }
                    data_files.append(file_info)
                except Exception as e:
                    data_files.append({
                        'name': os.path.basename(file_path),
                        'path': file_path.replace(str(self.base_dir), ''),
                        'status': 'error',
                        'error': str(e)[:50]
                    })
        
        # Database Files
        db_files = ['correlation_data/hybrid_crypto_data.db', 'monitoring.db', 'contact_agent.db']
        for db_file in db_files:
            full_path = self.base_dir / db_file
            if full_path.exists():
                try:
                    conn = sqlite3.connect(full_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    
                    # Count total records
                    total_records = 0
                    for table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                        count = cursor.fetchone()[0]
                        total_records += count
                    
                    conn.close()
                    
                    stat = os.stat(full_path)
                    data_files.append({
                        'name': os.path.basename(db_file),
                        'path': db_file,
                        'size': f"{stat.st_size / 1024:.1f} KB",
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'records': total_records,
                        'tables': len(tables),
                        'type': 'database',
                        'status': 'valid'
                    })
                except Exception as e:
                    data_files.append({
                        'name': os.path.basename(db_file),
                        'path': db_file,
                        'status': 'error',
                        'error': str(e)[:50],
                        'type': 'database'
                    })
        
        return sorted(data_files, key=lambda x: x.get('modified', ''), reverse=True)
    
    def get_log_status(self):
        """Log-Dateien Status und letzte Einträge"""
        log_files = []
        log_dir = self.base_dir / 'logs'
        
        if log_dir.exists():
            for log_file in log_dir.glob('*.log'):
                try:
                    stat = os.stat(log_file)
                    
                    # Letzte 5 Zeilen lesen
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        recent_lines = lines[-5:] if len(lines) > 5 else lines
                    
                    log_files.append({
                        'name': log_file.name,
                        'size': f"{stat.st_size / 1024:.1f} KB",
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'lines': len(lines),
                        'recent': [line.strip() for line in recent_lines],
                        'status': 'active' if stat.st_mtime > time.time() - 3600 else 'inactive'  # Active if modified in last hour
                    })
                except Exception as e:
                    log_files.append({
                        'name': log_file.name,
                        'status': 'error',
                        'error': str(e)[:50]
                    })
        
        return sorted(log_files, key=lambda x: x.get('modified', ''), reverse=True)
    
    def get_current_crypto_data(self):
        """Aktuelle Kryptowährungsdaten"""
        try:
            # Versuche aktuellen Hybrid-Daten zu laden
            hybrid_file = self.base_dir / 'correlation_data/hybrid_latest.json'
            if hybrid_file.exists():
                with open(hybrid_file, 'r') as f:
                    return json.load(f)
            
            # Fallback: Liquidation-Daten
            liquidation_file = self.base_dir / 'liquidation_data/liquidation_analysis_latest.json'
            if liquidation_file.exists():
                with open(liquidation_file, 'r') as f:
                    return json.load(f)
            
            return {}
        except Exception as e:
            self.logger.error(f"Failed to load crypto data: {e}")
            return {}

monitor = AgentCeliMonitor()

@app.route('/')
def dashboard():
    """Hauptseite des Dashboards"""
    return render_template('monitoring_dashboard.html')

@app.route('/api/system')
def api_system():
    """System-Status API"""
    return jsonify({
        'processes': monitor.get_system_status(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/apis')
def api_apis():
    """API-Status API - Neue detaillierte Struktur"""
    return jsonify({
        'api_sources': monitor.get_api_sources_detail(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/data')
def api_data():
    """Daten-Status API"""
    return jsonify({
        'files': monitor.get_data_status(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/logs')
def api_logs():
    """Log-Status API"""
    return jsonify({
        'logs': monitor.get_log_status(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/crypto')
def api_crypto():
    """Aktuelle Krypto-Daten API"""
    return jsonify({
        'data': monitor.get_current_crypto_data(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/overview')
def api_overview():
    """Komplett-Übersicht API"""
    return jsonify({
        'system': {
            'processes': len(monitor.get_system_status()),
            'uptime': 'Unknown'
        },
        'apis': {
            'total': len(monitor.get_api_status()),
            'online': len([api for api in monitor.get_api_status() if api['status'] == 'online'])
        },
        'data': {
            'total_files': len(monitor.get_data_status()),
            'valid_files': len([f for f in monitor.get_data_status() if f.get('status') == 'valid'])
        },
        'logs': {
            'total_logs': len(monitor.get_log_status()),
            'active_logs': len([l for l in monitor.get_log_status() if l.get('status') == 'active'])
        },
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🔍 AgentCeli Monitoring Dashboard")
    print("==================================")
    print("✅ Backend-Verbindung: Aktiviert")
    print("📊 Datenquellen: Live-Monitoring")
    print("🌐 Dashboard verfügbar unter: http://localhost:8090")
    print("==================================")
    
    app.run(host='0.0.0.0', port=8090, debug=False, threaded=True)