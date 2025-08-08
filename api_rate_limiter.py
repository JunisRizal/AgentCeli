#!/usr/bin/env python3
"""
AgentCeli API Rate Limiter
Prevents excessive API usage and controls costs
"""

import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, deque
import logging

class APIRateLimiter:
    def __init__(self, config_file="agentceli_config.json"):
        self.base_dir = Path(__file__).parent
        self.config_file = self.base_dir / config_file
        self.lock = threading.Lock()
        
        # Rate limiting tracking
        self.request_history = defaultdict(lambda: deque(maxlen=1000))
        self.daily_costs = defaultdict(float)
        self.hourly_requests = defaultdict(lambda: defaultdict(int))
        
        # Load configuration
        self.load_config()
        self.setup_logging()
        
        # Default rate limits (requests per minute)
        self.rate_limits = {
            "binance": {"rpm": 1200, "daily_cost_limit": 0.0},
            "coingecko": {"rpm": 50, "daily_cost_limit": 0.0},
            "santiment": {"rpm": 10, "daily_cost_limit": 1.00},
            "whale_alert": {"rpm": 60, "daily_cost_limit": 5.00},
            "coinbase": {"rpm": 600, "daily_cost_limit": 0.0},
            "fear_greed": {"rpm": 60, "daily_cost_limit": 0.0}
        }
        
        # Emergency stops
        self.emergency_stop = False
        self.total_daily_limit = 10.00  # $10 per day maximum
        
    def load_config(self):
        """Load configuration with rate limits"""
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except:
            self.config = {}
            
        # Update rate limits from config
        paid_apis = self.config.get("data_sources", {}).get("paid_apis", {})
        for api_name, api_config in paid_apis.items():
            if api_name in self.rate_limits:
                cost_per_call = api_config.get("cost_per_call", 0.0)
                # Conservative daily limits based on cost
                if cost_per_call > 0:
                    max_daily_calls = min(100, int(2.0 / cost_per_call))  # Max $2/day per API
                    self.rate_limits[api_name]["daily_cost_limit"] = max_daily_calls * cost_per_call
                    self.rate_limits[api_name]["rpm"] = min(self.rate_limits[api_name]["rpm"], max_daily_calls // 24)
    
    def setup_logging(self):
        """Setup logging for rate limiter"""
        log_file = self.base_dir / "logs" / "rate_limiter.log"
        log_file.parent.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - RATE_LIMITER - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def can_make_request(self, api_name, cost=0.0):
        """Check if request is allowed based on rate limits"""
        with self.lock:
            now = datetime.now()
            current_minute = now.strftime("%Y-%m-%d-%H-%M")
            current_day = now.strftime("%Y-%m-%d")
            
            # Emergency stop check
            if self.emergency_stop:
                self.logger.warning(f"🚨 EMERGENCY STOP - All API requests blocked")
                return False, "Emergency stop activated"
            
            # Daily cost limit check
            total_daily_cost = sum(self.daily_costs.values())
            if total_daily_cost >= self.total_daily_limit:
                self.logger.warning(f"🚨 DAILY LIMIT EXCEEDED - Total: ${total_daily_cost:.4f}")
                return False, f"Daily cost limit exceeded: ${total_daily_cost:.4f}"
            
            # API-specific checks
            if api_name not in self.rate_limits:
                self.logger.warning(f"⚠️ Unknown API: {api_name}")
                return True, "Unknown API - allowed"
            
            limits = self.rate_limits[api_name]
            
            # Check requests per minute
            minute_requests = self.hourly_requests[api_name][current_minute]
            if minute_requests >= limits["rpm"]:
                self.logger.warning(f"⏱️ RATE LIMIT - {api_name}: {minute_requests}/{limits['rpm']} RPM")
                return False, f"Rate limit exceeded: {minute_requests}/{limits['rpm']} RPM"
            
            # Check daily cost for this API
            if cost > 0 and self.daily_costs[api_name] + cost > limits["daily_cost_limit"]:
                self.logger.warning(f"💰 COST LIMIT - {api_name}: ${self.daily_costs[api_name] + cost:.4f}")
                return False, f"Daily cost limit for {api_name}: ${self.daily_costs[api_name] + cost:.4f}"
            
            return True, "Request allowed"
    
    def log_request(self, api_name, cost=0.0, success=True):
        """Log a completed API request"""
        with self.lock:
            now = datetime.now()
            current_minute = now.strftime("%Y-%m-%d-%H-%M")
            current_day = now.strftime("%Y-%m-%d")
            
            # Track request
            self.request_history[api_name].append({
                "timestamp": now.isoformat(),
                "cost": cost,
                "success": success
            })
            
            # Update counters
            self.hourly_requests[api_name][current_minute] += 1
            if success and cost > 0:
                self.daily_costs[api_name] += cost
            
            # Log high-cost requests
            if cost > 0.05:
                self.logger.warning(f"💸 HIGH COST REQUEST - {api_name}: ${cost:.4f}")
            
            # Check if approaching limits
            total_daily = sum(self.daily_costs.values())
            if total_daily > self.total_daily_limit * 0.8:  # 80% of limit
                self.logger.warning(f"⚠️ APPROACHING DAILY LIMIT - ${total_daily:.4f}/{self.total_daily_limit}")
    
    def get_status(self):
        """Get current rate limiting status"""
        with self.lock:
            now = datetime.now()
            current_minute = now.strftime("%Y-%m-%d-%H-%M")
            total_daily_cost = sum(self.daily_costs.values())
            
            status = {
                "timestamp": now.isoformat(),
                "emergency_stop": self.emergency_stop,
                "total_daily_cost": total_daily_cost,
                "daily_limit": self.total_daily_limit,
                "usage_percentage": (total_daily_cost / self.total_daily_limit) * 100,
                "apis": {}
            }
            
            for api_name, limits in self.rate_limits.items():
                minute_requests = self.hourly_requests[api_name][current_minute]
                daily_cost = self.daily_costs[api_name]
                
                status["apis"][api_name] = {
                    "requests_this_minute": minute_requests,
                    "rpm_limit": limits["rpm"],
                    "rpm_usage_percent": (minute_requests / limits["rpm"]) * 100,
                    "daily_cost": daily_cost,
                    "daily_cost_limit": limits["daily_cost_limit"],
                    "cost_usage_percent": (daily_cost / limits["daily_cost_limit"]) * 100 if limits["daily_cost_limit"] > 0 else 0,
                    "status": self._get_api_status(api_name, minute_requests, daily_cost, limits)
                }
            
            return status
    
    def _get_api_status(self, api_name, minute_requests, daily_cost, limits):
        """Get status for specific API"""
        rpm_usage = (minute_requests / limits["rpm"]) * 100
        cost_usage = (daily_cost / limits["daily_cost_limit"]) * 100 if limits["daily_cost_limit"] > 0 else 0
        
        if rpm_usage >= 90 or cost_usage >= 90:
            return "CRITICAL"
        elif rpm_usage >= 70 or cost_usage >= 70:
            return "WARNING"
        else:
            return "OK"
    
    def emergency_stop_all(self, reason="Manual activation"):
        """Activate emergency stop for all APIs"""
        self.emergency_stop = True
        self.logger.critical(f"🚨 EMERGENCY STOP ACTIVATED: {reason}")
    
    def resume_operations(self):
        """Resume normal operations"""
        self.emergency_stop = False
        self.logger.info("✅ Operations resumed")
    
    def reset_daily_limits(self):
        """Reset daily counters (called at midnight)"""
        with self.lock:
            self.daily_costs.clear()
            self.logger.info("🔄 Daily limits reset")
    
    def cleanup_old_data(self):
        """Clean up old tracking data"""
        with self.lock:
            cutoff = datetime.now() - timedelta(hours=2)
            cutoff_str = cutoff.strftime("%Y-%m-%d-%H-%M")
            
            # Clean hourly request tracking
            for api_name in self.hourly_requests:
                old_keys = [k for k in self.hourly_requests[api_name].keys() if k < cutoff_str]
                for key in old_keys:
                    del self.hourly_requests[api_name][key]

# Global rate limiter instance
rate_limiter = APIRateLimiter()

def check_api_rate_limit(api_name, cost=0.0):
    """Decorator function to check rate limits"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            allowed, reason = rate_limiter.can_make_request(api_name, cost)
            if not allowed:
                rate_limiter.logger.warning(f"🚫 Request blocked: {api_name} - {reason}")
                return {"error": f"Rate limit exceeded: {reason}", "cost": cost}
            
            try:
                start_time = time.time()
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                result = {"error": str(e)}
                success = False
            
            response_time = time.time() - start_time
            rate_limiter.log_request(api_name, cost, success)
            
            if isinstance(result, dict):
                result["_rate_limit_info"] = {
                    "api": api_name,
                    "cost": cost,
                    "response_time": response_time,
                    "limited": False
                }
            
            return result
        return wrapper
    return decorator

if __name__ == "__main__":
    print("🔒 AgentCeli API Rate Limiter")
    print("=" * 40)
    
    status = rate_limiter.get_status()
    
    print(f"💰 Daily Cost: ${status['total_daily_cost']:.4f} / ${status['daily_limit']:.2f}")
    print(f"📊 Usage: {status['usage_percentage']:.1f}%")
    print(f"🚨 Emergency Stop: {status['emergency_stop']}")
    print()
    
    print("API Status:")
    for api_name, api_status in status["apis"].items():
        status_emoji = {"OK": "✅", "WARNING": "⚠️", "CRITICAL": "🚨"}[api_status["status"]]
        print(f"  {status_emoji} {api_name}: {api_status['requests_this_minute']}/{api_status['rpm_limit']} RPM, ${api_status['daily_cost']:.4f} cost")