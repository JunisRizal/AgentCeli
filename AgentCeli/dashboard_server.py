#!/usr/bin/env python3
"""
AgentCeli Dashboard Server
Web-based management interface for the AgentCeli system
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_cors import CORS
import requests
import json
import time
import subprocess
import os
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3

# Import our modules
from data_source_expansion import DataSourceManager
from client_connection_manager import ClientManager

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Ensure directories exist
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Initialize managers
data_source_manager = DataSourceManager()
client_manager = ClientManager(BASE_DIR)

class DashboardManager:
    def __init__(self):
        self.agentceli_url = "http://localhost:8080"
        self.public_api_url = "http://localhost:8082"
        self.client_api_url = "http://localhost:8081"
        
    def get_system_status(self):
        """Get comprehensive system status"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'agentceli': {'running': False, 'data': None},
            'public_api': {'running': False, 'data': None},
            'client_api': {'running': False, 'data': None},
            'data_freshness': None,
            'total_clients': 0,
            'active_sources': 0
        }
        
        # Check AgentCeli main system
        try:
            response = requests.get(f"{self.agentceli_url}/api/status", timeout=3)
            if response.status_code == 200:
                status['agentceli']['running'] = True
                status['agentceli']['data'] = response.json()
                status['active_sources'] = status['agentceli']['data'].get('enabled_cycles', 0)
        except:
            pass
        
        # Check public API
        try:
            response = requests.get(f"{self.public_api_url}/api/health", timeout=3)
            if response.status_code == 200:
                status['public_api']['running'] = True
                status['public_api']['data'] = response.json()
        except:
            pass
        
        # Check client API
        try:
            response = requests.get(f"{self.client_api_url}/api/health", timeout=3)
            if response.status_code == 200:
                status['client_api']['running'] = True
                status['client_api']['data'] = response.json()
                status['total_clients'] = status['client_api']['data'].get('clients', 0)
        except:
            pass
        
        # Check data freshness
        json_file = BASE_DIR / "correlation_data" / "hybrid_latest.json"
        if json_file.exists():
            mod_time = json_file.stat().st_mtime
            data_age = time.time() - mod_time
            status['data_freshness'] = {
                'last_update': datetime.fromtimestamp(mod_time).isoformat(),
                'age_seconds': data_age,
                'is_fresh': data_age < 300  # Fresh if less than 5 minutes old
            }
        
        return status
    
    def get_live_data(self):
        """Get current live crypto data"""
        try:
            response = requests.get(f"{self.public_api_url}/api/crypto/latest", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def get_data_sources_status(self):
        """Get status of all data sources"""
        try:
            response = requests.get(f"{self.agentceli_url}/api/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('api_health', {})
        except:
            pass
        return {}
    
    def get_client_stats(self):
        """Get client delivery statistics"""
        try:
            response = requests.get(f"{self.client_api_url}/api/clients/stats", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {}

dashboard_manager = DashboardManager()

# Routes
@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/dashboard/status')
def api_status():
    """Get system status for dashboard"""
    return jsonify(dashboard_manager.get_system_status())

@app.route('/api/dashboard/live-data')
def api_live_data():
    """Get live crypto data for dashboard"""
    data = dashboard_manager.get_live_data()
    if data:
        return jsonify(data)
    return jsonify({'error': 'No data available'}), 404

@app.route('/api/dashboard/sources')
def api_sources():
    """Get data sources status"""
    sources = dashboard_manager.get_data_sources_status()
    return jsonify(sources)

@app.route('/api/dashboard/clients')
def api_clients():
    """Get client information"""
    clients = client_manager.clients
    stats = dashboard_manager.get_client_stats()
    
    return jsonify({
        'clients': clients,
        'stats': stats,
        'total': len(clients)
    })

@app.route('/api/dashboard/control/<action>')
def api_control(action):
    """Control AgentCeli system"""
    result = {'success': False, 'message': ''}
    
    try:
        if action == 'start':
            subprocess.run([
                'python3', str(BASE_DIR / 'agentceli_control.py'), 'start'
            ], cwd=BASE_DIR, capture_output=True, text=True, timeout=30)
            result = {'success': True, 'message': 'AgentCeli started'}
            
        elif action == 'stop':
            subprocess.run([
                'python3', str(BASE_DIR / 'agentceli_control.py'), 'stop'
            ], cwd=BASE_DIR, capture_output=True, text=True, timeout=30)
            result = {'success': True, 'message': 'AgentCeli stopped'}
            
        elif action == 'restart':
            subprocess.run([
                'python3', str(BASE_DIR / 'agentceli_control.py'), 'restart'
            ], cwd=BASE_DIR, capture_output=True, text=True, timeout=60)
            result = {'success': True, 'message': 'AgentCeli restarted'}
            
        else:
            result = {'success': False, 'message': 'Unknown action'}
            
    except Exception as e:
        result = {'success': False, 'message': str(e)}
    
    return jsonify(result)

@app.route('/api/dashboard/add-source', methods=['POST'])
def api_add_source():
    """Add new data source"""
    data = request.json
    
    try:
        source_name = data['name']
        source_type = data['type']
        config = data.get('config', {})
        
        success = data_source_manager.add_source(source_name, source_type, config)
        
        if success:
            return jsonify({'success': True, 'message': f'Source {source_name} added'})
        else:
            return jsonify({'success': False, 'message': 'Failed to add source'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/dashboard/test-source', methods=['POST'])
def api_test_source():
    """Test a data source connection"""
    data = request.json
    
    try:
        source_type = data['type']
        config = data.get('config', {})
        
        # Create temporary source instance for testing
        source_classes = {
            'kraken': 'KrakenAPI',
            'coinbase_advanced': 'CoinbaseAdvancedAPI',
            'alphavantage': 'AlphaVantageAPI'
        }
        
        if source_type in source_classes:
            # Import and test the source
            from data_source_expansion import KrakenAPI, CoinbaseAdvancedAPI, AlphaVantageAPI
            
            source_class_map = {
                'kraken': KrakenAPI,
                'coinbase_advanced': CoinbaseAdvancedAPI,
                'alphavantage': AlphaVantageAPI
            }
            
            source_class = source_class_map[source_type]
            source_instance = source_class(config)
            
            # Test connection
            connected = source_instance.connect()
            
            if connected:
                # Try to fetch sample data
                sample_data = source_instance.fetch_data()
                return jsonify({
                    'success': True,
                    'connected': True,
                    'sample_data': sample_data,
                    'cost_estimate': source_instance.get_cost_estimate()
                })
            else:
                return jsonify({
                    'success': False,
                    'connected': False,
                    'message': 'Connection failed'
                })
        else:
            return jsonify({
                'success': False,
                'message': f'Unknown source type: {source_type}'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/dashboard/add-client', methods=['POST'])
def api_add_client():
    """Add new client"""
    data = request.json
    
    try:
        success = client_manager.register_client(
            data['client_id'],
            data['name'],
            data['type'],
            data.get('endpoint'),
            data.get('webhook_url'),
            data.get('api_key')
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Client registered'})
        else:
            return jsonify({'success': False, 'message': 'Failed to register client'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/sources')
def sources_page():
    """Data sources management page"""
    return render_template('sources.html')

@app.route('/clients')  
def clients_page():
    """Client management page"""
    return render_template('clients.html')

@app.route('/logs')
def logs_page():
    """System logs page"""
    return render_template('logs.html')

@app.route('/api/dashboard/logs')
def api_logs():
    """Get system logs"""
    try:
        log_file = BASE_DIR / "logs" / "agentceli.log"
        if log_file.exists():
            with open(log_file, 'r') as f:
                lines = f.readlines()
                # Return last 100 lines
                return jsonify({
                    'logs': lines[-100:],
                    'total_lines': len(lines)
                })
        else:
            return jsonify({'logs': [], 'total_lines': 0})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("🚀 Starting AgentCeli Dashboard...")
    print("🌐 Dashboard will be available at: http://localhost:8083")
    print("📊 Features:")
    print("   - System monitoring")
    print("   - Data source management") 
    print("   - Client management")
    print("   - Live data viewing")
    print("   - System control")
    
    app.run(host='0.0.0.0', port=8083, debug=False)