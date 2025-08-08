#!/usr/bin/env python3
"""
Santiment AI Social Volume Monitor
High-frequency collection every 15 minutes for AI social volume data
"""

import json
import time
from datetime import datetime, timedelta
import logging
from pathlib import Path
import sys

# Import requests properly
if "/Users/julius/Desktop/AgentCeli" in sys.path:
    sys.path.remove("/Users/julius/Desktop/AgentCeli")

import requests as http_requests

class SantimentAISocialMonitor:
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
        log_file = self.base_dir / "logs" / "santiment_ai_social.log"
        log_file.parent.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - AI_SOCIAL - %(levelname)s - %(message)s',
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
    
    def check_15min_limit(self):
        """Check if data has been collected in the last 15 minutes"""
        now = datetime.now()
        fifteen_min_ago = now - timedelta(minutes=15)
        
        output_dir = self.base_dir / "santiment_data"
        latest_file = output_dir / "ai_social_latest.json"
        
        if latest_file.exists():
            try:
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                    last_collection = datetime.fromisoformat(data.get('timestamp', ''))
                    if last_collection > fifteen_min_ago:
                        return True
            except:
                pass
        return False
    
    def get_ai_social_volume(self, hours_back=24):
        """Get AI social volume for market gesamtheit (santiment)"""
        to_date = datetime.now().strftime("%Y-%m-%dT%H:00:00Z")
        from_date = (datetime.now() - timedelta(hours=hours_back)).strftime("%Y-%m-%dT%H:00:00Z")
        
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
        
        self.logger.info(f"🤖 Collecting AI social volume (Gesamtmarkt) from {from_date} to {to_date}")
        result = self.run_query(query.strip())
        
        ai_data = {
            "timestamp": datetime.now().isoformat(),
            "data_source": "santiment",
            "metric": "social_volume_ai_total",
            "scope": "gesamtmarkt",
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
                    ai_data["data"] = timeseries_data
                    self.logger.info(f"✅ Collected {len(timeseries_data)} AI social volume data points")
                else:
                    self.logger.warning("⚠️ No AI social volume data returned")
            except Exception as e:
                self.logger.error(f"Failed to process AI social volume data: {e}")
        
        return ai_data
    
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
        
        self.logger.info(f"💾 AI Social data saved: {json_file}")
        return str(json_file)
    
    def monitor_ai_social(self):
        """Main monitoring function - runs every 15 minutes"""
        
        # Check if we've collected in the last 15 minutes
        if self.check_15min_limit():
            self.logger.info("⏭️ AI social data collected recently - skipping to avoid over-polling")
            print("⏭️ AI social data collected within last 15 minutes")
            return None
        
        self.logger.info("🚀 Starting AI Social Volume Monitoring...")
        
        # Collect AI social volume data
        ai_data = self.get_ai_social_volume(hours_back=48)  # Get last 48 hours of hourly data
        ai_file = self.save_data(ai_data, "ai_social")
        
        # Print summary
        print("\n🤖 AI SOCIAL VOLUME MONITORING SUMMARY:")
        print("=" * 50)
        print(f"📅 Scope: Gesamtmarkt (santiment)")
        print(f"⏰ Interval: 1h (collected every 15 min)")
        print(f"📊 Data Points: {len(ai_data['data'])}")
        print(f"💰 Cost: ${ai_data['cost_estimate']:.4f}")
        print(f"📁 File: {ai_file}")
        
        if ai_data['data']:
            latest_point = ai_data['data'][-1]
            print(f"📈 Latest AI Social Volume: {latest_point.get('value', 'N/A')}")
            print(f"🕐 Latest Timestamp: {latest_point.get('datetime', 'N/A')}")
        
        return {
            "ai_social": ai_data,
            "cost": ai_data['cost_estimate']
        }

def main():
    """Main execution - HIGH FREQUENCY (every 15 min)"""
    monitor = SantimentAISocialMonitor()
    
    if not monitor.santiment_config.get("enabled", False):
        print("❌ Santiment API is disabled in config")
        return
    
    print("🤖 Santiment AI Social Volume Monitor")
    print("⏰ High-frequency collection: Every 15 minutes")
    print("📊 Metric: social_volume_ai_total (Gesamtmarkt)")
    print("💰 Cost: $0.02 per collection")
    
    # Monitor AI social volume
    result = monitor.monitor_ai_social()
    
    if result is None:
        print("\n✅ 15-minute limit respected - no additional API costs")
    else:
        print(f"\n💰 Collection cost: ${result['cost']:.4f}")
        print("⏰ Next collection: In 15 minutes")

if __name__ == "__main__":
    main()