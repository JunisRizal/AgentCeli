#!/usr/bin/env python3
"""
AgentCeli Setup Verification
Checks all components and provides status report
"""

import json
import os
import sys
from pathlib import Path
import subprocess

def print_status(message, status="info"):
    colors = {
        "success": "\033[0;32m✅\033[0m",
        "warning": "\033[1;33m⚠️\033[0m", 
        "error": "\033[0;31m❌\033[0m",
        "info": "\033[0;34mℹ️\033[0m"
    }
    print(f"{colors.get(status, colors['info'])} {message}")

def check_python_modules():
    """Check required Python modules"""
    print("\n📦 Python Module Check:")
    
    required_modules = [
        'flask', 'requests', 'json', 'threading', 
        'sqlite3', 'datetime', 'pathlib', 'csv'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print_status(f"{module}: Available", "success")
        except ImportError:
            print_status(f"{module}: Missing", "error")
            missing.append(module)
    
    if missing:
        print_status(f"Missing modules: {', '.join(missing)}", "warning")
        print("Install with: pip3 install " + " ".join(missing))
    else:
        print_status("All required modules available", "success")
    
    return len(missing) == 0

def check_configuration():
    """Check AgentCeli configuration"""
    print("\n⚙️ Configuration Check:")
    
    config_file = "agentceli_config.json"
    if not os.path.exists(config_file):
        print_status("agentceli_config.json: Missing", "error")
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        print_status("Configuration file: Valid JSON", "success")
        
        # Check structure
        if 'data_sources' in config:
            print_status("Data sources section: Present", "success")
            
            # Check free APIs
            free_apis = config['data_sources'].get('free_apis', {})
            enabled_free = [api for api, settings in free_apis.items() if settings.get('enabled', False)]
            print_status(f"Free APIs enabled: {len(enabled_free)} ({', '.join(enabled_free)})", "success")
            
            # Check paid APIs
            paid_apis = config['data_sources'].get('paid_apis', {})
            enabled_paid = []
            for api, settings in paid_apis.items():
                if settings.get('enabled', False) and settings.get('key'):
                    enabled_paid.append(api)
            
            if enabled_paid:
                print_status(f"Paid APIs configured: {', '.join(enabled_paid)}", "success")
            else:
                print_status("Paid APIs: None configured (using free tier)", "info")
        
        return True
        
    except Exception as e:
        print_status(f"Configuration error: {e}", "error")
        return False

def check_data_files():
    """Check data files and directories"""
    print("\n📁 Data Files Check:")
    
    # Check directories
    directories = ['correlation_data', 'santiment_data', 'liquidation_data', 'logs']
    for directory in directories:
        if os.path.exists(directory):
            print_status(f"{directory}/: Exists", "success")
        else:
            print_status(f"{directory}/: Missing", "warning")
    
    # Check data files
    data_files = {
        'correlation_data/hybrid_latest.json': 'Core AgentCeli data',
        'correlation_data/hybrid_crypto_data.db': 'SQLite database',
        'agentceli_config.json': 'Configuration file'
    }
    
    for file_path, description in data_files.items():
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print_status(f"{description}: {file_size} bytes", "success")
        else:
            print_status(f"{description}: Not found", "warning")
    
    # Check Santiment data
    santiment_dir = Path("santiment_data")
    if santiment_dir.exists():
        santiment_files = list(santiment_dir.glob("*latest.json"))
        if santiment_files:
            print_status(f"Santiment data files: {len(santiment_files)} available", "success")
        else:
            print_status("Santiment data files: None found", "info")

def check_scripts():
    """Check executable scripts"""
    print("\n🔧 Script Check:")
    
    scripts = [
        'AgentCeli_Starter_Package.sh',
        'START_HERE.sh', 
        'install_agentceli.sh',
        'start_enhanced_liquidation_heatmap.sh'
    ]
    
    for script in scripts:
        if os.path.exists(script):
            if os.access(script, os.X_OK):
                print_status(f"{script}: Executable", "success")
            else:
                print_status(f"{script}: Not executable", "warning")
                print(f"   Fix with: chmod +x {script}")
        else:
            print_status(f"{script}: Missing", "warning")

def check_core_modules():
    """Check AgentCeli core modules"""
    print("\n🐙 AgentCeli Core Module Check:")
    
    core_modules = [
        'agentceli_hybrid.py',
        'agentceli_master_dashboard.py', 
        'enhanced_liquidation_heatmap.py',
        'liquidation_heatmap.py'
    ]
    
    for module in core_modules:
        if os.path.exists(module):
            try:
                # Try importing without running
                import importlib.util
                spec = importlib.util.spec_from_file_location("test_module", module)
                if spec and spec.loader:
                    print_status(f"{module}: Importable", "success")
                else:
                    print_status(f"{module}: Import issues", "warning")
            except Exception as e:
                print_status(f"{module}: Import error - {e}", "warning")
        else:
            print_status(f"{module}: Missing", "error")

def check_running_processes():
    """Check if AgentCeli processes are running"""
    print("\n🔄 Running Processes Check:")
    
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        processes = result.stdout
        
        agentceli_processes = [
            'agentceli_hybrid.py',
            'agentceli_master_dashboard.py',
            'enhanced_liquidation_heatmap.py',
            'santiment'
        ]
        
        running = []
        for process in agentceli_processes:
            if process in processes:
                running.append(process)
                print_status(f"{process}: Running", "success")
            else:
                print_status(f"{process}: Stopped", "info")
        
        if running:
            print_status(f"Active processes: {len(running)}", "success")
        else:
            print_status("No AgentCeli processes currently running", "info")
            
    except Exception as e:
        print_status(f"Process check error: {e}", "warning")

def generate_status_report():
    """Generate comprehensive status report"""
    print("\n" + "="*50)
    print("🐙 AgentCeli Setup Verification Report")
    print("="*50)
    
    # Run all checks
    modules_ok = check_python_modules()
    config_ok = check_configuration()
    check_data_files()
    check_scripts()
    check_core_modules()
    check_running_processes()
    
    # Summary
    print("\n📊 Summary:")
    if modules_ok and config_ok:
        print_status("AgentCeli setup: Ready to use!", "success")
        print("\n🚀 Next steps:")
        print("   1. Start AgentCeli: ./START_HERE.sh")
        print("   2. Access dashboard: http://localhost:8081")
        print("   3. View liquidation heatmap: http://localhost:8086")
    else:
        print_status("AgentCeli setup: Needs attention", "warning")
        print("\n🔧 Fix issues above, then run verification again")
    
    print("\n💡 For help: Check README_AgentCeli.md")
    print("📞 For issues: Review logs/ directory")

if __name__ == "__main__":
    generate_status_report()