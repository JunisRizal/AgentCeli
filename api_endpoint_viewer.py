#!/usr/bin/env python3
"""
API Endpoint Viewer - Real-time API values display
Shows actual data from AgentCeli API endpoints without modifying the main dashboard
"""

from flask import Flask, jsonify, render_template_string
import requests
import json
from datetime import datetime
from pathlib import Path

class APIEndpointViewer:
    def __init__(self):
        self.app = Flask(__name__)
        self.agentceli_url = "http://localhost:8080"
        self.dashboard_url = "http://localhost:9000"
        self.base_dir = Path(__file__).parent
        
        self.setup_routes()
    
    def get_all_api_data(self):
        """Fetch real data from all available API endpoints"""
        api_data = {
            'timestamp': datetime.now().isoformat(),
            'endpoints': {},
            'files': {},
            'errors': []
        }
        
        # Test AgentCeli API endpoints
        endpoints_to_test = [
            '/api/status',
            '/api/prices'
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = requests.get(f"{self.agentceli_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    api_data['endpoints'][endpoint] = {
                        'status': 'success',
                        'data': response.json(),
                        'response_time': response.elapsed.total_seconds()
                    }
                else:
                    api_data['endpoints'][endpoint] = {
                        'status': 'error',
                        'error': f"HTTP {response.status_code}",
                        'data': None
                    }
            except Exception as e:
                api_data['endpoints'][endpoint] = {
                    'status': 'error',
                    'error': str(e),
                    'data': None
                }
        
        # Check file outputs with real data
        file_paths = [
            'correlation_data/hybrid_latest.json',
            'correlation_data/hybrid_latest.csv'
        ]
        
        for file_path in file_paths:
            full_path = self.base_dir / file_path
            if full_path.exists():
                try:
                    if file_path.endswith('.json'):
                        with open(full_path, 'r') as f:
                            file_data = json.load(f)
                        api_data['files'][file_path] = {
                            'status': 'exists',
                            'size': full_path.stat().st_size,
                            'modified': datetime.fromtimestamp(full_path.stat().st_mtime).isoformat(),
                            'preview': self.get_json_preview(file_data)
                        }
                    else:  # CSV
                        with open(full_path, 'r') as f:
                            lines = f.readlines()
                        api_data['files'][file_path] = {
                            'status': 'exists',
                            'size': full_path.stat().st_size,
                            'modified': datetime.fromtimestamp(full_path.stat().st_mtime).isoformat(),
                            'preview': {
                                'lines': len(lines),
                                'header': lines[0].strip() if lines else None,
                                'last_line': lines[-1].strip() if len(lines) > 1 else None
                            }
                        }
                except Exception as e:
                    api_data['files'][file_path] = {
                        'status': 'error',
                        'error': str(e)
                    }
            else:
                api_data['files'][file_path] = {
                    'status': 'missing'
                }
        
        return api_data
    
    def get_json_preview(self, data):
        """Create a preview of JSON data"""
        preview = {}
        
        if isinstance(data, dict):
            for key, value in data.items():
                if key in ['timestamp', 'api_tier', 'total_sources', 'cost_estimate']:
                    preview[key] = value
                elif key == 'live_prices' and isinstance(value, dict):
                    preview['live_prices_count'] = len(value)
                    if 'binance' in value:
                        preview['sample_prices'] = {k: v.get('price', 0) for k, v in list(value['binance'].items())[:4]}
                elif key == 'fear_greed' and isinstance(value, dict):
                    preview['fear_greed'] = value.get('value', 'N/A')
        
        return preview
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def viewer():
            return render_template_string(VIEWER_HTML)
        
        @self.app.route('/api/live-data')
        def live_data():
            return jsonify(self.get_all_api_data())
        
        @self.app.route('/api/raw/<path:endpoint>')
        def raw_endpoint(endpoint):
            """Proxy to get raw data from AgentCeli"""
            try:
                response = requests.get(f"{self.agentceli_url}/api/{endpoint}", timeout=5)
                return jsonify({
                    'status': response.status_code,
                    'data': response.json() if response.status_code == 200 else None,
                    'raw_response': response.text
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

# HTML Template for API Viewer
VIEWER_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>🔍 API Endpoint Viewer - Real Values</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: 'Monaco', 'Courier New', monospace; 
            margin: 0; 
            padding: 20px; 
            background: #1a1a1a;
            color: #00ff00;
        }
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
        }
        .header { 
            background: #333; 
            padding: 20px; 
            border-radius: 10px; 
            margin-bottom: 20px; 
            border: 2px solid #00ff00;
        }
        .header h1 { 
            margin: 0; 
            color: #00ff00; 
            text-shadow: 0 0 10px #00ff00;
        }
        .grid { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 20px; 
            margin-bottom: 20px;
        }
        .panel { 
            background: #222; 
            padding: 20px; 
            border-radius: 10px; 
            border: 1px solid #444;
            box-shadow: 0 0 20px rgba(0,255,0,0.1);
        }
        .panel h2 { 
            margin-top: 0; 
            color: #00ffff; 
            border-bottom: 1px solid #00ffff;
            padding-bottom: 10px;
        }
        .endpoint { 
            margin: 15px 0; 
            padding: 15px; 
            background: #111; 
            border-radius: 8px; 
            border-left: 4px solid #00ff00;
        }
        .endpoint.error { border-left-color: #ff0000; }
        .endpoint-url { 
            color: #ffff00; 
            font-weight: bold; 
            font-size: 1.1em;
        }
        .status-success { color: #00ff00; }
        .status-error { color: #ff0000; }
        .json-data { 
            background: #000; 
            padding: 10px; 
            border-radius: 5px; 
            overflow-x: auto; 
            margin: 10px 0;
            border: 1px solid #333;
        }
        .key { color: #00ffff; }
        .value { color: #ffff00; }
        .string { color: #00ff00; }
        .number { color: #ff8c00; }
        .refresh-btn { 
            background: #00ff00; 
            color: #000; 
            border: none; 
            padding: 10px 20px; 
            border-radius: 5px; 
            cursor: pointer; 
            font-weight: bold;
            margin-bottom: 15px;
        }
        .refresh-btn:hover { 
            background: #00cc00; 
            box-shadow: 0 0 10px #00ff00;
        }
        .timestamp { 
            color: #888; 
            font-size: 0.9em; 
        }
        .file-info { 
            margin: 10px 0; 
            padding: 10px; 
            background: #111; 
            border-radius: 5px;
            border-left: 4px solid #ffff00;
        }
        .auto-refresh { 
            color: #00ffff; 
            font-size: 0.9em; 
            float: right;
        }
        pre { 
            white-space: pre-wrap; 
            word-wrap: break-word; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 API Endpoint Viewer</h1>
            <p>Real-time values from AgentCeli API endpoints</p>
            <div class="auto-refresh">Auto-refresh: 10s</div>
        </div>
        
        <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Now</button>
        
        <div class="grid">
            <!-- API Endpoints -->
            <div class="panel">
                <h2>📡 Live API Endpoints</h2>
                <div id="api-endpoints">
                    Loading endpoints...
                </div>
            </div>
            
            <!-- File Outputs -->
            <div class="panel">
                <h2>📁 File Outputs</h2>
                <div id="file-outputs">
                    Loading files...
                </div>
            </div>
        </div>
        
        <!-- Raw Data Display -->
        <div class="panel">
            <h2>📊 Raw JSON Data</h2>
            <div class="json-data" id="raw-data">
                Loading raw data...
            </div>
        </div>
        
        <!-- Live Price Monitor -->
        <div class="panel">
            <h2>💰 Live Price Monitor</h2>
            <div id="price-monitor">
                <div class="timestamp">Waiting for price data...</div>
            </div>
        </div>
    </div>

    <script>
        let refreshInterval;
        
        function formatJSON(obj, indent = 0) {
            const spaces = '  '.repeat(indent);
            let html = '';
            
            if (typeof obj === 'object' && obj !== null) {
                if (Array.isArray(obj)) {
                    html += '[\\n';
                    obj.forEach((item, index) => {
                        html += spaces + '  ' + formatJSON(item, indent + 1);
                        if (index < obj.length - 1) html += ',';
                        html += '\\n';
                    });
                    html += spaces + ']';
                } else {
                    html += '{\\n';
                    const keys = Object.keys(obj);
                    keys.forEach((key, index) => {
                        html += spaces + '  <span class="key">"' + key + '"</span>: ';
                        html += formatJSON(obj[key], indent + 1);
                        if (index < keys.length - 1) html += ',';
                        html += '\\n';
                    });
                    html += spaces + '}';
                }
            } else if (typeof obj === 'string') {
                html += '<span class="string">"' + obj + '"</span>';
            } else if (typeof obj === 'number') {
                html += '<span class="number">' + obj + '</span>';
            } else {
                html += '<span class="value">' + obj + '</span>';
            }
            
            return html;
        }
        
        function refreshData() {
            fetch('/api/live-data')
                .then(response => response.json())
                .then(data => {
                    updateEndpoints(data.endpoints);
                    updateFiles(data.files);
                    updateRawData(data);
                    updatePriceMonitor(data);
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('api-endpoints').innerHTML = 
                        '<div class="endpoint error">❌ Connection Error: ' + error + '</div>';
                });
        }
        
        function updateEndpoints(endpoints) {
            const container = document.getElementById('api-endpoints');
            let html = '';
            
            for (const [url, data] of Object.entries(endpoints)) {
                const statusClass = data.status === 'success' ? 'status-success' : 'status-error';
                const endpointClass = data.status === 'success' ? '' : 'error';
                
                html += `
                    <div class="endpoint ${endpointClass}">
                        <div class="endpoint-url">${url}</div>
                        <div class="${statusClass}">
                            ${data.status === 'success' ? '✅ Success' : '❌ ' + data.error}
                        </div>
                `;
                
                if (data.data) {
                    html += '<div class="json-data"><pre>' + formatJSON(data.data) + '</pre></div>';
                }
                
                if (data.response_time) {
                    html += `<div class="timestamp">Response time: ${(data.response_time * 1000).toFixed(0)}ms</div>`;
                }
                
                html += '</div>';
            }
            
            container.innerHTML = html;
        }
        
        function updateFiles(files) {
            const container = document.getElementById('file-outputs');
            let html = '';
            
            for (const [path, data] of Object.entries(files)) {
                html += `
                    <div class="file-info">
                        <strong>${path}</strong><br>
                        Status: ${data.status}<br>
                `;
                
                if (data.status === 'exists') {
                    html += `
                        Size: ${data.size} bytes<br>
                        Modified: ${new Date(data.modified).toLocaleString()}<br>
                    `;
                    
                    if (data.preview) {
                        html += '<div class="json-data"><pre>' + formatJSON(data.preview) + '</pre></div>';
                    }
                } else if (data.error) {
                    html += `Error: ${data.error}<br>`;
                }
                
                html += '</div>';
            }
            
            container.innerHTML = html;
        }
        
        function updateRawData(data) {
            const container = document.getElementById('raw-data');
            container.innerHTML = '<pre>' + formatJSON(data) + '</pre>';
        }
        
        function updatePriceMonitor(data) {
            const container = document.getElementById('price-monitor');
            let html = '';
            
            // Extract price data from endpoints
            const pricesEndpoint = data.endpoints['/api/prices'];
            if (pricesEndpoint && pricesEndpoint.data) {
                const prices = pricesEndpoint.data;
                html += `
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <div style="background: #111; padding: 15px; border-radius: 8px;">
                            <div style="color: #ffff00; font-size: 1.2em;">BTC</div>
                            <div style="color: #00ff00; font-size: 1.8em; font-weight: bold;">$${prices.btc.toLocaleString()}</div>
                        </div>
                        <div style="background: #111; padding: 15px; border-radius: 8px;">
                            <div style="color: #ffff00; font-size: 1.2em;">ETH</div>
                            <div style="color: #00ff00; font-size: 1.8em; font-weight: bold;">$${prices.eth.toLocaleString()}</div>
                        </div>
                        <div style="background: #111; padding: 15px; border-radius: 8px;">
                            <div style="color: #ffff00; font-size: 1.2em;">SOL</div>
                            <div style="color: #00ff00; font-size: 1.8em; font-weight: bold;">$${prices.sol.toLocaleString()}</div>
                        </div>
                        <div style="background: #111; padding: 15px; border-radius: 8px;">
                            <div style="color: #ffff00; font-size: 1.2em;">XRP</div>
                            <div style="color: #00ff00; font-size: 1.8em; font-weight: bold;">$${prices.xrp.toFixed(4)}</div>
                        </div>
                    </div>
                    <div class="timestamp">
                        Last update: ${new Date(prices.timestamp).toLocaleString()}<br>
                        API Tier: ${prices.api_tier} | Fear & Greed: ${prices.fear_greed || 'N/A'}
                    </div>
                `;
            } else {
                html = '<div class="timestamp">No price data available</div>';
            }
            
            container.innerHTML = html;
        }
        
        // Initialize
        refreshData();
        refreshInterval = setInterval(refreshData, 10000); // Refresh every 10 seconds
        
        // Show update indicator
        setInterval(() => {
            const btn = document.querySelector('.refresh-btn');
            btn.textContent = '🔄 Refreshing...';
            setTimeout(() => {
                btn.textContent = '🔄 Refresh Now';
            }, 1000);
        }, 10000);
    </script>
</body>
</html>
'''

def main():
    viewer = APIEndpointViewer()
    
    print("🔍 Starting API Endpoint Viewer...")
    print("🌐 URL: http://localhost:8091")
    print("📊 Shows real values from AgentCeli API endpoints")
    print("⚡ Auto-refreshes every 10 seconds")
    print("🔗 AgentCeli API: http://localhost:8080")
    print("🎛️ Main Dashboard: http://localhost:9000 (untouched)")
    
    try:
        viewer.app.run(host='127.0.0.1', port=8091, debug=False)
    except KeyboardInterrupt:
        print("\n🔍 API Endpoint Viewer stopped")

if __name__ == "__main__":
    main()