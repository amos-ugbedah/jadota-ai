import ccxt
import asyncio
import logging
from decimal import Decimal
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet

from ..models.exchange import ExchangeAccount, ExchangeOrder, ExchangeBalance
from ..schemas.exchange import ExchangeAccountCreate, ExchangeOrderCreate
from ..core.config import settings

logger = logging.getLogger(__name__)

class ExchangeService:
    """Service for interacting with Bitget exchange."""
    
    def __init__(self):
        # Initialize encryption
        self.fernet = Fernet(settings.encryption_key.encode())
        self.exchange_name = "bitget"
    
    def _encrypt_secret(self, secret: str) -> str:
        """Encrypt a secret."""
        return self.fernet.encrypt(secret.encode()).decode()
    
    def _decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt a secret."""
        return self.fernet.decrypt(encrypted_secret.encode()).decode()
    
    def _get_exchange(self, account: ExchangeAccount) -> ccxt.bitget:
        """Get initialized exchange instance."""
        return ccxt.bitget({
            'apiKey': account.api_key,
            'secret': self._decrypt_secret(account.api_secret_encrypted),
            'password': self._decrypt_secret(account.passphrase_encrypted) if account.passphrase_encrypted else '',
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })
    
    async def create_account(
        self, 
        db: Session, 
        user_id: str, 
        data: ExchangeAccountCreate
    ) -> ExchangeAccount:
        """Create a new exchange account."""
        # Encrypt secrets
        encrypted_secret = self._encrypt_secret(data.api_secret.get_secret_value())
        encrypted_passphrase = self._encrypt_secret(data.passphrase) if data.passphrase else None
        
        # Create account
        account = ExchangeAccount(
            user_id=user_id,
            exchange="BITGET",
            api_key=data.api_key,
            api_secret_encrypted=encrypted_secret,
            passphrase_encrypted=encrypted_passphrase,
            ip_whitelist=data.ip_whitelist or []
        )
        
        db.add(account)
        db.commit()
        db.refresh(account)
        
        # Verify connection
        await self.verify_connection(db, account.id)
        
        return account
    
    async def verify_connection(self, db: Session, account_id: str) -> bool:
        """Verify exchange connection."""
        account = db.query(ExchangeAccount).filter(
            ExchangeAccount.id == account_id
        ).first()
        
        if not account:
            raise ValueError("Account not found")
        
        try:
            exchange = self._get_exchange(account)
            
            # Test connection by fetching balance
            await asyncio.to_thread(exchange.fetch_balance)
            
            account.is_verified = True
            account.last_verified_at = datetime.utcnow()
            db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Exchange verification failed: {e}")
            account.is_verified = False
            db.commit()
            raise ValueError(f"Connection failed: {str(e)}")
    
    async def get_balance(
        self, 
        db: Session, 
        user_id: str,
        asset: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get exchange balance."""
        account = db.query(ExchangeAccount).filter(
            ExchangeAccount.user_id == user_id,
            ExchangeAccount.is_active == True
        ).first()
        
        if not account:
            raise ValueError("No active exchange account found")
        
        try:
            exchange = self._get_exchange(account)
            balance = await asyncio.to_thread(exchange.fetch_balance)
            
            # Store balance in database
            for asset_name, asset_data in balance['total'].items():
                if asset_data > 0 or (asset and asset.upper() == asset_name):
                    # Update or create balance record
                    existing = db.query(ExchangeBalance).filter(
                        ExchangeBalance.user_id == user_id,
                        ExchangeBalance.exchange_account_id == account.id,
                        ExchangeBalance.asset == asset_name
                    ).first()
                    
                    if existing:
                        existing.total = asset_data
                        existing.free = balance['free'].get(asset_name, 0)
                        existing.used = balance['used'].get(asset_name, 0)
                        existing.updated_at = datetime.utcnow()
                    else:
                        new_balance = ExchangeBalance(
                            user_id=user_id,
                            exchange_account_id=account.id,
                            asset=asset_name,
                            total=asset_data,
                            free=balance['free'].get(asset_name, 0),
                            used=balance['used'].get(asset_name, 0)
                        )
                        db.add(new_balance)
            
            db.commit()
            
            # Return balances
            if asset:
                asset_data = balance['total'].get(asset.upper(), 0)
                return [{
                    'asset': asset.upper(),
                    'total': asset_data,
                    'free': balance['free'].get(asset.upper(), 0),
                    'used': balance['used'].get(asset.upper(), 0),
                    'updated_at': datetime.utcnow()
                }]
            
            return [{
                'asset': asset_name,
                'total': balance['total'].get(asset_name, 0),
                'free': balance['free'].get(asset_name, 0),
                'used': balance['used'].get(asset_name, 0),
                'updated_at': datetime.utcnow()
            } for asset_name, asset_data in balance['total'].items() if asset_data > 0]
            
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            raise ValueError(f"Balance fetch failed: {str(e)}")
    
    async def place_order(
        self,
        db: Session,
        user_id: str,
        order_data: ExchangeOrderCreate
    ) -> Dict[str, Any]:
        """Place an order on the exchange."""
        account = db.query(ExchangeAccount).filter(
            ExchangeAccount.user_id == user_id,
            ExchangeAccount.is_active == True,
            ExchangeAccount.permissions_trade == True
        ).first()
        
        if not account:
            raise ValueError("No active exchange account with trading permissions")
        
        try:
            exchange = self._get_exchange(account)
            
            # Prepare order parameters
            symbol = order_data.symbol
            side = order_data.side.lower()
            order_type = order_data.order_type.lower()
            quantity = float(order_data.quantity)
            
            params = {}
            if order_data.stop_price:
                params['stopPrice'] = float(order_data.stop_price)
            
            # Place order
            if order_type == 'market':
                order = await asyncio.to_thread(
                    exchange.create_market_order,
                    symbol, side, quantity
                )
            elif order_type == 'limit':
                price = float(order_data.price) if order_data.price else None
                if not price:
                    raise ValueError("Price required for limit orders")
                order = await asyncio.to_thread(
                    exchange.create_limit_order,
                    symbol, side, quantity, price
                )
            elif order_type == 'stop':
                stop_price = float(order_data.stop_price) if order_data.stop_price else None
                if not stop_price:
                    raise ValueError("Stop price required for stop orders")
                order = await asyncio.to_thread(
                    exchange.create_order,
                    symbol, order_type, side, quantity, None, {'stopPrice': stop_price}
                )
            else:
                raise ValueError(f"Unsupported order type: {order_type}")
            
            # Store order in database
            exchange_order = ExchangeOrder(
                user_id=user_id,
                exchange_account_id=account.id,
                symbol=order_data.symbol,
                side=order_data.side,
                order_type=order_data.order_type,
                quantity=order_data.quantity,
                price=order_data.price,
                stop_price=order_data.stop_price,
                exchange_order_id=order.get('id'),
                status=order.get('status', 'OPEN').upper(),
                exchange_response=order
            )
            
            # Update with execution details if filled
            if order.get('filled') and order.get('filled') > 0:
                exchange_order.executed_quantity = order.get('filled', 0)
                exchange_order.executed_price = order.get('price', 0)
                exchange_order.avg_price = order.get('average', 0)
                exchange_order.executed_at = datetime.utcnow()
                if order.get('fee'):
                    exchange_order.fee = order['fee'].get('cost', 0)
                    exchange_order.fee_currency = order['fee'].get('currency', 'USDT')
            
            db.add(exchange_order)
            db.commit()
            db.refresh(exchange_order)
            
            return {
                'id': exchange_order.id,
                'exchange_order_id': exchange_order.exchange_order_id,
                'symbol': exchange_order.symbol,
                'side': exchange_order.side,
                'order_type': exchange_order.order_type,
                'quantity': float(exchange_order.quantity),
                'executed_quantity': float(exchange_order.executed_quantity or 0),
                'executed_price': float(exchange_order.executed_price) if exchange_order.executed_price else None,
                'status': exchange_order.status,
                'message': 'Order placed successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise ValueError(f"Order failed: {str(e)}")
    
    async def cancel_order(
        self,
        db: Session,
        user_id: str,
        order_id: str
    ) -> Dict[str, Any]:
        """Cancel an order on the exchange."""
        # Find the order
        exchange_order = db.query(ExchangeOrder).filter(
            ExchangeOrder.id == order_id,
            ExchangeOrder.user_id == user_id
        ).first()
        
        if not exchange_order:
            raise ValueError("Order not found")
        
        if exchange_order.status in ['FILLED', 'CANCELLED', 'FAILED']:
            return {
                'order_id': order_id,
                'status': exchange_order.status,
                'message': f'Order already {exchange_order.status.lower()}'
            }
        
        account = db.query(ExchangeAccount).filter(
            ExchangeAccount.id == exchange_order.exchange_account_id
        ).first()
        
        if not account:
            raise ValueError("Exchange account not found")
        
        try:
            exchange = self._get_exchange(account)
            
            # Cancel order
            result = await asyncio.to_thread(
                exchange.cancel_order,
                exchange_order.exchange_order_id,
                exchange_order.symbol
            )
            
            exchange_order.status = 'CANCELLED'
            exchange_order.cancelled_at = datetime.utcnow()
            db.commit()
            
            return {
                'order_id': order_id,
                'status': 'CANCELLED',
                'message': 'Order cancelled successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise ValueError(f"Cancel failed: {str(e)}")
    
    async def get_order_status(
        self,
        db: Session,
        user_id: str,
        order_id: str
    ) -> Dict[str, Any]:
        """Get order status."""
        exchange_order = db.query(ExchangeOrder).filter(
            ExchangeOrder.id == order_id,
            ExchangeOrder.user_id == user_id
        ).first()
        
        if not exchange_order:
            raise ValueError("Order not found")
        
        return {
            'id': exchange_order.id,
            'exchange_order_id': exchange_order.exchange_order_id,
            'symbol': exchange_order.symbol,
            'side': exchange_order.side,
            'order_type': exchange_order.order_type,
            'quantity': float(exchange_order.quantity),
            'executed_quantity': float(exchange_order.executed_quantity or 0),
            'executed_price': float(exchange_order.executed_price) if exchange_order.executed_price else None,
            'avg_price': float(exchange_order.avg_price) if exchange_order.avg_price else None,
            'status': exchange_order.status,
            'fee': float(exchange_order.fee) if exchange_order.fee else 0,
            'fee_currency': exchange_order.fee_currency,
            'placed_at': exchange_order.placed_at,
            'executed_at': exchange_order.executed_at
        }

# Create singleton
exchange_service = ExchangeService()
