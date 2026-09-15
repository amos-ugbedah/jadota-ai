import os
import hmac
import hashlib
import time
import requests
from typing import Dict, Any

class BitgetService:
    def __init__(self):
        self.api_key = os.getenv("BITGET_API_KEY")
        self.api_secret = os.getenv("BITGET_API_SECRET")
        self.passphrase = os.getenv("BITGET_PASSPHRASE")
        self.base_url = "https://api.bitget.com"
        
    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        message = timestamp + method + request_path + body
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_headers(self, method: str, request_path: str, body: str = "") -> Dict[str, str]:
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(timestamp, method, request_path, body)
        
        return {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json"
        }
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account balance and info"""
        request_path = "/api/v2/account/all-account-balance"
        headers = self._get_headers("GET", request_path)
        
        response = requests.get(
            f"{self.base_url}{request_path}",
            headers=headers
        )
        return response.json()
    
    def place_order(self, symbol: str, side: str, size: float, order_type: str = "market") -> Dict[str, Any]:
        """Place a real order on Bitget"""
        request_path = "/api/v2/order/place-order"
        body = {
            "symbol": symbol,
            "side": side.lower(),
            "orderType": order_type,
            "size": str(size)
        }
        
        headers = self._get_headers("POST", request_path, str(body))
        
        response = requests.post(
            f"{self.base_url}{request_path}",
            json=body,
            headers=headers
        )
        return response.json()
    
    def get_open_orders(self, symbol: str = None) -> Dict[str, Any]:
        """Get open orders"""
        request_path = "/api/v2/order/orders-pending"
        params = {}
        if symbol:
            params["symbol"] = symbol
            
        headers = self._get_headers("GET", request_path)
        
        response = requests.get(
            f"{self.base_url}{request_path}",
            params=params,
            headers=headers
        )
        return response.json()
    
    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel an order"""
        request_path = "/api/v2/order/cancel-order"
        body = {
            "orderId": order_id,
            "symbol": symbol
        }
        
        headers = self._get_headers("POST", request_path, str(body))
        
        response = requests.post(
            f"{self.base_url}{request_path}",
            json=body,
            headers=headers
        )
        return response.json()