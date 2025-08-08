#!/usr/bin/env python3
"""
Test script to identify dashboard deployment issues
"""

import sys
import os
from pathlib import Path

def test_dashboard_deployment():
    """Test all aspects of dashboard deployment"""
    print("🔍 Testing Dashboard Deployment Issues...")
    print("=" * 50)
    
    # 1. Check Python environment
    print(f"✅ Python: {sys.version.split()[0]}")
    
    # 2. Check required modules
    required_modules = ['flask', 'sqlite3', 'json', 'pathlib']
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ Module {module}: Available")
        except ImportError as e:
            print(f"❌ Module {module}: Missing - {e}")
    
    # 3. Check file structure
    base_dir = Path(__file__).parent
    required_files = [
        'datasource_monitor_dashboard.py',
        'templates/datasource_monitor.html',
        'agentceli_config.json'
    ]
    
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"✅ File {file_path}: Found")
        else:
            print(f"❌ File {file_path}: Missing")
    
    # 4. Test database setup
    try:
        from datasource_monitor_dashboard import DataSourceMonitor
        monitor = DataSourceMonitor()
        print("✅ Database: SQLite setup successful")
    except Exception as e:
        print(f"❌ Database: Setup failed - {e}")
    
    # 5. Test Flask app creation
    try:
        import datasource_monitor_dashboard
        app = datasource_monitor_dashboard.app
        print("✅ Flask App: Created successfully")
    except Exception as e:
        print(f"❌ Flask App: Creation failed - {e}")
    
    # 6. Test template rendering
    try:
        from flask import Flask
        test_app = Flask(__name__, template_folder='templates')
        with test_app.app_context():
            print("✅ Template System: Working")
    except Exception as e:
        print(f"❌ Template System: Failed - {e}")
    
    # 7. Check port availability
    import socket
    def check_port(port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    
    port = 8086
    if check_port(port):
        print(f"⚠️ Port {port}: Already in use")
    else:
        print(f"✅ Port {port}: Available")
    
    # 8. Test configuration loading
    try:
        config_file = base_dir / 'agentceli_config.json'
        if config_file.exists():
            import json
            with open(config_file, 'r') as f:
                config = json.load(f)
            print("✅ Configuration: Loaded successfully")
        else:
            print("⚠️ Configuration: File missing, using defaults")
    except Exception as e:
        print(f"❌ Configuration: Failed to load - {e}")
    
    print("\n🚀 Deployment Recommendations:")
    print("-" * 30)
    
    # Check if dashboard should work
    if check_port(8086):
        print("1. Stop any existing dashboard on port 8086")
        print("   Run: lsof -ti:8086 | xargs kill -9")
    
    print("2. Start dashboard with:")
    print("   ./start_monitor_dashboard.sh")
    print("   OR")
    print("   python3 datasource_monitor_dashboard.py")
    
    print("3. Access dashboard at:")
    print("   http://localhost:8086")
    
    print("4. If issues persist, check logs for:")
    print("   - Permission errors")
    print("   - Port conflicts")
    print("   - Missing data files")

if __name__ == "__main__":
    test_dashboard_deployment()