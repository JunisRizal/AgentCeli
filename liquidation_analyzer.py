#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Liquidation Risk Analyzer - AgentCeli
=====================================
Comprehensive liquidation risk analysis with detailed German explanations
No visualization - pure data analysis and reporting
"""

import json
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import requests
import time
import os

class LiquidationAnalyzer:
    def __init__(self, config_file="agentceli_config.json"):
        """Initialize liquidation analyzer"""
        self.config = self.load_config(config_file)
        self.symbols = ['BTC', 'ETH', 'XRP', 'SOL']
        
        print("📊 Liquidation Risk Analyzer - AgentCeli initialized")
    
    def load_config(self, config_file):
        """Load configuration"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Config error: {e}")
            return {}
    
    def get_latest_price_data(self):
        """Get latest price data from hybrid data source"""
        try:
            with open('correlation_data/hybrid_latest.json', 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"❌ Price data error: {e}")
            return {}
    
    def get_fear_greed_index(self):
        """Get Fear & Greed index"""
        try:
            response = requests.get('https://api.alternative.me/fng/', timeout=10)
            data = response.json()
            return {
                'value': int(data['data'][0]['value']),
                'classification': data['data'][0]['value_classification'],
                'liquidation_multiplier': 1.5 if int(data['data'][0]['value']) > 50 else 1.2
            }
        except:
            return {'value': 50, 'classification': 'Neutral', 'liquidation_multiplier': 1.3}
    
    def get_whale_movements(self, symbol):
        """Get whale movement data (mock data for now)"""
        # In production, this would connect to Santiment Pro API
        mock_data = {
            'BTC': {'net_flow_7d': -2854.61, 'net_flow_24h': 409.53, 'pressure': 'LOW'},
            'ETH': {'net_flow_7d': -370428.78, 'net_flow_24h': -3220.94, 'pressure': 'LOW'},
            'XRP': {'net_flow_7d': -22041927.89, 'net_flow_24h': 1688204.95, 'pressure': 'ACCUMULATION'},
            'SOL': {'net_flow_7d': 0, 'net_flow_24h': 0, 'pressure': 'LOW'}
        }
        return mock_data.get(symbol, {'net_flow_7d': 0, 'net_flow_24h': 0, 'pressure': 'LOW'})
    
    def calculate_liquidation_risk(self, symbol, price_data, whale_data, fg_data):
        """Calculate comprehensive liquidation risk score"""
        try:
            # Get price change volatility
            price_change = abs(price_data.get('change_24h', 0))
            volatility_score = price_change * 10  # Scale volatility
            
            # Whale flow impact
            whale_net_7d = whale_data.get('net_flow_7d', 0)
            whale_intensity = min(abs(whale_net_7d) / 1000000, 50)  # Cap at 50
            
            # Fear & Greed multiplier
            fg_multiplier = fg_data.get('liquidation_multiplier', 1.3)
            
            # Combined risk score
            base_risk = volatility_score + whale_intensity
            final_risk = base_risk * fg_multiplier
            
            # Classify risk
            if final_risk < 20:
                risk_class = "LOW"
                risk_explanation = "NIEDRIG RISKANT - Stabile Bedingungen"
                risk_advice = "Relativ sichere Handelsbedingungen."
            elif final_risk < 40:
                risk_class = "MEDIUM"
                risk_explanation = "MODERATE GEFAHR - Normale Marktrisiken"
                risk_advice = "Standard-Risikomanagement anwenden."
            elif final_risk < 60:
                risk_class = "HIGH"
                risk_explanation = "HOCH RISKANT - Erhöhte Liquidation-Gefahr"
                risk_advice = "Leverage reduzieren, enge Stop-Loss setzen."
            else:
                risk_class = "EXTREME"
                risk_explanation = "EXTREM GEFÄHRLICH - Sehr hohe Liquidation-Wahrscheinlichkeit"
                risk_advice = "Vorsicht bei Leverage! Starke Bewegungen wahrscheinlich."
            
            return {
                'risk_score': final_risk,
                'risk_class': risk_class,
                'risk_explanation': risk_explanation,
                'risk_advice': risk_advice,
                'volatility_component': volatility_score,
                'whale_component': whale_intensity,
                'fear_greed_multiplier': fg_multiplier
            }
            
        except Exception as e:
            print(f"❌ Risk calculation error for {symbol}: {e}")
            return {
                'risk_score': 0,
                'risk_class': 'LOW',
                'risk_explanation': 'Keine Daten',
                'risk_advice': 'Keine Analyse möglich',
                'volatility_component': 0,
                'whale_component': 0,
                'fear_greed_multiplier': 1.0
            }
    
    def generate_detailed_explanation(self, symbol, price_data, whale_data, risk_data, fg_data):
        """Generate detailed German explanation"""
        try:
            current_price = price_data.get('price', 0)
            price_change = price_data.get('change_24h', 0)
            prev_price = current_price / (1 + price_change/100) if price_change != 0 else current_price
            
            # Price direction
            if price_change > 0:
                price_direction = f"gestiegen um {price_change:.2f}%"
                trend = "BULLISH"
            elif price_change < 0:
                price_direction = f"gefallen um {abs(price_change):.2f}%"
                trend = "BEARISH"
            else:
                price_direction = "unverändert"
                trend = "NEUTRAL"
            
            # Whale analysis
            whale_net_7d = whale_data.get('net_flow_7d', 0)
            whale_net_24h = whale_data.get('net_flow_24h', 0)
            
            if abs(whale_net_7d) > 10000000:  # > 10M
                whale_signal = "Akkumulation" if whale_net_7d < 0 else "Distribution"
                whale_summary = f"{abs(whale_net_7d/1000000):.1f}M {'weg von' if whale_net_7d < 0 else 'zu'} Exchanges ({'BULLISH' if whale_net_7d < 0 else 'BEARISH'})"
            else:
                whale_signal = "Neutral"
                whale_summary = "Ausgeglichene Whale-Aktivität"
            
            # Fear & Greed impact
            fg_value = fg_data.get('value', 50)
            if fg_value > 70:
                fg_impact = "Gier verstärkt Liquidation-Risiko (überkauft)"
            elif fg_value < 30:
                fg_impact = "Angst verstärkt Liquidation-Risiko (überverkauft)"
            else:
                fg_impact = "Neutraler Markt-Sentiment"
            
            # Liquidation zones (estimated)
            support_10x = current_price * 0.85
            support_5x = current_price * 0.75
            resistance_10x = current_price * 1.15
            resistance_5x = current_price * 1.25
            
            explanation = f"""
{symbol} Liquidation-Analyse:

📊 PREIS (24h):
   Aktuell: ${current_price:,.2f}
   Gestern: ${prev_price:,.2f}
   Änderung: {price_change:+.2f}% ({price_direction})

🐋 WHALE-AKTIVITÄT (7 Tage):
   Zufluss: {whale_data.get('inflow_7d', 0)/1000000:.1f}M {symbol}
   Abfluss: {whale_data.get('outflow_7d', 0)/1000000:.1f}M {symbol}
   Netto: {whale_net_7d/1000000:+.1f}M {symbol}
   Status: {whale_signal}

🔥 LIQUIDATION-RISIKO:
   Score: {risk_data['risk_score']:.1f}/100
   Klasse: {risk_data['risk_explanation']}
   Empfehlung: {risk_data['risk_advice']}

🎯 LIQUIDATION-ZONEN:
   10x Long: ${support_10x:.2f} (-15%)
   5x Long: ${support_5x:.2f} (-25%)
   10x Short: ${resistance_10x:.2f} (+15%)
   5x Short: ${resistance_5x:.2f} (+25%)

😨 MARKET SENTIMENT:
   Fear & Greed: {fg_value} ({fg_data['classification']})
   Impact: {fg_impact}
            """
            
            return explanation.strip()
            
        except Exception as e:
            print(f"❌ Explanation error for {symbol}: {e}")
            return f"{symbol}: Fehler bei der Analyse"
    
    def analyze_all_symbols(self):
        """Analyze all symbols and return comprehensive report"""
        print("\n🔍 Starting comprehensive liquidation analysis...")
        
        # Get market data
        price_data = self.get_latest_price_data()
        fg_data = self.get_fear_greed_index()
        
        results = {}
        
        for symbol in self.symbols:
            print(f"📊 Analyzing {symbol}...")
            
            # Get symbol-specific data
            if 'sources' in price_data and 'binance' in price_data['sources']:
                symbol_price = price_data['sources']['binance'].get(f'{symbol}USDT', {})
            else:
                symbol_price = {'price': 0, 'change_24h': 0}
            
            whale_data = self.get_whale_movements(symbol)
            risk_data = self.calculate_liquidation_risk(symbol, symbol_price, whale_data, fg_data)
            explanation = self.generate_detailed_explanation(symbol, symbol_price, whale_data, risk_data, fg_data)
            
            results[symbol] = {
                'price_data': symbol_price,
                'whale_data': whale_data,
                'risk_data': risk_data,
                'explanation': explanation,
                'timestamp': datetime.now().isoformat()
            }
        
        return results
    
    def save_analysis(self, results):
        """Save analysis results to file"""
        try:
            os.makedirs('liquidation_data', exist_ok=True)
            
            # Save detailed results
            with open('liquidation_data/liquidation_analysis_latest.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print("💾 Analysis saved to liquidation_data/liquidation_analysis_latest.json")
            return True
            
        except Exception as e:
            print(f"❌ Save error: {e}")
            return False
    
    def print_summary_report(self, results):
        """Print summary report to console"""
        print("\n" + "="*60)
        print("📊 LIQUIDATION RISK SUMMARY REPORT")
        print("="*60)
        
        total_symbols = len(results)
        risk_scores = [results[symbol]['risk_data']['risk_score'] for symbol in results]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        high_risk_count = sum(1 for score in risk_scores if score > 60)
        
        print(f"🔍 Symbols Analyzed: {total_symbols}")
        print(f"📈 Average Risk Score: {avg_risk:.1f}/100")
        print(f"⚠️ High Risk Assets: {high_risk_count}")
        print(f"😨 Market Sentiment: Fear & Greed Index")
        
        print("\n📋 INDIVIDUAL SYMBOL ANALYSIS:")
        print("-" * 60)
        
        for symbol in sorted(results.keys()):
            data = results[symbol]
            risk_score = data['risk_data']['risk_score']
            risk_class = data['risk_data']['risk_class']
            price = data['price_data'].get('price', 0)
            change = data['price_data'].get('change_24h', 0)
            
            risk_emoji = {
                'LOW': '🟢',
                'MEDIUM': '🟡', 
                'HIGH': '🟠',
                'EXTREME': '🔴'
            }.get(risk_class, '⚪')
            
            print(f"{risk_emoji} {symbol:4} | Risk: {risk_score:5.1f} | Price: ${price:8,.2f} | Change: {change:+6.2f}%")
        
        print("\n💡 DETAILED EXPLANATIONS:")
        print("=" * 60)
        
        for symbol in sorted(results.keys()):
            print(f"\n🔥 {symbol} DETAILS:")
            print("-" * 30)
            print(results[symbol]['explanation'])
    
    def run_analysis(self):
        """Run complete analysis"""
        try:
            results = self.analyze_all_symbols()
            self.save_analysis(results)
            self.print_summary_report(results)
            
            print(f"\n✅ Analysis complete at {datetime.now().strftime('%H:%M:%S')}")
            return results
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return {}

def main():
    """Main function"""
    print("📊 Liquidation Risk Analyzer - AgentCeli")
    print("=" * 50)
    print("Features:")
    print("  🔍 Multi-source risk analysis")
    print("  🌊 Volatility-based liquidation estimates")
    print("  🐋 Whale movement correlation")
    print("  😨 Fear & Greed sentiment integration")
    print("  🎯 Estimated liquidation zones")
    print("  📋 Detailed German explanations")
    print()
    
    analyzer = LiquidationAnalyzer()
    results = analyzer.run_analysis()
    
    return results

if __name__ == "__main__":
    main()