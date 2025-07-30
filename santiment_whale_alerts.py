#!/usr/bin/env python3
"""
Santiment Whale Alerts Integration for AgentCeli
Collects whale transaction data, exchange flows, and sentiment
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging
import sys

# Import requests properly (avoid local file conflict)
if "/Users/julius/Desktop/AgentCeli" in sys.path:
    sys.path.remove("/Users/julius/Desktop/AgentCeli")

import requests as http_requests

class SantimentWhaleCollector:
    def __init__(self, config_file="agentceli_config.json"):
        self.base_dir = Path(__file__).parent
        self.config = self.load_config(config_file)
        self.santiment_config = self.config["data_sources"]["paid_apis"]["santiment"]
        
        self.api_key = self.santiment_config["key"]
        self.endpoint = self.santiment_config["endpoint"]
        self.metrics = self.santiment_config["metrics"]
        self.cost_per_call = self.santiment_config["cost_per_call"]
        
        self.headers = {
            "Authorization": f"Apikey {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Asset mapping (Santiment names)
        self.assets = {
            "bitcoin": "BTC",
            "ethereum": "ETH", 
            "ripple": "XRP",
            "solana": "SOL"
        }
        
        self.setup_logging()
        
    def load_config(self, config_file):
        """Load AgentCeli configuration"""
        try:
            with open(self.base_dir / config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load config: {e}")
            return {}
    
    def setup_logging(self):
        """Setup logging"""
        log_file = self.base_dir / "logs" / "santiment.log"
        log_file.parent.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - SANTIMENT - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def build_query(self, metric, assets, from_date, to_date, interval="1d"):
        """Build GraphQL query for Santiment API"""
        asset_list = json.dumps(list(assets.keys()))
        
        query_template = '''
        query {
            getMetric(metric: "%s") {
                timeseriesDataPerSlugJson(
                    selector: { slugs: %s },
                    from: "%s",
                    to: "%s",
                    interval: "%s"
                )
            }
        }
        ''' % (metric, asset_list, from_date, to_date, interval)
        
        return query_template.strip()
    
    def run_query(self, query):
        """Execute GraphQL query"""
        try:
            payload = {"query": query}
            response = http_requests.post(
                self.endpoint,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Query failed: {e}")
            return None
    
    def get_latest_whale_data(self, days_back=1):
        """Get latest whale data for all assets"""
        to_date = datetime.now().strftime("%Y-%m-%dT00:00:00Z")
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00Z")
        
        whale_data = {
            "timestamp": datetime.now().isoformat(),
            "data_source": "santiment",
            "cost_estimate": 0,
            "assets": {}
        }
        
        self.logger.info(f"🐋 Collecting whale data from {from_date} to {to_date}")
        
        # Collect data for each metric
        for metric in self.metrics:
            self.logger.info(f"📊 Collecting {metric}")
            
            query = self.build_query(metric, self.assets, from_date, to_date, "1d")
            result = self.run_query(query)
            
            if result and "data" in result:
                # Process each asset
                try:
                    metric_data = result["data"]["getMetric"]["timeseriesDataPerSlugJson"]
                    
                    for asset_slug, asset_symbol in self.assets.items():
                        if asset_symbol not in whale_data["assets"]:
                            whale_data["assets"][asset_symbol] = {}
                        
                        # Extract latest data point for this asset
                        if asset_slug in metric_data:
                            asset_timeseries = json.loads(metric_data[asset_slug])
                            
                            if asset_timeseries:
                                latest_point = asset_timeseries[-1]  # Most recent data
                                whale_data["assets"][asset_symbol][metric] = {
                                    "value": latest_point.get("value"),
                                    "timestamp": latest_point.get("datetime")
                                }
                    
                    whale_data["cost_estimate"] += self.cost_per_call
                    
                except Exception as e:
                    self.logger.error(f"Failed to process {metric}: {e}")
            
            # Rate limiting
            time.sleep(1)
        
        return whale_data
    
    def get_whale_alerts(self, threshold_usd=1000000):
        """Get whale transaction alerts above threshold"""
        whale_data = self.get_latest_whale_data(days_back=1)
        alerts = []
        
        for symbol, metrics in whale_data["assets"].items():
            whale_count = metrics.get("whale_transaction_count_1m_usd_to_inf", {})
            
            if whale_count.get("value", 0) > 0:
                alerts.append({
                    "symbol": symbol,
                    "whale_transactions": whale_count.get("value", 0),
                    "timestamp": whale_count.get("timestamp"),
                    "alert_level": "HIGH" if whale_count.get("value", 0) > 10 else "MEDIUM"
                })
        
        return {
            "alerts": alerts,
            "total_cost": whale_data["cost_estimate"],
            "timestamp": whale_data["timestamp"]
        }
    
    def save_data(self, data, filename_prefix="santiment"):
        """Save data to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory
        output_dir = self.base_dir / "santiment_data"
        output_dir.mkdir(exist_ok=True)
        
        # Save JSON
        json_file = output_dir / f"{filename_prefix}_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Save latest
        latest_file = output_dir / f"{filename_prefix}_latest.json"
        with open(latest_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"💾 Data saved: {json_file}")
        return str(json_file)
    
    def get_exchange_flows(self, from_date=None, to_date=None, interval="1d"):
        """Get exchange inflow and outflow data for specified date range"""
        if not from_date:
            from_date = "2025-06-01T00:00:00Z"
        if not to_date:
            to_date = "2025-07-29T00:00:00Z"
            
        flow_data = {
            "timestamp": datetime.now().isoformat(),
            "data_source": "santiment",
            "date_range": {"from": from_date, "to": to_date},
            "cost_estimate": 0,
            "exchange_flows": {}
        }
        
        self.logger.info(f"💱 Collecting exchange flows from {from_date} to {to_date}")
        
        # Collect inflow and outflow data
        for metric in ["exchange_inflow", "exchange_outflow"]:
            self.logger.info(f"📈 Collecting {metric}")
            
            query = self.build_query(metric, self.assets, from_date, to_date, interval)
            result = self.run_query(query)
            
            if result and "data" in result:
                try:
                    metric_data = result["data"]["getMetric"]["timeseriesDataPerSlugJson"]
                    
                    for asset_slug, asset_symbol in self.assets.items():
                        if asset_symbol not in flow_data["exchange_flows"]:
                            flow_data["exchange_flows"][asset_symbol] = {
                                "inflows": [],
                                "outflows": [],
                                "net_flows": []
                            }
                        
                        if asset_slug in metric_data:
                            asset_timeseries = json.loads(metric_data[asset_slug])
                            
                            if metric == "exchange_inflow":
                                flow_data["exchange_flows"][asset_symbol]["inflows"] = asset_timeseries
                            elif metric == "exchange_outflow":
                                flow_data["exchange_flows"][asset_symbol]["outflows"] = asset_timeseries
                    
                    flow_data["cost_estimate"] += self.cost_per_call
                    
                except Exception as e:
                    self.logger.error(f"Failed to process {metric}: {e}")
            
            time.sleep(1)
        
        # Calculate net flows
        for symbol in flow_data["exchange_flows"]:
            inflows = flow_data["exchange_flows"][symbol]["inflows"]
            outflows = flow_data["exchange_flows"][symbol]["outflows"]
            net_flows = []
            
            # Match timestamps and calculate net flow
            for inflow_point in inflows:
                matching_outflow = next(
                    (o for o in outflows if o.get("datetime") == inflow_point.get("datetime")), 
                    {"value": 0}
                )
                
                net_value = (inflow_point.get("value", 0) or 0) - (matching_outflow.get("value", 0) or 0)
                net_flows.append({
                    "datetime": inflow_point.get("datetime"),
                    "value": net_value
                })
            
            flow_data["exchange_flows"][symbol]["net_flows"] = net_flows
        
        return flow_data

    def get_formatted_whale_summary(self):
        """Get formatted whale summary for API"""
        whale_data = self.get_latest_whale_data(days_back=1)
        
        summary = {
            "success": True,
            "source": "santiment",
            "cost": whale_data["cost_estimate"],
            "timestamp": whale_data["timestamp"],
            "whale_activity": {}
        }
        
        for symbol, metrics in whale_data["assets"].items():
            whale_count = metrics.get("whale_transaction_count_1m_usd_to_inf", {}).get("value", 0)
            inflow = metrics.get("exchange_inflow", {}).get("value", 0)
            outflow = metrics.get("exchange_outflow", {}).get("value", 0)
            sentiment = metrics.get("sentiment_balance_total", {}).get("value", 0)
            
            summary["whale_activity"][symbol] = {
                "whale_transactions": whale_count,
                "exchange_inflow": round(inflow, 2) if inflow else 0,
                "exchange_outflow": round(outflow, 2) if outflow else 0,
                "net_flow": round((inflow or 0) - (outflow or 0), 2),
                "sentiment_score": round(sentiment, 3) if sentiment else 0,
                "alert_level": "HIGH" if whale_count > 10 else "MEDIUM" if whale_count > 5 else "LOW"
            }
        
        return summary

