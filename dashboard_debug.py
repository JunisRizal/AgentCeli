#!/usr/bin/env python3
"""
Simple debug dashboard to test data display
"""

from flask import Flask, render_template_string
import json
from datasource_monitor_dashboard import monitor

app = Flask(__name__)

DEBUG_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>AgentCeli Debug Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .status { background: #f0f0f0; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .api-item { margin: 10px 0; padding: 10px; background: #e8f5e8; border-radius: 3px; }
        .cost { color: #d63384; font-weight: bold; }
        .active { color: #198754; }
        .disabled { color: #6c757d; }
    </style>
</head>
<body>
    <h1>🐙 AgentCeli Debug Dashboard</h1>
    <p>📅 {{ timestamp }}</p>
    
    <div class="status">
        <h2>📊 API Status</h2>
        {% for name, info in sources.items() %}
        <div class="api-item">
            <strong>{{ name.upper() }}</strong> 
            <span class="{{ 'active' if info.enabled else 'disabled' }}">
                {{ 'ACTIVE' if info.enabled else 'DISABLED' }}
            </span>
            <br>
            Requests Today: {{ info.requests_today }}
            | Cost: <span class="cost">${{ "%.4f"|format(info.cost_today) }}</span>
            | Response Time: {{ info.avg_response_time }}s
            <br>
            Data Types: {{ info.data_types|join(', ') }}
        </div>
        {% endfor %}
    </div>
    
    <div class="status">
        <h2>💰 Cost Summary</h2>
        <p>Total Daily Cost: <span class="cost">${{ "%.4f"|format(total_cost) }}</span></p>
        <p>Active APIs: {{ active_count }}</p>
        <p>Total Requests: {{ total_requests }}</p>
    </div>
    
    <div class="status">
        <h2>🔄 Auto Refresh</h2>
        <p>This page refreshes every 30 seconds</p>
        <button onclick="location.reload()">🔄 Refresh Now</button>
    </div>
    
    <script>
        // Auto refresh every 30 seconds
        setTimeout(function() {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
'''

@app.route('/')
def debug_dashboard():
    """Debug dashboard with simple data display"""
    try:
        # Get data from monitor
        sources = monitor.get_data_source_status()
        
        # Calculate summary
        total_cost = sum(info.get('cost_today', 0) for info in sources.values())
        active_count = sum(1 for info in sources.values() if info.get('enabled', False))  
        total_requests = sum(info.get('requests_today', 0) for info in sources.values())
        
        return render_template_string(DEBUG_TEMPLATE, 
            sources=sources,
            total_cost=total_cost,
            active_count=active_count,
            total_requests=total_requests,
            timestamp=monitor.last_update.get('dashboard', 'Unknown') if hasattr(monitor, 'last_update') and monitor.last_update else 'Just loaded'
        )
    except Exception as e:
        return f"<h1>❌ Debug Dashboard Error</h1><p>{str(e)}</p>"

@app.route('/api/test')
def api_test():
    """Test API endpoint"""
    return {
        "status": "OK",
        "sources_count": len(monitor.get_data_source_status()),
        "monitor_active": True,
        "test_timestamp": monitor.request_history if hasattr(monitor, 'request_history') else "No history"
    }

if __name__ == '__main__':
    print("🔧 Starting Debug Dashboard on port 8089...")
    app.run(host='127.0.0.1', port=8089, debug=True)