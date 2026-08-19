import asyncio
import json
from typing import Dict, Set, Callable, Any, Optional
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    """WebSocket manager that uses price simulator instead of real exchange connection."""
    
    def __init__(self):
        self.connections: Set[Any] = set()
        self.subscriptions: Dict[str, Set[Any]] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._callbacks: Dict[str, Callable] = {}
    
    async def connect(self):
        """Skip real connection - use price simulator instead."""
        logger.info("WebSocket manager running in SIMULATION mode (no real exchange connection)")
        self._running = True
        
        # Just keep running without connecting to exchange
        while self._running:
            await asyncio.sleep(60)  # Check periodically if still running
    
    async def _handle_message(self, message: str):
        """Handle incoming messages (not used in simulation mode)."""
        pass
    
    def register_callback(self, symbol: str, callback: Callable):
        """Register a callback for price updates."""
        self._callbacks[symbol] = callback
        logger.info(f"Registered callback for {symbol}")
    
    async def subscribe_client(self, client: Any, symbol: str):
        """Subscribe a client to price updates for a symbol."""
        if symbol not in self.subscriptions:
            self.subscriptions[symbol] = set()
        self.subscriptions[symbol].add(client)
        logger.info(f"Client subscribed to {symbol}")
    
    async def unsubscribe_client(self, client: Any, symbol: str):
        """Unsubscribe a client from price updates."""
        if symbol in self.subscriptions:
            self.subscriptions[symbol].discard(client)
            logger.info(f"Client unsubscribed from {symbol}")
    
    async def add_connection(self, client: Any):
        """Add a new client connection."""
        self.connections.add(client)
        logger.info(f"New WebSocket connection (total: {len(self.connections)})")
    
    async def remove_connection(self, client: Any):
        """Remove a client connection."""
        self.connections.discard(client)
        # Remove from all subscriptions
        for symbol in list(self.subscriptions.keys()):
            self.subscriptions[symbol].discard(client)
        logger.info(f"WebSocket connection removed (remaining: {len(self.connections)})")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        for client in list(self.connections):
            try:
                await client.send(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                self.connections.discard(client)
    
    def start(self):
        """Start the WebSocket manager."""
        if not self._running:
            self._task = asyncio.create_task(self.connect())
            logger.info("WebSocket manager started (simulation mode)")
    
    def stop(self):
        """Stop the WebSocket manager."""
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("WebSocket manager stopped")

# Create singleton instance
ws_manager = WebSocketManager()