def main():
    """Main execution"""
    collector = SantimentWhaleCollector()
    
    if not collector.santiment_config.get("enabled", False):
        print("❌ Santiment API is disabled in config")
        return
    
    print("🐋 Starting Santiment Data Collection...")
    
    # Get exchange flow data (inflow/outflow)
    print("\n💱 Collecting Exchange Flows...")
    flow_data = collector.get_exchange_flows()
    collector.save_data(flow_data, "exchange_flows")
    
    # Get whale data
    whale_data = collector.get_latest_whale_data()
    collector.save_data(whale_data, "whale_data")
    
    # Get alerts
    alerts = collector.get_whale_alerts()
    collector.save_data(alerts, "whale_alerts")
    
    # Print exchange flow summary
    print("\n💱 EXCHANGE FLOW SUMMARY:")
    print("=" * 40)
    for symbol, flows in flow_data["exchange_flows"].items():
        if flows["inflows"] and flows["outflows"]:
            latest_inflow = flows["inflows"][-1]["value"] if flows["inflows"] else 0
            latest_outflow = flows["outflows"][-1]["value"] if flows["outflows"] else 0
            net_flow = (latest_inflow or 0) - (latest_outflow or 0)
            
            print(f"{symbol}:")
            print(f"  Latest Inflow: ${latest_inflow:,.2f}" if latest_inflow else "  Latest Inflow: $0.00")
            print(f"  Latest Outflow: ${latest_outflow:,.2f}" if latest_outflow else "  Latest Outflow: $0.00")
            print(f"  Net Flow: ${net_flow:,.2f}")
            print(f"  Data Points: {len(flows['inflows'])}")
            print()
    
    # Print whale summary
    summary = collector.get_formatted_whale_summary()
    print("\n🐋 WHALE ACTIVITY SUMMARY:")
    print("=" * 40)
    for symbol, activity in summary["whale_activity"].items():
        print(f"{symbol}:")
        print(f"  Whale Transactions: {activity['whale_transactions']}")
        print(f"  Net Flow: ${activity['net_flow']:,.2f}")
        print(f"  Alert Level: {activity['alert_level']}")
        print(f"  Sentiment: {activity['sentiment_score']}")
        print()
    
    print(f"💰 Total Cost: ${flow_data['cost_estimate'] + summary['cost']:.4f}")

if __name__ == "__main__":
    main()