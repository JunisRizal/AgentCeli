#!/usr/bin/env python3
"""
AgentCeli Master Dashboard - Complete Control Panel
Features:
- Real-time data monitoring from all sources
- Santiment data visualization with charts
- Data source control (enable/disable APIs)
- Cost tracking and alerts
- Service management (start/stop collectors)
- Data export and analysis tools
"""

from flask import Flask, jsonify, render_template_string, request
import json
import sqlite3
import subprocess
import threading
import time
import os
import signal
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import logging

app = Flask(__name__)

class AgentCeliMasterDashboard:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.config_file = self.base_dir / "agentceli_config.json"
        
        # Data directories
        self.correlation_dir = self.base_dir / "correlation_data"
        self.santiment_dir = self.base_dir / "santiment_data"
        
        # Service management
        self.running_services = {}
        self.service_logs = defaultdict(list)
        
        # Load configuration
        self.load_config()
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup dashboard logging"""
        log_file = self.base_dir / "logs" / "dashboard.log"
        log_file.parent.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - DASHBOARD - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_config(self):
        """Load AgentCeli configuration"""
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            self.config = self.get_default_config()
            
    def get_default_config(self):
        """Default configuration if file missing"""
        return {
            "data_sources": {
                "free_apis": {
                    "binance": {"enabled": True, "priority": "high"},
                    "coinbase": {"enabled": True, "priority": "medium"},
                    "coingecko": {"enabled": True, "priority": "high"},
                    "fear_greed": {"enabled": True, "priority": "medium"}
                },
                "paid_apis": {
                    "santiment": {
                        "enabled": True, 
                        "key": "7zelhlvci5blrymf_o5vruhdpz42smn7t",
                        "cost_per_call": 0.02
                    }
                }
            },
            "data_delivery": {
                "http_api": {"enabled": True, "port": 8080}
            },
            "rate_limits": {
                "daily_cost_limit": 5.00,
                "santiment_max_calls_per_hour": 10
            }
        }
        
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info("Configuration saved")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            return False
            
    def get_live_data(self):
        """Get latest live data from all sources"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "agentceli_data": self.get_agentceli_data(),
            "santiment_data": self.get_santiment_summary(),
            "service_status": self.get_service_status(),
            "data_sources": self.get_data_source_status(),
            "costs": self.get_cost_summary(),
            "real_time_details": self.get_realtime_collection_details()
        }
        return data
        
    def get_realtime_collection_details(self):
        """Get detailed breakdown of what's actually being collected"""
        details = {
            "active_collectors": [],
            "data_frequency": {},
            "last_collection_times": {},
            "data_points_per_source": {},
            "file_sizes": {}
        }
        
        # Check AgentCeli hybrid data
        hybrid_file = self.correlation_dir / "hybrid_latest.json"
        if hybrid_file.exists():
            try:
                with open(hybrid_file, 'r') as f:
                    hybrid_data = json.load(f)
                    
                details["active_collectors"].append("AgentCeli Hybrid")
                details["data_frequency"]["agentceli_hybrid"] = "Every 5 minutes"
                details["last_collection_times"]["agentceli_hybrid"] = hybrid_data.get("timestamp")
                
                # Count data points
                binance_pairs = len(hybrid_data.get("live_prices", {}).get("binance", {}))
                coingecko_coins = len(hybrid_data.get("sources", {}).get("coingecko", {}))
                
                details["data_points_per_source"]["binance"] = f"{binance_pairs} trading pairs"
                details["data_points_per_source"]["coingecko"] = f"{coingecko_coins} coins"
                details["data_points_per_source"]["fear_greed"] = "1 sentiment index"
                
                details["file_sizes"]["hybrid_latest.json"] = f"{hybrid_file.stat().st_size} bytes"
                
            except Exception as e:
                self.logger.error(f"Error reading hybrid data: {e}")
        
        # Check Santiment data
        santiment_files = list(self.santiment_dir.glob("*latest.json"))
        if santiment_files:
            details["active_collectors"].append("Santiment APIs")
            details["data_frequency"]["santiment_flows"] = "Daily"
            details["data_frequency"]["santiment_ai_social"] = "Every 15 minutes"
            
            for file in santiment_files:
                file_size = file.stat().st_size
                details["file_sizes"][file.name] = f"{file_size} bytes"
        
        # Check database
        db_file = self.correlation_dir / "hybrid_crypto_data.db"
        if db_file.exists():
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM live_prices")
                total_records = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(DISTINCT symbol) FROM live_prices")
                unique_symbols = cursor.fetchone()[0]
                conn.close()
                
                details["data_points_per_source"]["database"] = f"{total_records} total records, {unique_symbols} symbols"
                details["file_sizes"]["hybrid_crypto_data.db"] = f"{db_file.stat().st_size} bytes"
                
            except Exception as e:
                self.logger.error(f"Error reading database: {e}")
        
        return details
        
    def get_agentceli_data(self):
        """Get AgentCeli hybrid data"""
        try:
            latest_file = self.correlation_dir / "hybrid_latest.json"
            if latest_file.exists():
                with open(latest_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load AgentCeli data: {e}")
        return None
        
    def get_santiment_summary(self):
        """Get Santiment data summary"""
        try:
            # Multi-asset flows
            flows_file = self.santiment_dir / "multi_asset_flows_latest.json"
            ai_social_file = self.santiment_dir / "ai_social_latest.json"
            whale_data_file = self.santiment_dir / "whale_data_latest.json"
            
            summary = {
                "multi_asset_flows": None,
                "ai_social": None,
                "whale_data": None,
                "total_files": len(list(self.santiment_dir.glob("*.json")))
            }
            
            if flows_file.exists():
                with open(flows_file, 'r') as f:
                    flows_data = json.load(f)
                    summary["multi_asset_flows"] = {
                        "timestamp": flows_data.get("timestamp"),
                        "cost": flows_data.get("cost_estimate", 0),
                        "assets": list(flows_data.get("assets", {}).keys()),
                        "date_range": flows_data.get("date_range")
                    }
                    
            if ai_social_file.exists():
                with open(ai_social_file, 'r') as f:
                    ai_data = json.load(f)
                    summary["ai_social"] = {
                        "timestamp": ai_data.get("timestamp"),
                        "data_points": len(ai_data.get("data", [])),
                        "latest_value": ai_data.get("data", [{}])[-1].get("value", 0) if ai_data.get("data") else 0
                    }
                    
            if whale_data_file.exists():
                with open(whale_data_file, 'r') as f:
                    whale_data = json.load(f)
                    summary["whale_data"] = {
                        "timestamp": whale_data.get("timestamp"),
                        "alerts": len(whale_data.get("whale_alerts", []))
                    }
                    
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to load Santiment summary: {e}")
            return None
            
    def get_service_status(self):
        """Get status of all services"""
        services = {
            "agentceli_hybrid": {
                "name": "AgentCeli Hybrid Collector",
                "file": "agentceli_hybrid.py",
                "port": 8080,
                "status": "unknown",
                "description": "Main data collector (free APIs)"
            },
            "santiment_flows": {
                "name": "Santiment Exchange Flows",
                "file": "santiment_exchange_flows.py", 
                "port": None,
                "status": "unknown",
                "description": "Daily exchange flow data"
            },
            "santiment_ai_social": {
                "name": "Santiment AI Social Monitor",
                "file": "santiment_ai_social_monitor.py",
                "port": None,
                "status": "unknown", 
                "description": "15-minute AI social volume"
            },
            "datasource_monitor": {
                "name": "Data Source Monitor Dashboard",
                "file": "datasource_monitor_dashboard.py",
                "port": 8090,
                "status": "unknown",
                "description": "API monitoring dashboard"
            }
        }
        
        # Check if services are running
        for service_id, service in services.items():
            if service_id in self.running_services:
                services[service_id]["status"] = "running"
                services[service_id]["pid"] = self.running_services[service_id].get("pid")
            else:
                # Check if port is in use (for services with ports)
                if service.get("port"):
                    if self.is_port_in_use(service["port"]):
                        services[service_id]["status"] = "running"
                    else:
                        services[service_id]["status"] = "stopped"
                else:
                    services[service_id]["status"] = "stopped"
                    
        return services
        
    def is_port_in_use(self, port):
        """Check if port is in use"""
        try:
            result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                  capture_output=True, text=True)
            return bool(result.stdout.strip())
        except:
            return False
            
    def get_data_source_status(self):
        """Get data source configuration and status"""
        sources = {}
        
        # Free APIs
        if "free_apis" in self.config.get("data_sources", {}):
            for name, config in self.config["data_sources"]["free_apis"].items():
                sources[name] = {
                    "type": "FREE",
                    "enabled": config.get("enabled", False),
                    "priority": config.get("priority", "medium"),
                    "cost_per_day": 0.0,
                    "description": self.get_source_description(name)
                }
                
        # Paid APIs
        if "paid_apis" in self.config.get("data_sources", {}):
            for name, config in self.config["data_sources"]["paid_apis"].items():
                sources[name] = {
                    "type": "PAID",
                    "enabled": config.get("enabled", False),
                    "cost_per_call": config.get("cost_per_call", 0.0),
                    "cost_per_day": self.estimate_daily_cost(name, config),
                    "description": self.get_source_description(name)
                }
                
        return sources
        
    def get_source_description(self, source_name):
        """Get description for data source"""
        descriptions = {
            "binance": "Live crypto prices, volumes, 24h changes",
            "coinbase": "Spot prices, order books, market data",
            "coingecko": "Market caps, price changes, supply data",
            "fear_greed": "Market sentiment indicator (0-100)",
            "santiment": "Whale flows, exchange data, social sentiment"
        }
        return descriptions.get(source_name, "Cryptocurrency data source")
        
    def estimate_daily_cost(self, source_name, config):
        """Estimate daily cost for paid APIs"""
        cost_per_call = config.get("cost_per_call", 0)
        
        # Estimate calls per day based on source
        if source_name == "santiment":
            # 1 daily call for flows + 96 calls for 15-min AI social
            daily_calls = 1 + (24 * 4)  # 97 calls per day
            return daily_calls * cost_per_call
            
        return cost_per_call
        
    def get_cost_summary(self):
        """Get cost summary and budget tracking"""
        total_daily = 0.0
        paid_sources = self.config.get("data_sources", {}).get("paid_apis", {})
        
        for name, config in paid_sources.items():
            if config.get("enabled"):
                daily_cost = self.estimate_daily_cost(name, config)
                total_daily += daily_cost
                
        budget_limit = self.config.get("rate_limits", {}).get("daily_cost_limit", 5.0)
        
        return {
            "total_daily": total_daily,
            "monthly_estimate": total_daily * 30,
            "budget_limit": budget_limit,
            "budget_used_percent": (total_daily / budget_limit * 100) if budget_limit > 0 else 0,
            "within_budget": total_daily <= budget_limit
        }
        
    def start_service(self, service_name):
        """Start a service"""
        services = self.get_service_status()
        if service_name not in services:
            return {"success": False, "error": "Unknown service"}
            
        service = services[service_name]
        script_path = self.base_dir / service["file"]
        
        if not script_path.exists():
            return {"success": False, "error": f"Script {service['file']} not found"}
            
        try:
            # Kill existing process on port if needed
            if service.get("port") and self.is_port_in_use(service["port"]):
                subprocess.run(['lsof', '-ti', f':{service["port"]}', '|', 'xargs', 'kill', '-9'], 
                             shell=True, capture_output=True)
                time.sleep(2)
                
            # Start the service
            process = subprocess.Popen([
                "python3", str(script_path)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
               text=True, cwd=str(self.base_dir))
            
            self.running_services[service_name] = {
                "process": process,
                "pid": process.pid,
                "started_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"Started service {service_name} (PID: {process.pid})")
            return {"success": True, "pid": process.pid}
            
        except Exception as e:
            self.logger.error(f"Failed to start {service_name}: {e}")
            return {"success": False, "error": str(e)}
            
    def stop_service(self, service_name):
        """Stop a service"""
        if service_name not in self.running_services:
            return {"success": False, "error": "Service not running"}
            
        try:
            process = self.running_services[service_name]["process"]
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                
            del self.running_services[service_name]
            self.logger.info(f"Stopped service {service_name}")
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"Failed to stop {service_name}: {e}")
            return {"success": False, "error": str(e)}
            
    def toggle_data_source(self, source_name, enabled):
        """Enable/disable a data source"""
        updated = False
        
        # Check free APIs
        if "free_apis" in self.config.get("data_sources", {}):
            if source_name in self.config["data_sources"]["free_apis"]:
                self.config["data_sources"]["free_apis"][source_name]["enabled"] = enabled
                updated = True
                
        # Check paid APIs
        if "paid_apis" in self.config.get("data_sources", {}):
            if source_name in self.config["data_sources"]["paid_apis"]:
                self.config["data_sources"]["paid_apis"][source_name]["enabled"] = enabled
                updated = True
                
        if updated:
            if self.save_config():
                self.logger.info(f"Data source {source_name} {'enabled' if enabled else 'disabled'}")
                return {"success": True}
            else:
                return {"success": False, "error": "Failed to save configuration"}
        else:
            return {"success": False, "error": "Data source not found"}
            
    def get_santiment_chart_data(self):
        """Get Santiment data formatted for charts"""
        try:
            flows_file = self.santiment_dir / "multi_asset_flows_latest.json"
            if not flows_file.exists():
                return {"success": False, "error": "No Santiment data available"}
                
            with open(flows_file, 'r') as f:
                data = json.load(f)
                
            # Extract latest values for each asset
            chart_data = {
                "labels": [],
                "datasets": [
                    {
                        "label": "Exchange Inflows",
                        "data": [],
                        "backgroundColor": "rgba(72, 187, 120, 0.6)",
                        "borderColor": "rgba(72, 187, 120, 1)",
                        "borderWidth": 2
                    },
                    {
                        "label": "Exchange Outflows",
                        "data": [],
                        "backgroundColor": "rgba(245, 101, 101, 0.6)",
                        "borderColor": "rgba(245, 101, 101, 1)",
                        "borderWidth": 2
                    }
                ]
            }
            
            assets = data.get("assets", {})
            for asset_name, asset_data in assets.items():
                chart_data["labels"].append(asset_name)
                
                # Get latest inflow value
                inflows = asset_data.get("inflows", [])
                latest_inflow = inflows[-1].get("value", 0) if inflows else 0
                chart_data["datasets"][0]["data"].append(latest_inflow)
                
                # Get latest outflow value (make positive for display)
                outflows = asset_data.get("outflows", [])
                latest_outflow = abs(outflows[-1].get("value", 0)) if outflows else 0
                chart_data["datasets"][1]["data"].append(latest_outflow)
                
            return {"success": True, "chart_data": chart_data}
            
        except Exception as e:
            self.logger.error(f"Failed to generate chart data: {e}")
            return {"success": False, "error": str(e)}

# Global dashboard instance
dashboard = AgentCeliMasterDashboard()

@app.route('/')
def main_dashboard():
    """Main dashboard HTML interface"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🐙 AgentCeli Master Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        
        .header h1 { 
            font-size: 2.5rem; 
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .status-bar {
            display: flex;
            justify-content: space-around;
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        
        .status-item {
            text-align: center;
            flex: 1;
        }
        
        .status-value {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .status-label {
            color: #666;
            font-size: 0.9rem;
        }
        
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); 
            gap: 25px; 
            margin-bottom: 30px; 
        }
        
        .panel {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .panel:hover { transform: translateY(-5px); }
        
        .panel h2 {
            color: #333;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 1.3rem;
        }
        
        .service-item, .source-item {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .service-info h4 { margin-bottom: 5px; color: #333; }
        .service-info p { color: #666; font-size: 0.85rem; }
        
        .status-badge {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status-running { background: #d4edda; color: #155724; }
        .status-stopped { background: #f8d7da; color: #721c24; }
        .status-unknown { background: #e2e3e5; color: #383d41; }
        
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s ease;
            margin-left: 10px;
        }
        
        .btn-primary { background: #667eea; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        
        .toggle-switch {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 24px;
        }
        
        .toggle-switch input { opacity: 0; width: 0; height: 0; }
        
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 24px;
        }
        
        .slider:before {
            position: absolute;
            content: "";
            height: 18px; width: 18px;
            left: 3px; bottom: 3px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        
        input:checked + .slider { background-color: #667eea; }
        input:checked + .slider:before { transform: translateX(26px); }
        
        .chart-container { 
            height: 300px; 
            margin-top: 20px; 
            position: relative;
        }
        
        .cost-summary {
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 20px;
        }
        
        .cost-value { font-size: 2.5rem; font-weight: bold; margin-bottom: 5px; }
        .cost-subtitle { opacity: 0.9; }
        
        .refresh-btn {
            position: fixed;
            bottom: 30px; right: 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 50px;
            width: 60px; height: 60px;
            font-size: 1.5rem;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
            transition: transform 0.3s ease;
        }
        
        .refresh-btn:hover { transform: scale(1.1); }
        
        .alert {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
        }
        
        .alert-success { background: #d4edda; color: #155724; border-left: 4px solid #28a745; }
        .alert-warning { background: #fff3cd; color: #856404; border-left: 4px solid #ffc107; }
        .alert-danger { background: #f8d7da; color: #721c24; border-left: 4px solid #dc3545; }
        
        .loading { text-align: center; padding: 20px; color: #666; }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .pulse { animation: pulse 2s infinite; }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .data-table th {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        
        .data-table td {
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        
        .data-table tr:hover {
            background: #f8f9fa;
        }
        
        .source-badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .source-binance { background: #f0b90b; color: #000; }
        .source-coingecko { background: #8dc647; color: white; }
        .source-fear-greed { background: #6c5ce7; color: white; }
        .source-santiment { background: #0984e3; color: white; }
        
        .value-positive { color: #00b894; font-weight: bold; }
        .value-negative { color: #e17055; font-weight: bold; }
        .value-neutral { color: #636e72; }
        
        .timestamp { font-size: 0.8rem; color: #666; }
        
        .data-category {
            background: #f1f3f4;
            font-weight: bold;
            color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐙 AgentCeli Master Dashboard</h1>
            <p>Real-time cryptocurrency data collection and monitoring system</p>
        </div>
        
        <div class="status-bar">
            <div class="status-item">
                <div class="status-value" id="total-cost">$0.00</div>
                <div class="status-label">Daily Costs</div>
            </div>
            <div class="status-item">
                <div class="status-value" id="active-services">0</div>
                <div class="status-label">Active Services</div>
            </div>
            <div class="status-item">
                <div class="status-value" id="data-sources">0</div>
                <div class="status-label">Data Sources</div>
            </div>
            <div class="status-item">
                <div class="status-value" id="last-update">--:--</div>
                <div class="status-label">Last Update</div>
            </div>
        </div>
        
        <div class="grid">
            <!-- Services Control Panel -->
            <div class="panel">
                <h2>🚀 Services Control</h2>
                <div id="services-container" class="loading">
                    <div class="pulse">Loading services...</div>
                </div>
            </div>
            
            <!-- Data Sources Control -->
            <div class="panel">
                <h2>📡 Data Sources</h2>
                <div id="sources-container" class="loading">
                    <div class="pulse">Loading data sources...</div>
                </div>
            </div>
            
            <!-- Live Data Values Table -->
            <div class="panel" style="grid-column: 1 / -1;">
                <h2>📊 Current Data Values - Live Collection</h2>
                <div id="live-data-values-container" class="loading">
                    <div class="pulse">Loading current data values...</div>
                </div>
            </div>
            
            <!-- Real-time Collection Details -->
            <div class="panel">
                <h2>🔍 Real-time Collection Details</h2>
                <div id="realtime-details-container" class="loading">
                    <div class="pulse">Loading collection details...</div>
                </div>
            </div>
            
            <!-- Santiment Charts -->
            <div class="panel">
                <h2>📈 Santiment Exchange Flows</h2>
                <div class="alert alert-success">
                    <strong>Live Data:</strong> BTC, ETH, SOL, XRP exchange flows and sentiment
                </div>
                <canvas id="santimentChart" class="chart-container"></canvas>
            </div>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="refreshAll()" title="Refresh All Data">🔄</button>
    
    <script>
        let santimentChart = null;
        let refreshInterval = null;
        
        function refreshAll() {
            loadDashboardData();
            loadSantimentChart();
            loadRealtimeDetails();
            loadLiveDataValues();
        }
        
        function loadDashboardData() {
            fetch('/api/dashboard/data')
                .then(response => response.json())
                .then(data => updateDashboard(data))
                .catch(error => {
                    console.error('Error loading dashboard:', error);
                    showError('Failed to load dashboard data');
                });
        }
        
        function loadSantimentChart() {
            fetch('/api/santiment/chart-data')
                .then(response => response.json())
                .then(data => updateSantimentChart(data))
                .catch(error => {
                    console.error('Error loading Santiment data:', error);
                });
        }
        
        function loadRealtimeDetails() {
            fetch('/api/realtime/details')
                .then(response => response.json())
                .then(data => updateRealtimeDetails(data))
                .catch(error => {
                    console.error('Error loading realtime details:', error);
                });
        }
        
        function loadLiveDataValues() {
            fetch('/api/dashboard/data')
                .then(response => response.json())
                .then(data => updateLiveDataValues(data.agentceli_data, data.santiment_data))
                .catch(error => {
                    console.error('Error loading live data values:', error);
                });
        }
        
        function updateDashboard(data) {
            // Update status bar
            document.getElementById('total-cost').textContent = '$' + (data.costs?.total_daily || 0).toFixed(2);
            
            const activeServices = Object.values(data.service_status || {}).filter(s => s.status === 'running').length;
            document.getElementById('active-services').textContent = activeServices;
            
            const enabledSources = Object.values(data.data_sources || {}).filter(s => s.enabled).length;
            document.getElementById('data-sources').textContent = enabledSources;
            
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
            
            // Update services
            updateServices(data.service_status || {});
            
            // Update data sources
            updateDataSources(data.data_sources || {});
            
            // Update live data
            updateLiveData(data);
        }
        
        function updateServices(services) {
            const container = document.getElementById('services-container');
            container.innerHTML = '';
            
            Object.entries(services).forEach(([id, service]) => {
                const div = document.createElement('div');
                div.className = 'service-item';
                div.innerHTML = `
                    <div class="service-info">
                        <h4>${service.name}</h4>
                        <p>${service.description}</p>
                    </div>
                    <div>
                        <span class="status-badge status-${service.status}">${service.status}</span>
                        <button class="btn ${service.status === 'running' ? 'btn-danger' : 'btn-success'}" 
                                onclick="${service.status === 'running' ? 'stopService' : 'startService'}('${id}')">
                            ${service.status === 'running' ? 'Stop' : 'Start'}
                        </button>
                    </div>
                `;
                container.appendChild(div);
            });
        }
        
        function updateDataSources(sources) {
            const container = document.getElementById('sources-container');
            container.innerHTML = '';
            
            Object.entries(sources).forEach(([name, source]) => {
                const div = document.createElement('div');
                div.className = 'source-item';
                div.innerHTML = `
                    <div class="service-info">
                        <h4>${name.toUpperCase()} <span style="color: ${source.type === 'FREE' ? '#28a745' : '#ffc107'}; font-size: 0.8rem;">${source.type}</span></h4>
                        <p>${source.description}</p>
                        <small>Daily cost: $${source.cost_per_day?.toFixed(4) || '0.0000'}</small>
                    </div>
                    <div>
                        <label class="toggle-switch">
                            <input type="checkbox" ${source.enabled ? 'checked' : ''} 
                                   onchange="toggleDataSource('${name}', this.checked)">
                            <span class="slider"></span>
                        </label>
                    </div>
                `;
                container.appendChild(div);
            });
        }
        
        function updateLiveData(data) {
            const container = document.getElementById('live-data-container');
            
            let html = '';
            
            // AgentCeli data
            if (data.agentceli_data) {
                const agentData = data.agentceli_data;
                html += `
                    <div class="alert alert-success">
                        <strong>AgentCeli Status:</strong> Active (${agentData.api_tier})<br>
                        <strong>Fear & Greed:</strong> ${agentData.fear_greed?.value} (${agentData.fear_greed?.value_classification})<br>
                        <strong>Sources:</strong> ${agentData.total_sources}
                    </div>
                `;
                
                // Show live prices
                if (agentData.live_prices?.binance) {
                    html += '<h4>Live Prices:</h4>';
                    Object.entries(agentData.live_prices.binance).forEach(([pair, data]) => {
                        const symbol = pair.replace('USDT', '');
                        const changeColor = data.change_24h >= 0 ? '#28a745' : '#dc3545';
                        html += `
                            <div style="display: flex; justify-content: space-between; padding: 5px 0;">
                                <span><strong>${symbol}</strong></span>
                                <span>$${data.price.toLocaleString()}</span>
                                <span style="color: ${changeColor}">${data.change_24h >= 0 ? '+' : ''}${data.change_24h.toFixed(2)}%</span>
                            </div>
                        `;
                    });
                }
            }
            
            // Santiment data
            if (data.santiment_data) {
                const santiment = data.santiment_data;
                html += `
                    <div class="alert alert-warning">
                        <strong>Santiment Files:</strong> ${santiment.total_files}<br>
                        <strong>Assets:</strong> ${santiment.multi_asset_flows?.assets?.join(', ') || 'Loading...'}<br>
                        <strong>AI Social Volume:</strong> ${santiment.ai_social?.latest_value || 0}
                    </div>
                `;
            }
            
            if (!html) {
                html = '<div class="alert alert-danger">No live data available</div>';
            }
            
            container.innerHTML = html;
        }
        
        function updateRealtimeDetails(details) {
            const container = document.getElementById('realtime-details-container');
            
            let html = '';
            
            // Active collectors
            if (details.active_collectors && details.active_collectors.length > 0) {
                html += '<h4>🚀 Active Collectors:</h4>';
                details.active_collectors.forEach(collector => {
                    html += `<div class="alert alert-success">${collector}</div>`;
                });
            }
            
            // Data frequencies
            if (details.data_frequency && Object.keys(details.data_frequency).length > 0) {
                html += '<h4>⏰ Collection Frequencies:</h4>';
                Object.entries(details.data_frequency).forEach(([source, frequency]) => {
                    html += `<div style="padding: 5px 0;"><strong>${source}:</strong> ${frequency}</div>`;
                });
            }
            
            // Data points per source
            if (details.data_points_per_source && Object.keys(details.data_points_per_source).length > 0) {
                html += '<h4>📊 Data Points:</h4>';
                Object.entries(details.data_points_per_source).forEach(([source, count]) => {
                    html += `<div style="padding: 5px 0;"><strong>${source}:</strong> ${count}</div>`;
                });
            }
            
            // File sizes
            if (details.file_sizes && Object.keys(details.file_sizes).length > 0) {
                html += '<h4>💾 File Sizes:</h4>';
                Object.entries(details.file_sizes).forEach(([file, size]) => {
                    html += `<div style="padding: 5px 0;"><strong>${file}:</strong> ${size}</div>`;
                });
            }
            
            // Last collection times
            if (details.last_collection_times && Object.keys(details.last_collection_times).length > 0) {
                html += '<h4>🕐 Last Collections:</h4>';
                Object.entries(details.last_collection_times).forEach(([source, time]) => {
                    if (time) {
                        const date = new Date(time);
                        html += `<div style="padding: 5px 0;"><strong>${source}:</strong> ${date.toLocaleString()}</div>`;
                    }
                });
            }
            
            if (!html) {
                html = '<div class="alert alert-warning">No real-time collection details available</div>';
            }
            
            container.innerHTML = html;
        }
        
        function updateLiveDataValues(agentceliData, santimentData) {
            const container = document.getElementById('live-data-values-container');
            
            if (!agentceliData) {
                container.innerHTML = '<div class="alert alert-warning">No live data available from AgentCeli</div>';
                return;
            }
            
            let html = `
                <div class="alert alert-success">
                    <strong>Last Update:</strong> ${new Date(agentceliData.timestamp).toLocaleString()}
                    <strong style="margin-left: 20px;">API Tier:</strong> ${agentceliData.api_tier}
                    <strong style="margin-left: 20px;">Total Sources:</strong> ${agentceliData.total_sources}
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Asset</th>
                            <th>Data Type</th>
                            <th>Value</th>
                            <th>Source</th>
                            <th>Additional Info</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            // Binance Live Prices
            if (agentceliData.live_prices && agentceliData.live_prices.binance) {
                html += '<tr class="data-category"><td colspan="5">🏦 BINANCE - Live Trading Data</td></tr>';
                
                Object.entries(agentceliData.live_prices.binance).forEach(([pair, data]) => {
                    const symbol = pair.replace('USDT', '');
                    const changeClass = data.change_24h >= 0 ? 'value-positive' : 'value-negative';
                    
                    // Price row
                    html += `
                        <tr>
                            <td><strong>${symbol}</strong></td>
                            <td>Price</td>
                            <td><strong>$${data.price.toLocaleString()}</strong></td>
                            <td><span class="source-badge source-binance">Binance</span></td>
                            <td><span class="${changeClass}">${data.change_24h >= 0 ? '+' : ''}${data.change_24h}%</span></td>
                        </tr>
                    `;
                    
                    // Volume row
                    html += `
                        <tr>
                            <td></td>
                            <td>Volume 24h</td>
                            <td>${data.volume_24h.toLocaleString()}</td>
                            <td><span class="source-badge source-binance">Binance</span></td>
                            <td>Trading volume</td>
                        </tr>
                    `;
                });
            }
            
            // CoinGecko Market Data
            if (agentceliData.sources && agentceliData.sources.coingecko) {
                html += '<tr class="data-category"><td colspan="5">🦎 COINGECKO - Market Data</td></tr>';
                
                Object.entries(agentceliData.sources.coingecko).forEach(([coin, data]) => {
                    const symbol = coin.toUpperCase().replace('BITCOIN', 'BTC').replace('ETHEREUM', 'ETH').replace('RIPPLE', 'XRP').replace('SOLANA', 'SOL');
                    const changeClass = data.usd_24h_change >= 0 ? 'value-positive' : 'value-negative';
                    
                    // Price row
                    html += `
                        <tr>
                            <td><strong>${symbol}</strong></td>
                            <td>Market Price</td>
                            <td><strong>$${data.usd.toLocaleString()}</strong></td>
                            <td><span class="source-badge source-coingecko">CoinGecko</span></td>
                            <td><span class="${changeClass}">${data.usd_24h_change >= 0 ? '+' : ''}${data.usd_24h_change.toFixed(2)}%</span></td>
                        </tr>
                    `;
                    
                    // Market Cap row
                    html += `
                        <tr>
                            <td></td>
                            <td>Market Cap</td>
                            <td>$${(data.usd_market_cap / 1000000000).toFixed(2)}B</td>
                            <td><span class="source-badge source-coingecko">CoinGecko</span></td>
                            <td>Market capitalization</td>
                        </tr>
                    `;
                });
            }
            
            // Fear & Greed Index  
            if (agentceliData.fear_greed) {
                html += '<tr class="data-category"><td colspan="5">😨 FEAR & GREED INDEX - Market Sentiment</td></tr>';
                const fgValue = parseInt(agentceliData.fear_greed.value);
                const fgClass = fgValue >= 75 ? 'value-positive' : fgValue <= 25 ? 'value-negative' : 'value-neutral';
                
                html += `
                    <tr>
                        <td><strong>Market</strong></td>
                        <td>Sentiment Index</td>
                        <td><strong class="${fgClass}">${agentceliData.fear_greed.value}</strong></td>
                        <td><span class="source-badge source-fear-greed">Fear & Greed</span></td>
                        <td><strong>${agentceliData.fear_greed.value_classification}</strong></td>
                    </tr>
                `;
            }
            
            // Santiment Data Summary
            if (santimentData && santimentData.multi_asset_flows) {
                html += '<tr class="data-category"><td colspan="5">📊 SANTIMENT - On-chain & Social Data</td></tr>';
                
                const assets = santimentData.multi_asset_flows.assets || [];
                assets.forEach(asset => {
                    html += `
                        <tr>
                            <td><strong>${asset}</strong></td>
                            <td>Exchange Flows</td>
                            <td>Available</td>
                            <td><span class="source-badge source-santiment">Santiment</span></td>
                            <td>Inflows, outflows, sentiment</td>
                        </tr>
                    `;
                });
                
                if (santimentData.ai_social) {
                    html += `
                        <tr>
                            <td><strong>Market</strong></td>
                            <td>AI Social Volume</td>
                            <td>${santimentData.ai_social.latest_value || 0}</td>
                            <td><span class="source-badge source-santiment">Santiment</span></td>
                            <td>${santimentData.ai_social.data_points || 0} data points</td>
                        </tr>
                    `;
                }
            }
            
            html += '</tbody></table>';
            
            container.innerHTML = html;
        }
        
        function updateSantimentChart(response) {
            const ctx = document.getElementById('santimentChart').getContext('2d');
            
            if (santimentChart) {
                santimentChart.destroy();
            }
            
            if (response.success) {
                santimentChart = new Chart(ctx, {
                    type: 'bar',
                    data: response.chart_data,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            title: {
                                display: true,
                                text: 'Latest Exchange Flows by Asset'
                            },
                            legend: {
                                position: 'top'
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Flow Volume'
                                }
                            }
                        }
                    }
                });
            } else {
                ctx.canvas.style.display = 'none';
                const parent = ctx.canvas.parentElement;
                parent.innerHTML = '<div class="alert alert-warning">Santiment chart data not available</div>';
            }
        }
        
        function startService(serviceId) {
            fetch(`/api/services/${serviceId}/start`, { method: 'POST' })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        showSuccess(`Service ${serviceId} started successfully`);
                        setTimeout(refreshAll, 2000);
                    } else {
                        showError('Failed to start service: ' + result.error);
                    }
                });
        }
        
        function stopService(serviceId) {
            fetch(`/api/services/${serviceId}/stop`, { method: 'POST' })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        showSuccess(`Service ${serviceId} stopped successfully`);
                        setTimeout(refreshAll, 1000);
                    } else {
                        showError('Failed to stop service: ' + result.error);
                    }
                });
        }
        
        function toggleDataSource(sourceName, enabled) {
            fetch(`/api/sources/${sourceName}/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: enabled })
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    showSuccess(`Data source ${sourceName} ${enabled ? 'enabled' : 'disabled'}`);
                    setTimeout(refreshAll, 1000);
                } else {
                    showError('Failed to toggle data source: ' + result.error);
                    // Revert toggle
                    setTimeout(refreshAll, 500);
                }
            });
        }
        
        function showSuccess(message) {
            // Simple notification - could be enhanced with toast library
            console.log('SUCCESS:', message);
        }
        
        function showError(message) {
            console.error('ERROR:', message);
            alert('Error: ' + message);
        }
        
        // Initial load
        refreshAll();
        
        // Auto-refresh every 30 seconds
        refreshInterval = setInterval(refreshAll, 30000);
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (refreshInterval) clearInterval(refreshInterval);
        });
    </script>
</body>
</html>
    ''')

# API Endpoints
@app.route('/api/dashboard/data')
def get_dashboard_data():
    """Get all dashboard data"""
    return jsonify(dashboard.get_live_data())

@app.route('/api/services/<service_id>/start', methods=['POST'])
def start_service(service_id):
    """Start a service"""
    return jsonify(dashboard.start_service(service_id))

@app.route('/api/services/<service_id>/stop', methods=['POST'])  
def stop_service(service_id):
    """Stop a service"""
    return jsonify(dashboard.stop_service(service_id))

@app.route('/api/sources/<source_name>/toggle', methods=['POST'])
def toggle_data_source(source_name):
    """Toggle data source on/off"""
    data = request.get_json()
    enabled = data.get('enabled', False)
    return jsonify(dashboard.toggle_data_source(source_name, enabled))

@app.route('/api/santiment/chart-data')
def get_santiment_chart_data():
    """Get Santiment data for charts"""
    return jsonify(dashboard.get_santiment_chart_data())

@app.route('/api/realtime/details')
def get_realtime_details():
    """Get detailed real-time collection information"""
    return jsonify(dashboard.get_realtime_collection_details())

if __name__ == '__main__':
    print("🐙 AgentCeli Master Dashboard Starting...")
    print("🌐 Dashboard URL: http://localhost:8888")
    print("🎯 Features:")
    print("  ✅ Real-time data monitoring")
    print("  ✅ Service management (start/stop)")
    print("  ✅ Data source control panel")
    print("  ✅ Cost tracking & budget monitoring")
    print("  ✅ Santiment exchange flow charts")
    print("  ✅ Live price feeds & Fear/Greed index")
    print("="*60)
    
    try:
        app.run(host='127.0.0.1', port=8888, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped")
        # Stop all running services
        for service_name in list(dashboard.running_services.keys()):
            dashboard.stop_service(service_name)