#!/usr/bin/env python3
"""
Whale Alert WebSocket Integration for AgentCeli
Real-time whale transaction monitoring via WebSocket API
"""

import asyncio
import websockets
import json
import csv
import logging
from datetime import datetime
from pathlib import Path
import signal
import sys

class WhaleAlertWebSocket:
    def __init__(self, config_file="agentceli_config.json", api_key=None):
        self.base_dir = Path(__file__).parent
        self.config = self.load_config(config_file)
        self.api_key = api_key or self.get_api_key_from_config()
        self.websocket_url = f"wss://ws.whale-alert.io?api_key={self.api_key}" if self.api_key else "wss://ws.whale-alert.io"
        self.csv_file = self.base_dir / "whale_events.csv"
        self.is_running = True
        self.websocket = None
        
        self.setup_logging()
        self.setup_csv_file()
        self.setup_signal_handlers()
    
    def load_config(self, config_file):
        """Load AgentCeli configuration"""
        try:
            with open(self.base_dir / config_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def get_api_key_from_config(self):
        """Get Whale Alert API key from config"""
        try:
            return self.config.get("data_sources", {}).get("paid_apis", {}).get("whale_alert", {}).get("key")
        except:
            return None
    
    def setup_logging(self):
        """Setup logging"""
        log_file = self.base_dir / "logs" / "whale_alert.log"
        log_file.parent.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - WHALE_ALERT - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_csv_file(self):
        """Setup CSV file with headers if it doesn't exist"""
        if not self.csv_file.exists():
            with open(self.csv_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "symbol", "amount", "amount_usd", 
                    "from_owner", "to_owner", "transaction_type", 
                    "blockchain", "hash", "transaction_count"
                ])
            self.logger.info(f"📄 Created CSV file: {self.csv_file}")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"🛑 Received signal {signum}, shutting down...")
        self.is_running = False
        if self.websocket:
            asyncio.create_task(self.websocket.close())
    
    def log_whale_event(self, event_data):
        """Log whale event to CSV file"""
        try:
            timestamp = datetime.now().isoformat()
            
            # Extract relevant fields from event data
            symbol = event_data.get("symbol", "")
            amount = event_data.get("amount", 0)
            amount_usd = event_data.get("amount_usd", 0)
            from_owner = event_data.get("from", {}).get("owner", "")
            to_owner = event_data.get("to", {}).get("owner", "")
            transaction_type = event_data.get("transaction_type", "")
            blockchain = event_data.get("blockchain", "")
            tx_hash = event_data.get("hash", "")
            transaction_count = event_data.get("transaction_count", 1)
            
            # Write to CSV
            with open(self.csv_file, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp, symbol, amount, amount_usd,
                    from_owner, to_owner, transaction_type,
                    blockchain, tx_hash, transaction_count
                ])
            
            # Log the event
            self.logger.info(
                f"🐋 WHALE EVENT: {amount:,.2f} {symbol} "
                f"(${amount_usd:,.2f}) {transaction_type} on {blockchain}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log whale event: {e}")
    
    async def connect_and_listen(self):
        """Connect to WebSocket and listen for whale events"""
        reconnect_delay = 1
        max_reconnect_delay = 60
        
        while self.is_running:
            try:
                self.logger.info(f"🔌 Connecting to {self.websocket_url}")
                
                async with websockets.connect(
                    self.websocket_url,
                    ping_interval=30,
                    ping_timeout=10,
                    close_timeout=10
                ) as websocket:
                    self.websocket = websocket
                    self.logger.info("✅ Connected to Whale Alert WebSocket")
                    reconnect_delay = 1  # Reset delay on successful connection
                    
                    # Listen for messages
                    async for message in websocket:
                        if not self.is_running:
                            break
                            
                        try:
                            event_data = json.loads(message)
                            self.log_whale_event(event_data)
                            
                        except json.JSONDecodeError as e:
                            self.logger.error(f"Failed to parse message: {e}")
                        except Exception as e:
                            self.logger.error(f"Error processing message: {e}")
            
            except websockets.exceptions.ConnectionClosed:
                if self.is_running:
                    self.logger.warning("🔌 Connection closed, attempting to reconnect...")
                
            except Exception as e:
                if self.is_running:
                    self.logger.error(f"Connection error: {e}")
            
            # Reconnection logic
            if self.is_running:
                self.logger.info(f"⏳ Reconnecting in {reconnect_delay} seconds...")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
            
            self.websocket = None
    
    async def run(self):
        """Main run method"""
        self.logger.info("🚀 Starting Whale Alert WebSocket Monitor")
        self.logger.info(f"📄 Logging to: {self.csv_file}")
        
        try:
            await self.connect_and_listen()
        except KeyboardInterrupt:
            self.logger.info("🛑 Received keyboard interrupt")
        finally:
            self.logger.info("🔚 Whale Alert Monitor stopped")

async def main():
    """Main entry point"""
    monitor = WhaleAlertWebSocket()
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main())