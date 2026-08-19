import asyncio
import websockets
import json
from typing import Dict, Set, Callable, Any
from datetime import datetime
from decimal import Decimal
import threading

class WebSocketManager:
    def __init__(self):
        self.connections: Set[websockets.WebSocketServerProtocol] = set()
        self.subscriptions: Dict[str, Set[websockets.WebSocketServerProtocol]] = {}
        self._running = False
        self._task = None
        self._callbacks: Dict[str, Callable] = {}
    
    async def connect(self):
        """Connect to exchange WebSocket."""
        self._running = True
        uri = "wss://ws.bitget.com/v1/stream"
        
        while self._running:
            try:
                async with websockets.connect(uri) as websocket:
                    # Subscribe to ticker updates for all symbols
                    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT"]
                    subscribe_msg = {
                        "op": "subscribe",
                        "args": [{"channel": "ticker", "instId": sym} for sym in symbols]
                    }
                    await websocket.send(json.dumps(subscribe_msg))
                    print(f"WebSocket connected, subscribed to {len(symbols)} symbols")
                    
                    async for message in websocket:
                        await self._handle_message(message)
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket connection closed, reconnecting...")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"WebSocket error: {e}")
                await asyncio.sleep(5)
    
    async def _handle_message(self, message: str):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)
            
            # Check if it's a ticker update
            if 'data' in data and isinstance(data['data'], list):
                for item in data['data']:
                    if 'instId' in item and 'lastPr' in item:
                        symbol = item['instId']
                        price = Decimal(str(item['lastPr']))
                        
                        # Call registered callbacks
                        if symbol in self._callbacks:
                            await self._callbacks[symbol](symbol, price)
                        
                        # Broadcast to subscribed clients
                        if symbol in self.subscriptions:
                            for client in self.subscriptions[symbol]:
                                try:
                                    await client.send(json.dumps({
                                        'type': 'price_update',
                                        'symbol': symbol,
                                        'price': float(price),
                                        'timestamp': datetime.utcnow().isoformat()
                                    }))
                                except:
                                    pass
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"Error handling WebSocket message: {e}")
    
    def register_callback(self, symbol: str, callback: Callable):
        """Register a callback for price updates."""
        self._callbacks[symbol] = callback
    
    async def subscribe_client(self, client: websockets.WebSocketServerProtocol, symbol: str):
        """Subscribe a client to price updates for a symbol."""
        if symbol not in self.subscriptions:
            self.subscriptions[symbol] = set()
        self.subscriptions[symbol].add(client)
    
    async def unsubscribe_client(self, client: websockets.WebSocketServerProtocol, symbol: str):
        """Unsubscribe a client from price updates."""
        if symbol in self.subscriptions:
            self.subscriptions[symbol].discard(client)
    
    async def add_connection(self, client: websockets.WebSocketServerProtocol):
        """Add a new client connection."""
        self.connections.add(client)
    
    async def remove_connection(self, client: websockets.WebSocketServerProtocol):
        """Remove a client connection."""
        self.connections.discard(client)
        # Remove from all subscriptions
        for symbol in self.subscriptions:
            self.subscriptions[symbol].discard(client)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        for client in self.connections:
            try:
                await client.send(json.dumps(message))
            except:
                pass
    
    def start(self):
        """Start the WebSocket connection in a background task."""
        if not self._running:
            asyncio.create_task(self.connect())
            print("WebSocket manager started")
    
    def stop(self):
        """Stop the WebSocket connection."""
        self._running = False
        print("WebSocket manager stopped")

# Create singleton instance
ws_manager = WebSocketManager()
