#!/usr/bin/env python3
"""
AgentCeli Client Connection Manager
Handles connections to external systems requesting data
"""

import json
import time
import requests
import threading
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3

class ClientManager:
    """Manages client connections and data delivery"""
    
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir or Path(__file__).parent)
        self.clients_file = self.base_dir / "clients.json"
        self.db_file = self.base_dir / "agentceli_clients.db"
        
        self.clients = {}
        self.delivery_stats = {}
        
        # Initialize database
        self._init_database()
        self.load_clients()
        
        # Flask app for HTTP API
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for all routes
        self._setup_routes()
    
    def _init_database(self):
        """Initialize SQLite database for client management"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Clients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                endpoint TEXT,
                webhook_url TEXT,
                api_key TEXT,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_delivery TIMESTAMP,
                delivery_count INTEGER DEFAULT 0
            )
        ''')
        
        # Delivery log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS delivery_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_type TEXT,
                success BOOLEAN,
                response_time REAL,
                error_message TEXT,
                FOREIGN KEY (client_id) REFERENCES clients (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_clients(self):
        """Load client configuration from file and database"""
        # Load from JSON file (legacy)
        if self.clients_file.exists():
            with open(self.clients_file) as f:
                file_clients = json.load(f)
                self.clients.update(file_clients)
        
        # Load from database
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM clients WHERE enabled = 1')
        rows = cursor.fetchall()
        
        for row in rows:
            client_id = row[0]
            self.clients[client_id] = {
                'name': row[1],
                'type': row[2],
                'endpoint': row[3],
                'webhook_url': row[4],
                'api_key': row[5],
                'enabled': bool(row[6]),
                'created_at': row[7],
                'last_delivery': row[8],
                'delivery_count': row[9]
            }
        
        conn.close()
    
    def save_clients(self):
        """Save clients to JSON file (backup)"""
        with open(self.clients_file, 'w') as f:
            json.dump(self.clients, f, indent=2)
    
    def register_client(self, client_id, name, client_type, endpoint=None, webhook_url=None, api_key=None):
        """Register a new client"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO clients 
            (id, name, type, endpoint, webhook_url, api_key, enabled, created_at, delivery_count)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, 0)
        ''', (client_id, name, client_type, endpoint, webhook_url, api_key, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        # Update in-memory clients
        self.clients[client_id] = {
            'name': name,
            'type': client_type,
            'endpoint': endpoint,
            'webhook_url': webhook_url,
            'api_key': api_key,
            'enabled': True,
            'created_at': datetime.now().isoformat(),
            'delivery_count': 0
        }
        
        self.save_clients()
        print(f"✅ Registered client: {name} ({client_id})")
        return True
    
    def unregister_client(self, client_id):
        """Unregister a client"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE clients SET enabled = 0 WHERE id = ?', (client_id,))
        conn.commit()
        conn.close()
        
        if client_id in self.clients:
            del self.clients[client_id]
            self.save_clients()
        
        print(f"✅ Unregistered client: {client_id}")
        return True
    
    def deliver_to_client(self, client_id, data, data_type="live_prices"):
        """Deliver data to a specific client"""
        if client_id not in self.clients:
            return False
        
        client = self.clients[client_id]
        start_time = time.time()
        success = False
        error_msg = None
        
        try:
            if client['type'] == 'webhook' and client.get('webhook_url'):
                # Send via webhook
                headers = {'Content-Type': 'application/json'}
                if client.get('api_key'):
                    headers['Authorization'] = f"Bearer {client['api_key']}"
                
                response = requests.post(
                    client['webhook_url'],
                    json={
                        'source': 'AgentCeli',
                        'timestamp': datetime.now().isoformat(),
                        'data_type': data_type,
                        'data': data
                    },
                    headers=headers,
                    timeout=10
                )
                
                success = response.status_code == 200
                if not success:
                    error_msg = f"HTTP {response.status_code}: {response.text[:100]}"
            
            elif client['type'] == 'api' and client.get('endpoint'):
                # Client will fetch from our API - just log the availability
                success = True
            
            elif client['type'] == 'file':
                # Save to file for client pickup
                client_file = self.base_dir / f"client_data_{client_id}.json"
                with open(client_file, 'w') as f:
                    json.dump({
                        'timestamp': datetime.now().isoformat(),
                        'data_type': data_type,
                        'data': data
                    }, f, indent=2)
                success = True
            
            else:
                error_msg = "Unknown client type or missing configuration"
            
        except Exception as e:
            error_msg = str(e)
            success = False
        
        # Log delivery attempt
        response_time = time.time() - start_time
        self._log_delivery(client_id, data_type, success, response_time, error_msg)
        
        # Update client stats
        if success:
            client['delivery_count'] = client.get('delivery_count', 0) + 1
            client['last_delivery'] = datetime.now().isoformat()
        
        return success
    
    def broadcast_to_all(self, data, data_type="live_prices"):
        """Broadcast data to all enabled clients"""
        results = {}
        
        for client_id, client in self.clients.items():
            if client.get('enabled', True):
                results[client_id] = self.deliver_to_client(client_id, data, data_type)
        
        return results
    
    def _log_delivery(self, client_id, data_type, success, response_time, error_msg):
        """Log delivery attempt to database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO delivery_log 
            (client_id, data_type, success, response_time, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (client_id, data_type, success, response_time, error_msg))
        
        conn.commit()
        conn.close()
    
    def get_client_stats(self, client_id=None):
        """Get delivery statistics for clients"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        if client_id:
            # Stats for specific client
            cursor.execute('''
                SELECT COUNT(*) as total_deliveries,
                       SUM(success) as successful_deliveries,
                       AVG(response_time) as avg_response_time,
                       MAX(timestamp) as last_delivery
                FROM delivery_log 
                WHERE client_id = ?
            ''', (client_id,))
            
            row = cursor.fetchone()
            stats = {
                'client_id': client_id,
                'total_deliveries': row[0],
                'successful_deliveries': row[1] or 0,
                'success_rate': (row[1] or 0) / max(row[0], 1) * 100,
                'avg_response_time': row[2] or 0,
                'last_delivery': row[3]
            }
        else:
            # Stats for all clients
            cursor.execute('''
                SELECT client_id,
                       COUNT(*) as total_deliveries,
                       SUM(success) as successful_deliveries,
                       AVG(response_time) as avg_response_time,
                       MAX(timestamp) as last_delivery
                FROM delivery_log 
                GROUP BY client_id
            ''')
            
            stats = {}
            for row in cursor.fetchall():
                stats[row[0]] = {
                    'total_deliveries': row[1],
                    'successful_deliveries': row[2] or 0,
                    'success_rate': (row[2] or 0) / max(row[1], 1) * 100,
                    'avg_response_time': row[3] or 0,
                    'last_delivery': row[4]
                }
        
        conn.close()
        return stats
    
    def _setup_routes(self):
        """Setup Flask API routes"""
        
        @self.app.route('/api/clients', methods=['GET'])
        def list_clients():
            """List all registered clients"""
            return jsonify({
                'clients': self.clients,
                'total_clients': len(self.clients),
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/clients/<client_id>/stats', methods=['GET'])
        def client_stats(client_id):
            """Get stats for specific client"""
            stats = self.get_client_stats(client_id)
            return jsonify(stats)
        
        @self.app.route('/api/clients/stats', methods=['GET'])
        def all_client_stats():
            """Get stats for all clients"""
            stats = self.get_client_stats()
            return jsonify(stats)
        
        @self.app.route('/api/register', methods=['POST'])
        def register_client_api():
            """Register a new client via API"""
            data = request.json
            
            required_fields = ['client_id', 'name', 'type']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
            
            success = self.register_client(
                data['client_id'],
                data['name'],
                data['type'],
                data.get('endpoint'),
                data.get('webhook_url'),
                data.get('api_key')
            )
            
            if success:
                return jsonify({'message': 'Client registered successfully'})
            else:
                return jsonify({'error': 'Failed to register client'}), 500
        
        @self.app.route('/api/data/latest', methods=['GET'])
        def get_latest_data():
            """Endpoint for clients to fetch latest data"""
            try:
                # Read from AgentCeli's data files
                json_file = self.base_dir / "correlation_data" / "hybrid_latest.json"
                
                if json_file.exists():
                    with open(json_file) as f:
                        data = json.load(f)
                    
                    return jsonify({
                        'success': True,
                        'source': 'AgentCeli',
                        'timestamp': datetime.now().isoformat(),
                        'data': data
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'No data available'
                    }), 404
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'operational',
                'clients': len(self.clients),
                'timestamp': datetime.now().isoformat()
            })
    
    def start_api_server(self, host='0.0.0.0', port=8081):
        """Start the client API server"""
        print(f"🚀 Starting Client API server on {host}:{port}")
        self.app.run(host=host, port=port, debug=False, threaded=True)

class DataBroadcaster:
    """Handles automatic data broadcasting to clients"""
    
    def __init__(self, client_manager, agentceli_data_path):
        self.client_manager = client_manager
        self.data_path = Path(agentceli_data_path)
        self.last_broadcast = None
        self.broadcast_interval = 60  # seconds
        self.running = False
        
    def start_broadcasting(self):
        """Start automatic data broadcasting"""
        self.running = True
        broadcast_thread = threading.Thread(target=self._broadcast_loop)
        broadcast_thread.daemon = True
        broadcast_thread.start()
        print("📡 Data broadcasting started")
    
    def stop_broadcasting(self):
        """Stop automatic data broadcasting"""
        self.running = False
        print("📡 Data broadcasting stopped")
    
    def _broadcast_loop(self):
        """Main broadcasting loop"""
        while self.running:
            try:
                # Check if new data is available
                json_file = self.data_path / "correlation_data" / "hybrid_latest.json"
                
                if json_file.exists():
                    mod_time = json_file.stat().st_mtime
                    
                    if not self.last_broadcast or mod_time > self.last_broadcast:
                        # New data available, broadcast it
                        with open(json_file) as f:
                            data = json.load(f)
                        
                        results = self.client_manager.broadcast_to_all(data, "live_prices")
                        
                        success_count = sum(1 for r in results.values() if r)
                        total_clients = len(results)
                        
                        print(f"📡 Broadcasted to {success_count}/{total_clients} clients")
                        
                        self.last_broadcast = time.time()
                
                time.sleep(self.broadcast_interval)
                
            except Exception as e:
                print(f"❌ Broadcasting error: {e}")
                time.sleep(self.broadcast_interval)

# Example usage
if __name__ == "__main__":
    # Initialize client manager
    manager = ClientManager()
    
    # Register some example clients
    manager.register_client(
        "trustlogiq_website",
        "TrustLogiq Website", 
        "webhook",
        webhook_url="https://trustlogiq.netlify.app/api/agentceli-data"
    )
    
    manager.register_client(
        "correlation_system",
        "Correlation Analysis System",
        "file"
    )
    
    manager.register_client(
        "external_dashboard",
        "External Dashboard",
        "api",
        endpoint="http://localhost:8081/api/data/latest"
    )
    
    # Start broadcaster
    broadcaster = DataBroadcaster(manager, Path(__file__).parent)
    broadcaster.start_broadcasting()
    
    # Start API server
    try:
        manager.start_api_server(port=8081)
    except KeyboardInterrupt:
        broadcaster.stop_broadcasting()
        print("\n👋 Client manager stopped")