#!/usr/bin/env python3
"""
AgentCeli Control Panel - Easy management of the data collection system
"""

import os
import sys
import json
import time
import subprocess
import requests
from datetime import datetime
from pathlib import Path

class AgentCeliController:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.config_file = self.base_dir / "agentceli_config.json"
        self.pid_file = self.base_dir / "agentceli.pid"
        self.log_file = self.base_dir / "logs" / "agentceli.log"
        self.api_url = "http://localhost:8080"
        
        # Ensure directories exist
        (self.base_dir / "logs").mkdir(exist_ok=True)
        (self.base_dir / "correlation_data").mkdir(exist_ok=True)
        
        self.load_config()
    
    def load_config(self):
        """Load or create configuration"""
        default_config = {
            "data_sources": {
                "free_apis": {
                    "binance": {"enabled": True, "priority": "high"},
                    "coinbase": {"enabled": True, "priority": "medium"},
                    "coingecko": {"enabled": True, "priority": "high"},
                    "fear_greed": {"enabled": True, "priority": "medium"}
                },
                "paid_apis": {
                    "coinglass": {"enabled": False, "key": None, "cost_per_call": 0.01},
                    "taapi": {"enabled": False, "key": None, "cost_per_call": 0.005}
                }
            },
            "data_delivery": {
                "http_api": {"enabled": True, "port": 8080},
                "file_output": {"enabled": True, "formats": ["json", "csv"]},
                "webhooks": {"enabled": False, "endpoints": []},
                "database": {"enabled": False, "connection": None}
            },
            "clients": {
                "trustlogiq": {"enabled": True, "type": "website"},
                "correlation_system": {"enabled": True, "type": "analysis"}
            },
            "update_intervals": {
                "fast_data": 60,    # seconds - prices, volumes
                "slow_data": 300,   # seconds - market metrics
                "very_slow": 3600   # seconds - news, sentiment
            }
        }
        
        if self.config_file.exists():
            with open(self.config_file) as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save current configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def is_running(self):
        """Check if AgentCeli is running"""
        try:
            response = requests.get(f"{self.api_url}/api/status", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def start(self):
        """Start AgentCeli system"""
        if self.is_running():
            print("✅ AgentCeli is already running")
            return True
        
        print("🚀 Starting AgentCeli...")
        
        # Choose which script to run based on configuration
        if any(api["enabled"] for api in self.config["data_sources"]["paid_apis"].values()):
            script = "agentceli_hybrid.py"
        else:
            script = "agentceli_free.py"
        
        try:
            # Start AgentCeli in background
            process = subprocess.Popen([
                sys.executable, script
            ], 
            cwd=self.base_dir,
            stdout=open(self.log_file, 'a'),
            stderr=subprocess.STDOUT
            )
            
            # Save PID
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # Wait for startup
            time.sleep(3)
            
            if self.is_running():
                print("✅ AgentCeli started successfully")
                print(f"📊 API available at: {self.api_url}")
                print(f"📝 Logs: {self.log_file}")
                return True
            else:
                print("❌ Failed to start AgentCeli")
                return False
                
        except Exception as e:
            print(f"❌ Error starting AgentCeli: {e}")
            return False
    
    def stop(self):
        """Stop AgentCeli system"""
        if not self.is_running():
            print("⏹️ AgentCeli is not running")
            return True
        
        print("🛑 Stopping AgentCeli...")
        
        try:
            # Try graceful shutdown first
            requests.post(f"{self.api_url}/api/shutdown", timeout=5)
            time.sleep(2)
        except:
            pass
        
        # Force stop if still running
        if self.pid_file.exists():
            try:
                with open(self.pid_file) as f:
                    pid = int(f.read().strip())
                os.kill(pid, 15)  # SIGTERM
                time.sleep(1)
                
                # Force kill if necessary
                try:
                    os.kill(pid, 9)  # SIGKILL
                except ProcessLookupError:
                    pass
                    
                self.pid_file.unlink()
                print("✅ AgentCeli stopped")
                return True
                
            except Exception as e:
                print(f"⚠️ Error stopping AgentCeli: {e}")
        
        return not self.is_running()
    
    def restart(self):
        """Restart AgentCeli system"""
        print("🔄 Restarting AgentCeli...")
        self.stop()
        time.sleep(2)
        return self.start()
    
    def status(self):
        """Show AgentCeli status and data"""
        print("\n🐙 AgentCeli Status Report")
        print("=" * 50)
        
        # System status
        running = self.is_running()
        print(f"Status: {'🟢 RUNNING' if running else '🔴 STOPPED'}")
        
        if not running:
            print("Use: python agentceli_control.py start")
            return
        
        try:
            # API Health
            health = requests.get(f"{self.api_url}/api/status", timeout=5).json()
            print(f"API Health: {health.get('is_running', False)}")
            print(f"Active Cycles: {health.get('enabled_cycles', 0)}")
            
            # Current prices
            prices = requests.get(f"{self.api_url}/api/prices", timeout=5).json()
            print(f"\n📊 Current Prices:")
            print(f"  BTC: ${prices.get('btc', 'N/A'):,.2f}")
            print(f"  ETH: ${prices.get('eth', 'N/A'):,.2f}")
            print(f"  SOL: ${prices.get('sol', 'N/A'):,.2f}")
            print(f"  XRP: ${prices.get('xrp', 'N/A'):,.4f}")
            print(f"  Fear & Greed: {prices.get('fear_greed', 'N/A')}")
            
            # Data sources status
            api_health = health.get('api_health', {})
            print(f"\n🔌 Data Sources:")
            for source, info in api_health.items():
                status_icon = "🟢" if info['status'] == 'connected' else "🔴"
                print(f"  {status_icon} {source}: {info['message']}")
            
            # File outputs
            print(f"\n📁 Data Files:")
            csv_file = self.base_dir / "correlation_data" / "hybrid_latest.csv"
            json_file = self.base_dir / "correlation_data" / "hybrid_latest.json"
            
            if csv_file.exists():
                mod_time = datetime.fromtimestamp(csv_file.stat().st_mtime)
                print(f"  📊 CSV: {csv_file} (updated {mod_time.strftime('%H:%M:%S')})")
            
            if json_file.exists():
                mod_time = datetime.fromtimestamp(json_file.stat().st_mtime)
                print(f"  📄 JSON: {json_file} (updated {mod_time.strftime('%H:%M:%S')})")
            
        except Exception as e:
            print(f"❌ Error getting status: {e}")
    
    def add_client(self, name, endpoint, client_type="website"):
        """Add a new data client"""
        print(f"➕ Adding client: {name}")
        
        self.config["clients"][name] = {
            "enabled": True,
            "type": client_type,
            "endpoint": endpoint,
            "added": datetime.now().isoformat()
        }
        
        self.save_config()
        print(f"✅ Client '{name}' added successfully")
    
    def remove_client(self, name):
        """Remove a data client"""
        if name in self.config["clients"]:
            del self.config["clients"][name]
            self.save_config()
            print(f"✅ Client '{name}' removed")
        else:
            print(f"❌ Client '{name}' not found")
    
    def list_clients(self):
        """List all connected clients"""
        print("\n👥 Connected Clients:")
        print("-" * 30)
        
        for name, info in self.config["clients"].items():
            status = "🟢 Active" if info["enabled"] else "🔴 Inactive"
            print(f"  {status} {name} ({info['type']})")
            if "endpoint" in info:
                print(f"    📍 {info['endpoint']}")
    
    def add_data_source(self, source_name, api_key=None, cost_per_call=0.01):
        """Add a new paid data source"""
        print(f"➕ Adding data source: {source_name}")
        
        self.config["data_sources"]["paid_apis"][source_name] = {
            "enabled": False,
            "key": api_key,
            "cost_per_call": cost_per_call,
            "added": datetime.now().isoformat()
        }
        
        self.save_config()
        print(f"✅ Data source '{source_name}' added (disabled by default)")
        print("Enable with: python agentceli_control.py enable-source {source_name}")
    
    def enable_source(self, source_name):
        """Enable a data source"""
        sources = {**self.config["data_sources"]["free_apis"], 
                  **self.config["data_sources"]["paid_apis"]}
        
        if source_name in sources:
            # Find which category it's in
            if source_name in self.config["data_sources"]["free_apis"]:
                self.config["data_sources"]["free_apis"][source_name]["enabled"] = True
            else:
                self.config["data_sources"]["paid_apis"][source_name]["enabled"] = True
            
            self.save_config()
            print(f"✅ Data source '{source_name}' enabled")
            print("Restart AgentCeli to apply changes")
        else:
            print(f"❌ Data source '{source_name}' not found")
    
    def disable_source(self, source_name):
        """Disable a data source"""
        sources = {**self.config["data_sources"]["free_apis"], 
                  **self.config["data_sources"]["paid_apis"]}
        
        if source_name in sources:
            if source_name in self.config["data_sources"]["free_apis"]:
                self.config["data_sources"]["free_apis"][source_name]["enabled"] = False
            else:
                self.config["data_sources"]["paid_apis"][source_name]["enabled"] = False
            
            self.save_config()
            print(f"✅ Data source '{source_name}' disabled")
        else:
            print(f"❌ Data source '{source_name}' not found")
    
    def list_sources(self):
        """List all data sources"""
        print("\n🔌 Data Sources:")
        print("-" * 30)
        
        print("Free APIs:")
        for name, info in self.config["data_sources"]["free_apis"].items():
            status = "🟢 Active" if info["enabled"] else "🔴 Inactive"
            print(f"  {status} {name}")
        
        print("\nPaid APIs:")
        for name, info in self.config["data_sources"]["paid_apis"].items():
            status = "🟢 Active" if info["enabled"] else "🔴 Inactive"
            cost = f"(${info['cost_per_call']}/call)" if info["enabled"] else ""
            print(f"  {status} {name} {cost}")
    
    def show_menu(self):
        """Show interactive menu"""
        while True:
            print("\n🐙 AgentCeli Control Panel")
            print("=" * 40)
            print("1. Start AgentCeli")
            print("2. Stop AgentCeli") 
            print("3. Restart AgentCeli")
            print("4. Show Status")
            print("5. List Data Sources")
            print("6. List Clients")
            print("7. Add Client")
            print("8. Add Data Source")
            print("9. Enable/Disable Source")
            print("0. Exit")
            
            choice = input("\nChoose option (0-9): ").strip()
            
            if choice == "1":
                self.start()
            elif choice == "2":
                self.stop()
            elif choice == "3":
                self.restart()
            elif choice == "4":
                self.status()
            elif choice == "5":
                self.list_sources()
            elif choice == "6":
                self.list_clients()
            elif choice == "7":
                name = input("Client name: ").strip()
                endpoint = input("Endpoint URL: ").strip()
                client_type = input("Type (website/analysis): ").strip() or "website"
                self.add_client(name, endpoint, client_type)
            elif choice == "8":
                source = input("Source name: ").strip()
                key = input("API key (optional): ").strip() or None
                cost = float(input("Cost per call ($): ") or "0.01")
                self.add_data_source(source, key, cost)
            elif choice == "9":
                self.list_sources()
                source = input("Source name: ").strip()
                action = input("Enable or disable? (e/d): ").strip().lower()
                if action.startswith('e'):
                    self.enable_source(source)
                else:
                    self.disable_source(source)
            elif choice == "0":
                break
            else:
                print("Invalid choice")
            
            input("\nPress Enter to continue...")

def main():
    controller = AgentCeliController()
    
    if len(sys.argv) < 2:
        controller.show_menu()
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        controller.start()
    elif command == "stop":
        controller.stop()
    elif command == "restart":
        controller.restart()
    elif command == "status":
        controller.status()
    elif command == "list-sources":
        controller.list_sources()
    elif command == "list-clients":
        controller.list_clients()
    elif command == "enable-source" and len(sys.argv) > 2:
        controller.enable_source(sys.argv[2])
    elif command == "disable-source" and len(sys.argv) > 2:
        controller.disable_source(sys.argv[2])
    elif command == "add-client" and len(sys.argv) > 3:
        controller.add_client(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "website")
    elif command == "menu":
        controller.show_menu()
    else:
        print("Usage:")
        print("  python agentceli_control.py [start|stop|restart|status|menu]")
        print("  python agentceli_control.py [list-sources|list-clients]")
        print("  python agentceli_control.py [enable-source|disable-source] <name>")
        print("  python agentceli_control.py add-client <name> <endpoint> [type]")

if __name__ == "__main__":
    main()