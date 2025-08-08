#!/usr/bin/env python3
"""
Data Collection Watchdog - Monitors dataset count and shuts down AgentCeli if < 3 datasets for 30+ minutes
"""

import time
import subprocess
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import signal
import sys

class DataCollectionWatchdog:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.data_file = self.base_dir / "correlation_data" / "hybrid_latest.json"
        self.liquidation_file = self.base_dir / "liquidation_data" / "liquidation_analysis_latest.json"
        self.heatmap_file = self.base_dir / "liquidation_data" / "enhanced_liquidation_heatmap_latest.json"
        self.log_file = self.base_dir / "logs" / "data_watchdog.log"
        
        # Configuration
        self.check_interval = 300  # 5 minutes check interval
        self.shutdown_threshold = 1800  # 30 minutes (1800 seconds)
        self.min_datasets = 3
        
        # State tracking
        self.low_data_start_time = None
        self.last_dataset_count = 0
        
        # Ensure logs directory exists
        self.log_file.parent.mkdir(exist_ok=True)
        
    def log(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] DATA_WATCHDOG: {message}"
        print(log_message)
        
        try:
            with open(self.log_file, "a") as f:
                f.write(log_message + "\n")
        except Exception as e:
            print(f"Failed to write to log file: {e}")
    
    def count_datasets(self):
        """Count available datasets and check their freshness"""
        dataset_count = 0
        dataset_info = []
        current_time = datetime.now()
        max_age = 1800  # 30 minutes max age for data
        
        # Check hybrid price data
        if self.data_file.exists():
            try:
                file_mtime = datetime.fromtimestamp(self.data_file.stat().st_mtime)
                age_seconds = (current_time - file_mtime).total_seconds()
                
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                
                # Check if data has symbols and is recent
                if isinstance(data, dict) and 'symbols' in data and len(data['symbols']) > 0:
                    if age_seconds <= max_age:
                        dataset_count += 1
                        dataset_info.append(f"Price data ({len(data['symbols'])} symbols, {age_seconds:.0f}s old)")
                    else:
                        dataset_info.append(f"Price data (STALE: {age_seconds:.0f}s old)")
                
            except Exception as e:
                dataset_info.append(f"Price data (ERROR: {e})")
        else:
            dataset_info.append("Price data (MISSING)")
        
        # Check liquidation analysis data
        if self.liquidation_file.exists():
            try:
                file_mtime = datetime.fromtimestamp(self.liquidation_file.stat().st_mtime)
                age_seconds = (current_time - file_mtime).total_seconds()
                
                with open(self.liquidation_file, 'r') as f:
                    data = json.load(f)
                
                # Check if liquidation data has analysis results
                if isinstance(data, dict) and 'analysis' in data and len(data['analysis']) > 0:
                    if age_seconds <= max_age:
                        dataset_count += 1
                        dataset_info.append(f"Liquidation analysis ({len(data['analysis'])} symbols, {age_seconds:.0f}s old)")
                    else:
                        dataset_info.append(f"Liquidation analysis (STALE: {age_seconds:.0f}s old)")
                
            except Exception as e:
                dataset_info.append(f"Liquidation analysis (ERROR: {e})")
        else:
            dataset_info.append("Liquidation analysis (MISSING)")
        
        # Check enhanced liquidation heatmap
        if self.heatmap_file.exists():
            try:
                file_mtime = datetime.fromtimestamp(self.heatmap_file.stat().st_mtime)
                age_seconds = (current_time - file_mtime).total_seconds()
                
                with open(self.heatmap_file, 'r') as f:
                    data = json.load(f)
                
                # Check if heatmap has enhanced data
                if isinstance(data, dict) and 'enhanced_analysis' in data:
                    if age_seconds <= max_age:
                        dataset_count += 1
                        dataset_info.append(f"Enhanced heatmap ({age_seconds:.0f}s old)")
                    else:
                        dataset_info.append(f"Enhanced heatmap (STALE: {age_seconds:.0f}s old)")
                
            except Exception as e:
                dataset_info.append(f"Enhanced heatmap (ERROR: {e})")
        else:
            dataset_info.append("Enhanced heatmap (MISSING)")
        
        return dataset_count, dataset_info
    
    def get_agentceli_processes(self):
        """Get all running AgentCeli processes"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'agentceli' in cmdline.lower() and 'python' in cmdline.lower():
                        if 'data_collection_watchdog' not in cmdline.lower():  # Don't include ourselves
                            processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.log(f"Error getting processes: {e}")
        
        return processes
    
    def shutdown_agentceli(self):
        """Shutdown all AgentCeli processes"""
        self.log("🛑 SHUTTING DOWN AgentCeli - Dataset threshold exceeded")
        
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
        remaining_processes = self.get_agentceli_processes()
        
        if len(remaining_processes) == 0:
            self.log("✅ All AgentCeli processes stopped")
            return True
        else:
            self.log(f"⚠️ {len(remaining_processes)} processes still running")
            return False
    
    def check_data_health(self):
        """Check if data collection is healthy"""
        dataset_count, dataset_info = self.count_datasets()
        self.last_dataset_count = dataset_count
        
        current_time = datetime.now()
        
        self.log(f"📊 Found {dataset_count}/{self.min_datasets} valid datasets:")
        for info in dataset_info:
            self.log(f"   - {info}")
        
        # Check if we have enough datasets
        if dataset_count >= self.min_datasets:
            # Reset low data timer if we're back to healthy state
            if self.low_data_start_time:
                self.log(f"✅ Data collection recovered! Low data period lasted {(current_time - self.low_data_start_time).total_seconds():.0f} seconds")
                self.low_data_start_time = None
            return True
        else:
            # Start timer if this is the first time we detect low data
            if self.low_data_start_time is None:
                self.low_data_start_time = current_time
                self.log(f"⚠️ Low data collection detected! Started monitoring at {current_time.strftime('%H:%M:%S')}")
                return True  # Don't shutdown immediately
            else:
                # Check how long we've been in low data state
                low_data_duration = (current_time - self.low_data_start_time).total_seconds()
                remaining_time = self.shutdown_threshold - low_data_duration
                
                if remaining_time > 0:
                    self.log(f"⏰ Low data for {low_data_duration:.0f}s - Shutdown in {remaining_time:.0f}s")
                    return True  # Still within threshold
                else:
                    self.log(f"🚨 THRESHOLD EXCEEDED! Low data for {low_data_duration:.0f}s (threshold: {self.shutdown_threshold}s)")
                    return False  # Exceeded threshold, need to shutdown
    
    def run(self):
        """Main watchdog loop"""
        self.log("🐕 Data Collection Watchdog started")
        self.log(f"⚙️ Check interval: {self.check_interval} seconds")
        self.log(f"⚙️ Minimum datasets required: {self.min_datasets}")
        self.log(f"⚙️ Shutdown threshold: {self.shutdown_threshold} seconds ({self.shutdown_threshold/60:.1f} minutes)")
        
        try:
            while True:
                try:
                    # Check if AgentCeli processes are running
                    processes = self.get_agentceli_processes()
                    
                    if len(processes) == 0:
                        self.log("ℹ️ No AgentCeli processes running - watchdog monitoring only")
                        # Reset low data timer since no processes are running
                        self.low_data_start_time = None
                    else:
                        self.log(f"🔍 Monitoring {len(processes)} AgentCeli processes")
                        
                        # Check data health
                        if not self.check_data_health():
                            self.log("🚨 Data collection threshold exceeded - initiating shutdown")
                            
                            if self.shutdown_agentceli():
                                self.log("✅ AgentCeli shutdown completed")
                                # Reset timer after successful shutdown
                                self.low_data_start_time = None
                            else:
                                self.log("❌ Failed to fully shutdown AgentCeli")
                        else:
                            status = "✅ HEALTHY" if self.last_dataset_count >= self.min_datasets else "⚠️ MONITORING"
                            self.log(f"{status} - {self.last_dataset_count}/{self.min_datasets} datasets available")
                    
                    self.log(f"😴 Sleeping for {self.check_interval} seconds...")
                    time.sleep(self.check_interval)
                    
                except KeyboardInterrupt:
                    self.log("🛑 Data watchdog stopped by user")
                    break
                except Exception as e:
                    self.log(f"❌ Unexpected error: {e}")
                    time.sleep(60)  # Wait a minute before retrying
                    
        except Exception as e:
            self.log(f"💥 Fatal error: {e}")
        
        self.log("🐕 Data Collection Watchdog stopped")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Stopping data collection watchdog...")
    sys.exit(0)

if __name__ == "__main__":
    # Handle Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Change to AgentCeli directory
    os.chdir(Path(__file__).parent)
    
    # Start watchdog
    watchdog = DataCollectionWatchdog()
    watchdog.run()