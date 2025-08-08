#!/usr/bin/env python3
"""
AgentCeli Connection for CryptoPredictor1h1d3d
Feeds LIVE data to your correlation/prediction system
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error
import sqlite3
import json
import requests
import warnings
warnings.filterwarnings('ignore')

class CryptoPredictor1h1d3d:
    def __init__(self, agentceli_data_path="correlation_data", use_fallback=True):
        """Initialize with AgentCeli data connection

        Parameters
        ----------
        agentceli_data_path : str
            Path to correlation data directory.
        use_fallback : bool, optional
            If ``True`` (default) old CSV data will be used when the API is
            unreachable. Set to ``False`` to return ``None`` instead.
        """
        self.data_path = agentceli_data_path
        self.db_path = f"{agentceli_data_path}/hybrid_crypto_data.db"
        self.api_url = "http://localhost:8080"  # AgentCeli API

        # Whether to use local CSV data when API fails
        self.use_fallback = use_fallback
        
        # Your existing ML models
        self.models_1h = {}
        self.models_1d = {}
        self.models_3d = {}
        
        # Data storage
        self.live_data = None
        self.historical_data = None
        
        print("🔗 CryptoPredictor connected to AgentCeli data stream")
    
    def get_live_data_from_agentceli(self):
        """Get latest LIVE data from AgentCeli"""
        try:
            # Method 1: HTTP API (fastest)
            response = requests.get(f"{self.api_url}/api/prices", timeout=5)
            if response.status_code == 200:
                api_data = response.json() or {}

                timestamp = api_data.get('timestamp')
                btc = api_data.get('btc')
                eth = api_data.get('eth')
                sol = api_data.get('sol')
                xrp = api_data.get('xrp')
                fg = api_data.get('fear_greed')

                live_df = pd.DataFrame({
                    'timestamp': [pd.to_datetime(timestamp) if timestamp else pd.NaT],
                    'BTC_price': [btc if btc is not None else np.nan],
                    'ETH_price': [eth if eth is not None else np.nan],
                    'SOL_price': [sol if sol is not None else np.nan],
                    'XRP_price': [xrp if xrp is not None else np.nan],
                    'fear_greed': [fg if fg is not None else np.nan],
                    'market_cap': [api_data.get('market_cap')]
                })

                print(
                    f"✅ Live data: BTC=${btc if btc is not None else 'N/A'}, "
                    f"ETH=${eth if eth is not None else 'N/A'}"
                )
                return live_df
                
        except Exception as e:
            print(f"⚠️ API connection failed: {e}")
            if not self.use_fallback:
                print("⚠️ Fallback disabled - no data returned")
                return None

        # Method 2: File fallback
        if self.use_fallback:
            try:
                csv_file = f"{self.data_path}/hybrid_latest.csv"
                df = pd.read_csv(csv_file)
                df['timestamp'] = pd.to_datetime(df['timestamp'])

                # Pivot to get prices in columns
                pivot_df = df.pivot(index='timestamp', columns='symbol', values='price').reset_index()
                pivot_df.columns.name = None

                print("✅ Live data loaded from CSV")
                return pivot_df

            except Exception as e:
                print(f"❌ Failed to load live data: {e}")

        return None
    
    def get_historical_data_from_agentceli(self, hours=168):  # 7 days default
        """Get historical data from AgentCeli database for training"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = f"""
            SELECT 
                timestamp,
                symbol,
                price_usd as price,
                volume_24h,
                change_24h,
                fear_greed
            FROM live_prices 
            WHERE timestamp > datetime('now', '-{hours} hours')
            ORDER BY timestamp ASC
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if df.empty:
                print("⚠️ No historical data available yet")
                return None
            
            # Convert timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Create features for each symbol
            historical_features = []
            
            for symbol in ['BTC', 'ETH', 'SOL', 'XRP']:
                symbol_data = df[df['symbol'] == symbol].copy()
                if len(symbol_data) > 0:
                    symbol_data = symbol_data.sort_values('timestamp')
                    
                    # Add technical features
                    symbol_data[f'{symbol}_price_ma_5'] = symbol_data['price'].rolling(5).mean()
                    symbol_data[f'{symbol}_price_ma_20'] = symbol_data['price'].rolling(20).mean()
                    symbol_data[f'{symbol}_volatility'] = symbol_data['price'].rolling(10).std()
                    symbol_data[f'{symbol}_rsi'] = self.calculate_rsi(symbol_data['price'])
                    
                    historical_features.append(symbol_data)
            
            if historical_features:
                # Combine all symbols
                combined_df = pd.concat(historical_features, ignore_index=True)
                print(f"✅ Historical data: {len(combined_df)} records loaded")
                return combined_df
            
        except Exception as e:
            print(f"❌ Historical data error: {e}")
        
        return None
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI for technical analysis"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def prepare_features_for_prediction(self, df, target_symbol='BTC'):
        """Prepare features for ML models using AgentCeli data"""
        if df is None or df.empty:
            return None, None
        
        # Filter for target symbol
        symbol_data = df[df['symbol'] == target_symbol].copy()
        if len(symbol_data) < 50:  # Need minimum data
            print(f"⚠️ Not enough data for {target_symbol} ({len(symbol_data)} records)")
            return None, None
        
        symbol_data = symbol_data.sort_values('timestamp')
        
        # Create features
        features_df = pd.DataFrame()
        features_df['price'] = symbol_data['price']
        features_df['volume'] = symbol_data['volume_24h']
        features_df['change_24h'] = symbol_data['change_24h']
        features_df['fear_greed'] = symbol_data['fear_greed']
        
        # Technical indicators
        features_df['price_ma_5'] = features_df['price'].rolling(5).mean()
        features_df['price_ma_20'] = features_df['price'].rolling(20).mean()
        features_df['volatility'] = features_df['price'].rolling(10).std()
        features_df['rsi'] = self.calculate_rsi(features_df['price'])
        
        # Price ratios
        features_df['price_to_ma5'] = features_df['price'] / features_df['price_ma_5']
        features_df['price_to_ma20'] = features_df['price'] / features_df['price_ma_20']
        
        # Lag features
        features_df['price_lag_1'] = features_df['price'].shift(1)
        features_df['price_lag_2'] = features_df['price'].shift(2)
        features_df['change_lag_1'] = features_df['change_24h'].shift(1)
        
        # Create prediction targets
        features_df['target_1h'] = features_df['price'].shift(-1)  # 1 period ahead
        features_df['target_1d'] = features_df['price'].shift(-24)  # 24 periods ahead (if 1h data)
        features_df['target_3d'] = features_df['price'].shift(-72)  # 72 periods ahead
        
        # Direction targets (up/down)
        features_df['direction_1h'] = (features_df['target_1h'] > features_df['price']).astype(int)
        features_df['direction_1d'] = (features_df['target_1d'] > features_df['price']).astype(int)
        features_df['direction_3d'] = (features_df['target_3d'] > features_df['price']).astype(int)
        
        # Remove NaN rows
        features_df = features_df.dropna()
        
        if len(features_df) < 20:
            print(f"⚠️ Not enough clean data after feature engineering")
            return None, None
        
        # Select feature columns (exclude targets)
        feature_cols = [col for col in features_df.columns if not col.startswith('target_') and not col.startswith('direction_')]
        X = features_df[feature_cols]
        y = features_df[['target_1h', 'target_1d', 'target_3d', 'direction_1h', 'direction_1d', 'direction_3d']]
        
        print(f"✅ Features prepared: {X.shape[0]} samples, {X.shape[1]} features")
        return X, y
    
    def train_models(self, symbol='BTC'):
        """Train prediction models using AgentCeli historical data"""
        print(f"🤖 Training models for {symbol}...")
        
        # Get historical data from AgentCeli
        historical_data = self.get_historical_data_from_agentceli(hours=168)  # 7 days
        
        if historical_data is None:
            print("❌ No training data available")
            return False
        
        # Prepare features
        X, y = self.prepare_features_for_prediction(historical_data, symbol)
        
        if X is None or y is None:
            print("❌ Feature preparation failed")
            return False
        
        try:
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=False
            )
            
            # Train regression models (price prediction)
            self.models_1h[f'{symbol}_price'] = RandomForestRegressor(n_estimators=100, random_state=42)
            self.models_1d[f'{symbol}_price'] = RandomForestRegressor(n_estimators=100, random_state=42)
            self.models_3d[f'{symbol}_price'] = RandomForestRegressor(n_estimators=100, random_state=42)
            
            # Train classification models (direction prediction)
            self.models_1h[f'{symbol}_direction'] = RandomForestClassifier(n_estimators=100, random_state=42)
            self.models_1d[f'{symbol}_direction'] = RandomForestClassifier(n_estimators=100, random_state=42)
            self.models_3d[f'{symbol}_direction'] = RandomForestClassifier(n_estimators=100, random_state=42)
            
            # Fit models
            self.models_1h[f'{symbol}_price'].fit(X_train, y_train['target_1h'])
            self.models_1d[f'{symbol}_price'].fit(X_train, y_train['target_1d'])
            self.models_3d[f'{symbol}_price'].fit(X_train, y_train['target_3d'])
            
            self.models_1h[f'{symbol}_direction'].fit(X_train, y_train['direction_1h'])
            self.models_1d[f'{symbol}_direction'].fit(X_train, y_train['direction_1d'])
            self.models_3d[f'{symbol}_direction'].fit(X_train, y_train['direction_3d'])
            
            # Evaluate models
            price_1h_pred = self.models_1h[f'{symbol}_price'].predict(X_test)
            price_1d_pred = self.models_1d[f'{symbol}_price'].predict(X_test)
            price_3d_pred = self.models_3d[f'{symbol}_price'].predict(X_test)
            
            dir_1h_pred = self.models_1h[f'{symbol}_direction'].predict(X_test)
            dir_1d_pred = self.models_1d[f'{symbol}_direction'].predict(X_test)
            dir_3d_pred = self.models_3d[f'{symbol}_direction'].predict(X_test)
            
            # Calculate metrics
            mae_1h = mean_absolute_error(y_test['target_1h'], price_1h_pred)
            mae_1d = mean_absolute_error(y_test['target_1d'], price_1d_pred)
            mae_3d = mean_absolute_error(y_test['target_3d'], price_3d_pred)
            
            acc_1h = accuracy_score(y_test['direction_1h'], dir_1h_pred)
            acc_1d = accuracy_score(y_test['direction_1d'], dir_1d_pred)
            acc_3d = accuracy_score(y_test['direction_3d'], dir_3d_pred)
            
            print(f"✅ {symbol} Models trained successfully:")
            print(f"   Price MAE - 1h: ${mae_1h:.2f}, 1d: ${mae_1d:.2f}, 3d: ${mae_3d:.2f}")
            print(f"   Direction Accuracy - 1h: {acc_1h:.1%}, 1d: {acc_1d:.1%}, 3d: {acc_3d:.1%}")
            
            return True
            
        except Exception as e:
            print(f"❌ Training error: {e}")
            return False
    
    def make_live_predictions(self, symbol='BTC'):
        """Make predictions using live AgentCeli data"""
        print(f"🔮 Making live predictions for {symbol}...")
        
        # Get current live data
        live_df = self.get_live_data_from_agentceli()
        if live_df is None:
            print("❌ No live data available")
            return None
        
        # Get recent historical data for features
        recent_data = self.get_historical_data_from_agentceli(hours=48)
        if recent_data is None:
            print("❌ No recent data for features")
            return None
        
        # Prepare features
        X, _ = self.prepare_features_for_prediction(recent_data, symbol)
        if X is None:
            print("❌ Feature preparation failed")
            return None
        
        # Use latest features for prediction
        latest_features = X.iloc[-1:].fillna(method='ffill')
        
        try:
            # Make predictions if models exist
            predictions = {}
            
            if f'{symbol}_price' in self.models_1h:
                predictions['price_1h'] = self.models_1h[f'{symbol}_price'].predict(latest_features)[0]
                predictions['price_1d'] = self.models_1d[f'{symbol}_price'].predict(latest_features)[0]
                predictions['price_3d'] = self.models_3d[f'{symbol}_price'].predict(latest_features)[0]
                
                predictions['direction_1h'] = self.models_1h[f'{symbol}_direction'].predict(latest_features)[0]
                predictions['direction_1d'] = self.models_1d[f'{symbol}_direction'].predict(latest_features)[0]
                predictions['direction_3d'] = self.models_3d[f'{symbol}_direction'].predict(latest_features)[0]
                
                # Get current price from live data
                if symbol == 'BTC':
                    current_price = live_df['BTC_price'].iloc[0]
                elif symbol == 'ETH':
                    current_price = live_df['ETH_price'].iloc[0]
                else:
                    current_price = 0
                
                predictions['current_price'] = current_price
                predictions['timestamp'] = datetime.now().isoformat()
                
                print(f"🔮 {symbol} Predictions:")
                print(f"   Current: ${current_price:,.2f}")
                print(f"   1h: ${predictions['price_1h']:,.2f} ({'UP' if predictions['direction_1h'] else 'DOWN'})")
                print(f"   1d: ${predictions['price_1d']:,.2f} ({'UP' if predictions['direction_1d'] else 'DOWN'})")
                print(f"   3d: ${predictions['price_3d']:,.2f} ({'UP' if predictions['direction_3d'] else 'DOWN'})")
                
                return predictions
            else:
                print(f"❌ No trained models for {symbol}")
                return None
                
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return None
    
    def run_continuous_predictions(self, symbols=['BTC', 'ETH'], interval_minutes=30):
        """Run continuous predictions using AgentCeli live data"""
        import time
        
        print(f"🔄 Starting continuous predictions for {symbols}")
        print(f"⏱️ Update interval: {interval_minutes} minutes")
        
        while True:
            try:
                print(f"\n{'='*50}")
                print(f"🔮 Prediction cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                for symbol in symbols:
                    # Train models with latest data
                    self.train_models(symbol)
                    
                    # Make predictions
                    predictions = self.make_live_predictions(symbol)
                    
                    # Save predictions (optional)
                    if predictions:
                        with open(f'predictions_{symbol.lower()}.json', 'w') as f:
                            json.dump(predictions, f, indent=2)
                
                print(f"⏱️ Next update in {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\n👋 Continuous predictions stopped")
                break
            except Exception as e:
                print(f"❌ Cycle error: {e}")
                time.sleep(60)  # Wait 1 minute before retry

def main():
    """Test the connection between AgentCeli and CryptoPredictor"""
    print("🔗 Testing AgentCeli → CryptoPredictor Connection")
    print("="*50)
    
    # Initialize predictor with AgentCeli connection
    predictor = CryptoPredictor1h1d3d()
    
    # Test live data connection
    live_data = predictor.get_live_data_from_agentceli()
    if live_data is not None:
        print("✅ Live data connection successful")
        print(live_data.head())
    
    # Test historical data
    historical_data = predictor.get_historical_data_from_agentceli(hours=24)
    if historical_data is not None:
        print("✅ Historical data connection successful")
        print(f"Records: {len(historical_data)}")
    
    # Test model training
    success = predictor.train_models('BTC')
    if success:
        print("✅ Model training successful")
        
        # Test predictions
        predictions = predictor.make_live_predictions('BTC')
        if predictions:
            print("✅ Live predictions successful")
    
    print("\n💡 To run continuous predictions:")
    print("   predictor.run_continuous_predictions(['BTC', 'ETH'], interval_minutes=30)")

if __name__ == "__main__":
    main()