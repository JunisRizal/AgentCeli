#!/usr/bin/env python3
"""
Santiment Exchange Flow Data Collector
Collects inflow and outflow data as separate datasets using GraphQL
"""

import json
import time
from datetime import datetime
import logging
from pathlib import Path
import sys

# Import requests properly
if "/Users/julius/Desktop/AgentCeli" in sys.path:
    sys.path.remove("/Users/julius/Desktop/AgentCeli")

import requests as http_requests

class SantimentFlowCollector:
    def __init__(self, config_file="agentceli_config.json"):
        self.base_dir = Path(__file__).parent
        self.config = self.load_config(config_file)
        self.santiment_config = self.config["data_sources"]["paid_apis"]["santiment"]
        
        self.api_key = self.santiment_config["key"]
        self.endpoint = self.santiment_config["endpoint"]
        
        self.headers = {
            "Authorization": f"Apikey {self.api_key}",
            "Content-Type": "application/json"
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
            format='%(asctime)s - SANTIMENT_FLOWS - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
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
    
    def get_multi_asset_flows(self, from_date="2025-06-01T00:00:00Z", to_date="2025-07-29T00:00:00Z"):
        """Get inflow, outflow, and sentiment data for all assets in single query using user's exact format"""
        query = f'''
        {{
          btc_inflow: getMetric(metric: "exchange_inflow") {{
            timeseriesDataJson(
              slug: "bitcoin",
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
          btc_outflow: getMetric(metric: "exchange_outflow") {{
            timeseriesDataJson(
              slug: "bitcoin",
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
          btc_sentiment: getMetric(metric: "sentiment_balance_total") {{
            timeseriesDataJson(
              slug: "bitcoin",
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
          eth_inflow: getMetric(metric: "exchange_inflow") {{
            timeseriesDataJson(
              slug: "ethereum",
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
          eth_outflow: getMetric(metric: "exchange_outflow") {{
            timeseriesDataJson(
              slug: "ethereum",
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
          eth_sentiment: getMetric(metric: "sentiment_balance_total") {{
            timeseriesDataJson(
              slug: "ethereum",
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
          sol_inflow: getMetric(metric: "exchange_inflow") {{
            timeseriesDataJson(
              slug: "solana",
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
          sol_outflow: getMetric(metric: "exchange_outflow") {{
            timeseriesDataJson(
              slug: "solana",
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
          sol_sentiment: getMetric(metric: "sentiment_balance_total") {{
            timeseriesDataJson(
              slug: "solana",
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
          xrp_inflow: getMetric(metric: "exchange_inflow") {{
            timeseriesDataJson(
              slug: "ripple",
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
          xrp_outflow: getMetric(metric: "exchange_outflow") {{
            timeseriesDataJson(
              slug: "ripple",
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
          xrp_sentiment: getMetric(metric: "sentiment_balance_total") {{
            timeseriesDataJson(
              slug: "ripple",
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
          social_4chan: getMetric(metric: "social_volume_4chan") {{
            timeseriesDataPerSlugJson(
              selector: {{ slugs: ["bitcoin", "ethereum", "ripple", "solana"] }},
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
          social_bitcointalk: getMetric(metric: "social_volume_bitcointalk") {{
            timeseriesDataPerSlugJson(
              selector: {{ slugs: ["bitcoin", "ethereum", "ripple", "solana"] }},
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
          social_reddit: getMetric(metric: "social_volume_reddit") {{
            timeseriesDataPerSlugJson(
              selector: {{ slugs: ["bitcoin", "ethereum", "ripple", "solana"] }},
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
          social_telegram: getMetric(metric: "social_volume_telegram") {{
            timeseriesDataPerSlugJson(
              selector: {{ slugs: ["bitcoin", "ethereum", "ripple", "solana"] }},
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
          social_twitter: getMetric(metric: "social_volume_twitter") {{
            timeseriesDataPerSlugJson(
              selector: {{ slugs: ["bitcoin", "ethereum", "ripple", "solana"] }},
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
          social_youtube: getMetric(metric: "social_volume_youtube_videos") {{
            timeseriesDataPerSlugJson(
              selector: {{ slugs: ["bitcoin", "ethereum", "ripple", "solana"] }},
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
          social_farcaster: getMetric(metric: "social_volume_farcaster") {{
            timeseriesDataPerSlugJson(
              selector: {{ slugs: ["bitcoin", "ethereum", "ripple", "solana"] }},
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
          social_total: getMetric(metric: "social_volume_total") {{
            timeseriesDataPerSlugJson(
              selector: {{ slugs: ["bitcoin", "ethereum", "ripple", "solana"] }},
              from: "{from_date}",
              to: "{to_date}",
              interval: "1d"
            )
          }}
        }}
        '''
        
        self.logger.info(f"📊 Collecting multi-asset flow + sentiment + social data from {from_date} to {to_date}")
        result = self.run_query(query.strip())
        
        flow_data = {
            "timestamp": datetime.now().isoformat(),
            "data_source": "santiment",
            "date_range": {"from": from_date, "to": to_date},
            "cost_estimate": 0.02,  # Single efficient query for all assets + all metrics
            "assets": {
                "BTC": {
                    "inflows": [], "outflows": [], "sentiment": [],
                    "social": {
                        "4chan": [], "bitcointalk": [], "reddit": [], "telegram": [],
                        "twitter": [], "youtube": [], "farcaster": [], "total": []
                    }
                },
                "ETH": {
                    "inflows": [], "outflows": [], "sentiment": [],
                    "social": {
                        "4chan": [], "bitcointalk": [], "reddit": [], "telegram": [],
                        "twitter": [], "youtube": [], "farcaster": [], "total": []
                    }
                },
                "SOL": {
                    "inflows": [], "outflows": [], "sentiment": [],
                    "social": {
                        "4chan": [], "bitcointalk": [], "reddit": [], "telegram": [],
                        "twitter": [], "youtube": [], "farcaster": [], "total": []
                    }
                },
                "XRP": {
                    "inflows": [], "outflows": [], "sentiment": [],
                    "social": {
                        "4chan": [], "bitcointalk": [], "reddit": [], "telegram": [],
                        "twitter": [], "youtube": [], "farcaster": [], "total": []
                    }
                }
            }
        }
        
        if result and "data" in result:
            try:
                data = result["data"]
                
                # Process each asset's data
                assets_map = {
                    "btc": "BTC", "eth": "ETH", "sol": "SOL", "xrp": "XRP"
                }
                
                for asset_key, asset_symbol in assets_map.items():
                    # Process inflows
                    inflow_key = f"{asset_key}_inflow"
                    if inflow_key in data and data[inflow_key]["timeseriesDataJson"]:
                        timeseries_json = data[inflow_key]["timeseriesDataJson"]
                        if isinstance(timeseries_json, str):
                            inflow_timeseries = json.loads(timeseries_json)
                        else:
                            inflow_timeseries = timeseries_json
                        flow_data["assets"][asset_symbol]["inflows"] = inflow_timeseries
                    
                    # Process outflows
                    outflow_key = f"{asset_key}_outflow"
                    if outflow_key in data and data[outflow_key]["timeseriesDataJson"]:
                        timeseries_json = data[outflow_key]["timeseriesDataJson"]
                        if isinstance(timeseries_json, str):
                            outflow_timeseries = json.loads(timeseries_json)
                        else:
                            outflow_timeseries = timeseries_json
                        flow_data["assets"][asset_symbol]["outflows"] = outflow_timeseries
                    
                    # Process sentiment
                    sentiment_key = f"{asset_key}_sentiment"
                    if sentiment_key in data and data[sentiment_key]["timeseriesDataJson"]:
                        timeseries_json = data[sentiment_key]["timeseriesDataJson"]
                        if isinstance(timeseries_json, str):
                            sentiment_timeseries = json.loads(timeseries_json)
                        else:
                            sentiment_timeseries = timeseries_json
                        flow_data["assets"][asset_symbol]["sentiment"] = sentiment_timeseries
                
                # Process social volume data (different structure - timeseriesDataPerSlugJson)
                social_metrics = {
                    "social_4chan": "4chan",
                    "social_bitcointalk": "bitcointalk", 
                    "social_reddit": "reddit",
                    "social_telegram": "telegram",
                    "social_twitter": "twitter",
                    "social_youtube": "youtube",
                    "social_farcaster": "farcaster",
                    "social_total": "total"
                }
                
                slug_to_symbol = {
                    "bitcoin": "BTC", "ethereum": "ETH", "ripple": "XRP", "solana": "SOL"
                }
                
                # Process timeseriesDataPerSlugJson format (different from normal timeseriesDataJson)
                for social_key, platform_name in social_metrics.items():
                    if social_key in data and data[social_key].get("timeseriesDataPerSlugJson"):
                        # This format is: [{"data": [{"value": X, "slug": "bitcoin"}, ...], "datetime": "..."}, ...]
                        timeseries_data = data[social_key]["timeseriesDataPerSlugJson"]
                        
                        # Convert per-slug format to individual asset timeseries
                        for slug, symbol in slug_to_symbol.items():
                            asset_timeseries = []
                            
                            # Extract data for this specific asset from each timepoint
                            for timepoint in timeseries_data:
                                datetime_val = timepoint.get("datetime")
                                data_points = timepoint.get("data", [])
                                
                                # Find the data point for this asset slug
                                asset_value = None
                                for point in data_points:
                                    if point.get("slug") == slug:
                                        asset_value = point.get("value", 0)
                                        break
                                
                                if asset_value is not None:
                                    asset_timeseries.append({
                                        "datetime": datetime_val,
                                        "value": asset_value
                                    })
                            
                            # Store the converted timeseries
                            if asset_timeseries:
                                flow_data["assets"][symbol]["social"][platform_name] = asset_timeseries
                
                # Log collection summary
                for symbol, data_dict in flow_data["assets"].items():
                    inflow_count = len(data_dict["inflows"])
                    outflow_count = len(data_dict["outflows"])
                    sentiment_count = len(data_dict["sentiment"])
                    social_count = sum(len(platform_data) for platform_data in data_dict["social"].values() if platform_data)
                    self.logger.info(f"✅ {symbol}: {inflow_count} inflow, {outflow_count} outflow, {sentiment_count} sentiment, {social_count} social data points")
                
            except Exception as e:
                self.logger.error(f"Failed to process multi-asset flow data: {e}")
                self.logger.error(f"Raw response: {result}")
        
        return flow_data
    
    def get_ai_social_volume(self, from_date="2025-06-01T00:00:00Z", to_date="2025-07-29T00:00:00Z"):
        """Get AI social volume data for high-frequency monitoring (every 15 min)"""
        query = f'''
        {{
          getMetric(metric: "social_volume_ai_total") {{
            timeseriesDataJson(
              selector: {{ slug: "santiment" }},
              from: "{from_date}",
              to: "{to_date}",
              interval: "1h"
            )
          }}
        }}
        '''
        
        self.logger.info(f"🤖 Collecting AI social volume data from {from_date} to {to_date}")
        result = self.run_query(query.strip())
        
        ai_social_data = {
            "timestamp": datetime.now().isoformat(),
            "data_source": "santiment",
            "metric": "social_volume_ai_total",
            "date_range": {"from": from_date, "to": to_date},
            "interval": "1h",
            "cost_estimate": 0.02,
            "data": []
        }
        
        if result and "data" in result:
            try:
                timeseries_json = result["data"]["getMetric"]["timeseriesDataJson"]
                if timeseries_json:
                    if isinstance(timeseries_json, str):
                        timeseries_data = json.loads(timeseries_json)
                    else:
                        timeseries_data = timeseries_json
                    ai_social_data["data"] = timeseries_data
                    self.logger.info(f"✅ Collected {len(timeseries_data)} AI social volume data points")
                else:
                    self.logger.warning("⚠️ No AI social volume data returned")
            except Exception as e:
                self.logger.error(f"Failed to process AI social volume data: {e}")
                self.logger.error(f"Raw response: {result}")
        
        return ai_social_data
    
    def save_data(self, data, filename):
        """Save data to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory
        output_dir = self.base_dir / "santiment_data"
        output_dir.mkdir(exist_ok=True)
        
        # Save timestamped JSON
        json_file = output_dir / f"{filename}_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Save latest
        latest_file = output_dir / f"{filename}_latest.json"
        with open(latest_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"💾 Data saved: {json_file}")
        return str(json_file)
    
    def check_daily_limit(self):
        """Check if data has already been collected today"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        output_dir = self.base_dir / "santiment_data"
        latest_file = output_dir / "multi_asset_flows_latest.json"
        
        if latest_file.exists():
            try:
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                    last_collection = data.get('timestamp', '')
                    if last_collection.startswith(today):
                        return True
            except:
                pass
        return False
    
    def collect_all_flows(self, from_date="2025-06-01T00:00:00Z", to_date="2025-07-29T00:00:00Z"):
        """Collect multi-asset flow data in single query - ONCE PER DAY"""
        
        # Check if already collected today
        if self.check_daily_limit():
            self.logger.info("⏭️ Data already collected today - skipping to save API costs")
            print("⏭️ Multi-asset flow data already collected today")
            print("💰 Saving API costs by skipping duplicate collection")
            return None
        
        self.logger.info("🚀 Starting DAILY Multi-Asset Flow Data Collection...")
        
        # Collect all assets in single query (more efficient!)
        flow_data = self.get_multi_asset_flows(from_date, to_date)
        flow_file = self.save_data(flow_data, "multi_asset_flows")
        
        # Print summary
        print("\n💱 MULTI-ASSET FLOW DATA COLLECTION SUMMARY:")
        print("=" * 55)
        print(f"📅 Date Range: {from_date} to {to_date}")
        print(f"💰 API Cost: ${flow_data['cost_estimate']:.4f} (Single efficient query)")
        print(f"📁 Data File: {flow_file}")
        print()
        
        total_data_points = 0
        for symbol, asset_data in flow_data["assets"].items():
            inflow_count = len(asset_data["inflows"])
            outflow_count = len(asset_data["outflows"])
            sentiment_count = len(asset_data["sentiment"])
            total_data_points += inflow_count + outflow_count + sentiment_count
            
            # Calculate latest values if data exists
            latest_inflow = 0
            latest_outflow = 0
            latest_sentiment = 0
            net_flow = 0
            
            if asset_data["inflows"]:
                latest_inflow = asset_data["inflows"][-1].get("value", 0) or 0
            if asset_data["outflows"]:
                latest_outflow = asset_data["outflows"][-1].get("value", 0) or 0
            if asset_data["sentiment"]:
                latest_sentiment = asset_data["sentiment"][-1].get("value", 0) or 0
            net_flow = latest_inflow - latest_outflow
            
            print(f"📊 {symbol}:")
            print(f"   📈 Inflow Points: {inflow_count}")
            print(f"   📉 Outflow Points: {outflow_count}")
            print(f"   🧠 Sentiment Points: {sentiment_count}")
            if inflow_count > 0 or outflow_count > 0:
                print(f"   💰 Latest Net Flow: ${net_flow:,.2f}")
            if sentiment_count > 0:
                print(f"   📈 Latest Sentiment: {latest_sentiment:.3f}")
            print()
        
        print(f"📊 Total Data Points Collected: {total_data_points}")
        print(f"⏰ Next collection allowed: Tomorrow at same time")
        
        return {
            "multi_asset_flows": flow_data,
            "total_cost": flow_data['cost_estimate'],
            "data_points": total_data_points
        }

def main():
    """Main execution - DAILY COLLECTION ONLY"""
    collector = SantimentFlowCollector()
    
    if not collector.santiment_config.get("enabled", False):
        print("❌ Santiment API is disabled in config")
        return
    
    print("📅 Santiment Daily Collection - Cost-Efficient Mode")
    print("💰 API Cost: $0.02 per day (Single query: flows + sentiment)")
    print("⏰ Recommended: Run once daily via cron")
    
    # Collect flow data with your specified date range
    results = collector.collect_all_flows(
        from_date="2025-06-01T00:00:00Z",
        to_date="2025-07-29T00:00:00Z"
    )
    
    if results is None:
        print("\n✅ Daily limit respected - no additional API costs incurred")
    else:
        print(f"\n💰 Daily API cost: ${results['total_cost']:.4f}")
        print("⏰ Next collection allowed: Tomorrow")

if __name__ == "__main__":
    main()