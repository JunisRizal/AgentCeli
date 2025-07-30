#!/usr/bin/env python3
"""
AgentCeli Watchdog - Auto-restart system
Monitors AgentCeli data collection and restarts it every 10 minutes if needed
"""

import time
import subprocess
import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import signal
import sys

class AgentCeliWatchdog:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.data_file = self.base_dir / "correlation_data" / "hybrid_latest.json"
        self.csv_file = self.base_dir / "correlation_data" / "hybrid_latest.csv"
        self.pid_file = self.base_dir / "agentceli.pid"
        self.api_url = "http://localhost:8080/api/prices"
        self.check_interval = 600  # 10 minutes in seconds
        self.max_data_age = 300    # 5 minutes max data age
        self.restart_count = 0
        self.log_file = self.base_dir / "logs" / "watchdog.log"
        
        # Ensure logs directory exists
        self.log_file.parent.mkdir(exist_ok=True)
        
    def log(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] WATCHDOG: {message}"
        print(log_message)
        
        # Also write to log file
        try:
            with open(self.log_file, "a") as f:
                f.write(log_message + "\n")
        except Exception as e:
            print(f"Failed to write to log file: {e}")
    
    def check_data_freshness(self):
        """Check if data files are fresh enough"""
        try:
            if not self.data_file.exists():
                self.log("❌ Data file does not exist")
                return False
                
            # Check file modification time
            file_mtime = datetime.fromtimestamp(self.data_file.stat().st_mtime)
            age_seconds = (datetime.now() - file_mtime).total_seconds()
            
            if age_seconds > self.max_data_age:
                self.log(f"❌ Data file is {age_seconds:.0f} seconds old (max: {self.max_data_age})")
                return False
                
            # Check if data contains recent timestamp
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                
            if 'timestamp' in data:
                data_time = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00').replace('+00:00', ''))
                data_age = (datetime.now() - data_time).total_seconds()
                
                if data_age > self.max_data_age:
                    self.log(f"❌ Data timestamp is {data_age:.0f} seconds old")
                    return False
            
            self.log("✅ Data is fresh")
            return True
            
        except Exception as e:
            self.log(f"❌ Error checking data freshness: {e}")
            return False
    
    def check_api_health(self):
        """Check if API is responding with fresh data"""
        try:
            response = requests.get(self.api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Check if timestamp is recent
                if 'timestamp' in data:
                    api_time = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00').replace('+00:00', ''))
                    api_age = (datetime.now() - api_time).total_seconds()
                    
                    if api_age > self.max_data_age:
                        self.log(f"❌ API data is {api_age:.0f} seconds old")
                        return False
                
                self.log("✅ API is healthy")
                return True
            else:
                self.log(f"❌ API returned status {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ API health check failed: {e}")
            return False
    
    def get_agentceli_processes(self):
        """Get all running AgentCeli processes"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'agentceli' in cmdline.lower() and 'python' in cmdline.lower():
                        if 'watchdog' not in cmdline.lower():  # Don't include ourselves
                            processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.log(f"Error getting processes: {e}")
        
        return processes
    
    def stop_agentceli(self):
        """Stop all AgentCeli processes"""
        self.log("🛑 Stopping AgentCeli processes...")
        
        # Try using agentceli_control.py first
        try:
            result = subprocess.run(
                ["python3", "agentceli_control.py", "stop"],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                self.log("✅ AgentCeli stopped via control script")
                time.sleep(5)
                return True
        except Exception as e:
            self.log(f"⚠️ Control script stop failed: {e}")
        
        # Fallback: kill processes manually
        processes = self.get_agentceli_processes()
        for proc in processes:
            try:
                self.log(f"🔪 Killing process {proc.pid}: {' '.join(proc.info['cmdline'])}")
                proc.terminate()
                proc.wait(timeout=10)
            except Exception as e:
                self.log(f"⚠️ Failed to kill process {proc.pid}: {e}")
                try:
                    proc.kill()
                except:
                    pass
        
        time.sleep(3)
        return len(self.get_agentceli_processes()) == 0
    
    def start_agentceli(self):
        """Start AgentCeli system"""
        self.log("🚀 Starting AgentCeli...")
        
        try:
            # Try using agentceli_control.py first
            result = subprocess.run(
                ["python3", "agentceli_control.py", "start"],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log("✅ AgentCeli started via control script")
                time.sleep(10)  # Give it time to initialize
                return True
            else:
                self.log(f"⚠️ Control script failed: {result.stderr}")
        except Exception as e:
            self.log(f"⚠️ Control script start failed: {e}")
        
        # Fallback: start hybrid directly
        try:
            self.log("🔄 Starting agentceli_hybrid.py directly...")
            proc = subprocess.Popen(
                ["python3", "agentceli_hybrid.py"],
                cwd=self.base_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            time.sleep(15)  # Give it time to start
            
            if proc.poll() is None:  # Still running
                self.log("✅ AgentCeli hybrid started successfully")
                return True
            else:
                self.log("❌ AgentCeli hybrid failed to start")
                return False
                
        except Exception as e:
            self.log(f"❌ Failed to start AgentCeli: {e}")
            return False
    
    def restart_agentceli(self):
        """Restart AgentCeli system"""
        self.restart_count += 1
        self.log(f"🔄 RESTARTING AgentCeli (restart #{self.restart_count})")
        
        # Stop current processes
        if not self.stop_agentceli():
            self.log("⚠️ Failed to cleanly stop AgentCeli")
        
        # Start new process
        if self.start_agentceli():
            self.log("✅ AgentCeli restarted successfully")
            return True
        else:
            self.log("❌ Failed to restart AgentCeli")
            return False
    
    def health_check(self):
        """Perform comprehensive health check"""
        self.log("🔍 Performing health check...")
        
        data_fresh = self.check_data_freshness()
        api_healthy = self.check_api_health()
        processes = self.get_agentceli_processes()
        
        self.log(f"📊 Health Status: Data={data_fresh}, API={api_healthy}, Processes={len(processes)}")
        
        # If both data and API are healthy, system is OK
        if data_fresh and api_healthy:
            return True
        
        # If no processes are running, definitely need restart
        if len(processes) == 0:
            self.log("❌ No AgentCeli processes running")
            return False
        
        # If either data or API is unhealthy, need restart
        if not data_fresh or not api_healthy:
            return False
        
        return True
    
    def run(self):
        """Main watchdog loop"""
        self.log("🐕 AgentCeli Watchdog started")
        self.log(f"⚙️ Check interval: {self.check_interval} seconds")
        self.log(f"⚙️ Max data age: {self.max_data_age} seconds")
        
        try:
            while True:
                try:
                    if not self.health_check():
                        self.log("🚨 Health check failed - restarting AgentCeli")
                        self.restart_agentceli()
                    else:
                        self.log("✅ System healthy")
                    
                    self.log(f"😴 Sleeping for {self.check_interval} seconds...")
                    time.sleep(self.check_interval)
                    
                except KeyboardInterrupt:
                    self.log("🛑 Watchdog stopped by user")
                    break
                except Exception as e:
                    self.log(f"❌ Unexpected error: {e}")
                    time.sleep(60)  # Wait a minute before retrying
                    
        except Exception as e:
            self.log(f"💥 Fatal error: {e}")
        
        self.log("🐕 Watchdog stopped")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Stopping watchdog...")
    sys.exit(0)

if __name__ == "__main__":
    # Handle Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Change to AgentCeli directory
    os.chdir(Path(__file__).parent)
    
    # Start watchdog
    watchdog = AgentCeliWatchdog()
    watchdog.run()