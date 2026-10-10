"""
Per-user Bitget API client.

Async, httpx-based. Each instance is constructed with the user's
decrypted credentials and never reads from environment variables —
that's the point of per-user integration.

Reference: https://www.bitget.com/api-doc/common/intro
"""

import base64
import hashlib
import hmac
import json
import logging
import time
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class BitgetError(Exception):
    """Raised when Bitget returns a non-success response."""
    def __init__(self, code: str, msg: str, http_status: int = 0):
        self.code = code
        self.msg = msg
        self.http_status = http_status
        super().__init__(f"Bitget error {code} (HTTP {http_status}): {msg}")


class BitgetClient:
    """
    Async Bitget v2 client.

    Usage:
        async with BitgetClient(api_key, api_secret, passphrase, testnet=True) as c:
            await c.get_account_info()
    """

    LIVE_BASE = "https://api.bitget.com"
    TESTNET_BASE = "https://api.bitget.com"  # same host; test keys route differently server-side

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        passphrase: str,
        testnet: bool = True,
        timeout: float = 10.0,
    ):
        if not api_key or not api_secret or not passphrase:
            raise ValueError("api_key, api_secret, and passphrase are required")
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.testnet = testnet
        self.base_url = self.TESTNET_BASE if testnet else self.LIVE_BASE
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, *exc):
        if self._client:
            await self._client.aclose()
            self._client = None

    # ============================================
    # Signing
    # ============================================
    def _sign(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """
        Bitget v2 signing:
            sign = base64(HMAC-SHA256(timestamp + method + path + body))
        """
        message = f"{timestamp}{method.upper()}{path}{body}"
        mac = hmac.new(
            self.api_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        )
        return base64.b64encode(mac.digest()).decode("ascii")

    def _headers(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        ts = str(int(time.time() * 1000))
        return {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": self._sign(ts, method, path, body),
            "ACCESS-TIMESTAMP": ts,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
            "locale": "en-US",
        }

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self._client:
            raise RuntimeError("BitgetClient must be used as async context manager")

        query = ""
        if params:
            query = "?" + "&".join(f"{k}={v}" for k, v in params.items())
        full_path = path + query

        body_str = ""
        if body is not None:
            body_str = json.dumps(body, separators=(",", ":"))

        headers = self._headers(method, full_path, body_str)

        try:
            if method.upper() == "GET":
                resp = await self._client.get(self.base_url + full_path, headers=headers)
            elif method.upper() == "POST":
                resp = await self._client.post(
                    self.base_url + path, params=params, content=body_str, headers=headers
                )
            else:
                raise ValueError(f"Unsupported method: {method}")
            data = resp.json()
        except httpx.HTTPError as e:
            raise BitgetError("HTTP_ERROR", str(e), 0)

        if data.get("code") != "00000":
            raise BitgetError(
                data.get("code", "UNKNOWN"),
                data.get("msg", "Unknown error"),
                resp.status_code,
            )

        return data.get("data") or {}

    # ============================================
    # Endpoints
    # ============================================
    async def get_account_info(self) -> Dict[str, Any]:
        """Fetch account balance / info. Used to test credentials."""
        return await self._request("GET", "/api/v2/account/all-account-balance")

    async def get_open_orders(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        params = {"symbol": symbol} if symbol else None
        return await self._request("GET", "/api/v2/spot/trade/unfilled-orders", params=params)

    async def place_spot_market_order(
        self,
        symbol: str,          # e.g. "BTCUSDT"
        side: str,            # "buy" or "sell"
        size: str,            # amount as string
        client_oid: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Place a spot market order."""
        body: Dict[str, Any] = {
            "symbol": symbol,
            "side": side.lower(),
            "orderType": "market",
            "size": size,
        }
        if client_oid:
            body["clientOid"] = client_oid
        return await self._request("POST", "/api/v2/spot/trade/place-order", body=body)


async def verify_credentials(
    api_key: str,
    api_secret: str,
    passphrase: str,
    testnet: bool = True,
) -> Dict[str, Any]:
    """Call Bitget with the given credentials. Returns account data or raises."""
    async with BitgetClient(api_key, api_secret, passphrase, testnet=testnet) as c:
        return await c.get_account_info()