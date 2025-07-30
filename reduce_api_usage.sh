#!/bin/bash
# Immediate script to reduce API usage and prevent excessive costs

echo "🔧 Reducing API Usage - Emergency Cost Control"
echo "=" * 50

# 1. Kill high-frequency processes
echo "1. Stopping high-frequency data collection..."
pkill -f "live_crypto_agent.py" && echo "   ✅ Stopped live crypto agent"
pkill -f "santiment_ai_social_monitor.py" && echo "   ✅ Stopped AI social monitor"

# 2. Update intervals to be more conservative
echo "2. Updating configuration for lower API usage..."

# Create backup of current config
cp agentceli_config.json agentceli_config.json.backup

# Update config with conservative settings
python3 -c "
import json

# Load config
with open('agentceli_config.json', 'r') as f:
    config = json.load(f)

# Make it more conservative
config['update_intervals'] = {
    'fast_data': 600,     # 10 minutes instead of 5
    'slow_data': 1800,    # 30 minutes instead of 15  
    'very_slow': 7200     # 2 hours instead of 1
}

# Add strict rate limits
config['rate_limits'] = {
    'daily_cost_limit': 3.00,
    'santiment_max_calls_per_hour': 6,
    'whale_alert_max_calls_per_hour': 12,
    'emergency_stop_threshold': 4.00
}

# Disable expensive APIs temporarily
if 'data_sources' in config and 'paid_apis' in config['data_sources']:
    for api_name in ['coinglass', 'taapi']:
        if api_name in config['data_sources']['paid_apis']:
            config['data_sources']['paid_apis'][api_name]['enabled'] = False

with open('agentceli_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print('✅ Configuration updated with conservative settings')
"

# 3. Start rate limiter monitor
echo "3. Starting API usage monitor..."
python3 api_rate_limiter.py > logs/rate_limiter_status.log &
echo "   ✅ Rate limiter monitoring active"

# 4. Check current usage
echo "4. Current API usage status:"
python3 -c "
from api_rate_limiter import rate_limiter
status = rate_limiter.get_status()
print(f'   💰 Daily cost: \${status[\"total_daily_cost\"]:.4f}')
print(f'   📊 Usage: {status[\"usage_percentage\"]:.1f}%')
if status['usage_percentage'] > 70:
    print('   🚨 HIGH USAGE - Consider manual intervention')
else:
    print('   ✅ Usage within limits')
"

# 5. Show recommendations
echo ""
echo "🎯 Immediate Actions Taken:"
echo "   • Increased update intervals (10min/30min/2hr)"
echo "   • Disabled expensive APIs temporarily"
echo "   • Started rate limiting monitor"
echo "   • Set daily limit to \$3.00"
echo ""
echo "💡 Additional Recommendations:"
echo "   • Use ./start_whale_monitor.sh instead of continuous polling"
echo "   • Check logs/rate_limiter_status.log for usage"
echo "   • Dashboard refresh reduced to 60 seconds"
echo "   • Santiment data refresh reduced to 30 minutes"
echo ""
echo "📊 Monitor usage with: python3 api_usage_monitor.py"