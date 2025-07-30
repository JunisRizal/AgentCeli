#!/usr/bin/env python3
"""
API Usage Monitor - Real-time monitoring and alerts for API consumption
"""

import json
import time
from datetime import datetime
from pathlib import Path
from api_rate_limiter import rate_limiter

class APIUsageMonitor:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.alerts_sent = set()
        
    def check_usage_and_alert(self):
        """Check API usage and send alerts if needed"""
        status = rate_limiter.get_status()
        
        current_time = datetime.now().strftime("%H:%M")
        
        # Check overall daily usage
        usage_pct = status['usage_percentage']
        if usage_pct >= 80 and "daily_80" not in self.alerts_sent:
            self.send_alert("HIGH_USAGE", f"🚨 Daily API cost at {usage_pct:.1f}% (${status['total_daily_cost']:.2f})")
            self.alerts_sent.add("daily_80")
        
        # Check individual APIs
        for api_name, api_status in status['apis'].items():
            if api_status['status'] == 'CRITICAL':
                alert_key = f"{api_name}_critical_{current_time}"
                if alert_key not in self.alerts_sent:
                    self.send_alert("API_CRITICAL", f"🚨 {api_name} API at critical usage!")
                    self.alerts_sent.add(alert_key)
        
        # Emergency stop if needed
        if usage_pct >= 95:
            rate_limiter.emergency_stop_all("95% daily limit reached")
            self.send_alert("EMERGENCY_STOP", "🚨 EMERGENCY STOP - API usage stopped!")
    
    def send_alert(self, alert_type, message):
        """Send alert (log for now, can extend to webhooks/email)"""
        timestamp = datetime.now().isoformat()
        alert = {
            "timestamp": timestamp,
            "type": alert_type,
            "message": message
        }
        
        print(f"[{timestamp}] {alert_type}: {message}")
        
        # Save to alerts file
        alerts_file = self.base_dir / "logs" / "api_alerts.json"
        alerts_file.parent.mkdir(exist_ok=True)
        
        try:
            if alerts_file.exists():
                with open(alerts_file, 'r') as f:
                    alerts = json.load(f)
            else:
                alerts = []
            
            alerts.append(alert)
            
            # Keep only last 100 alerts
            if len(alerts) > 100:
                alerts = alerts[-100:]
            
            with open(alerts_file, 'w') as f:
                json.dump(alerts, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save alert: {e}")
    
    def get_recommendations(self):
        """Get recommendations to reduce API usage"""
        status = rate_limiter.get_status()
        recommendations = []
        
        if status['usage_percentage'] > 70:
            recommendations.append("🔧 Increase update intervals in config")
            recommendations.append("⏱️ Reduce dashboard refresh frequency")
            
        for api_name, api_status in status['apis'].items():
            if api_status['cost_usage_percent'] > 80:
                recommendations.append(f"💰 Reduce {api_name} call frequency")
            if api_status['rpm_usage_percent'] > 80:
                recommendations.append(f"⏱️ Add delays between {api_name} requests")
        
        return recommendations

def main():
    """Main monitoring loop"""
    monitor = APIUsageMonitor()
    
    print("📊 API Usage Monitor Started")
    print("=" * 40)
    
    while True:
        try:
            # Check usage and send alerts
            monitor.check_usage_and_alert()
            
            # Print current status
            status = rate_limiter.get_status()
            print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Daily: ${status['total_daily_cost']:.4f} ({status['usage_percentage']:.1f}%)")
            
            # Show recommendations if usage is high
            if status['usage_percentage'] > 50:
                recommendations = monitor.get_recommendations()
                if recommendations:
                    print("💡 Recommendations:")
                    for rec in recommendations[:3]:  # Show top 3
                        print(f"   {rec}")
            
            # Sleep for 5 minutes
            time.sleep(300)
            
        except KeyboardInterrupt:
            print("\n🛑 Monitor stopped")
            break
        except Exception as e:
            print(f"❌ Monitor error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()