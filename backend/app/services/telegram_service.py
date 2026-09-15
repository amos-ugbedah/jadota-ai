"""
Telegram Notification Service - Supports both individual and group notifications
"""

import logging
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegramService:
    """Service to send trading alerts via Telegram"""

    def __init__(self):
        self.bot_token: Optional[str] = None
        self.group_chat_id: Optional[str] = None
        self.is_enabled = False

    def initialize(self, bot_token: str, group_chat_id: str = None):
        """Initialize the Telegram service"""
        self.bot_token = bot_token
        self.group_chat_id = group_chat_id
        self.is_enabled = bool(bot_token)

        if self.is_enabled:
            logger.info(f"✅ Telegram Service initialized (Group: {group_chat_id or 'Not set'})")
        else:
            logger.warning("⚠️ Telegram Service disabled - missing bot token")

    async def send_message(
        self,
        chat_id: Optional[str] = None,
        message: Optional[str] = None,
        parse_mode: str = "HTML",
    ) -> bool:
        """
        Send a message to a specific chat (user or group).

        Usage:
            await telegram_service.send_message(chat_id, message)
            await telegram_service.send_message(chat_id="-123", message="hi")
            await telegram_service.send_message(message="hi")   # uses group chat id
        """
        # 🔥 Fallback: if caller passed only one positional arg, treat it as the message
        if message is None and chat_id is not None:
            message = chat_id
            chat_id = None

        # 🔥 Resolve chat_id (default to group chat)
        if chat_id is None:
            chat_id = self.group_chat_id

        if not self.is_enabled:
            logger.warning("⚠️ Telegram not enabled - message not sent")
            return False

        if not chat_id:
            logger.warning("⚠️ No chat_id provided and no group_chat_id set")
            return False

        if not message:
            logger.warning("⚠️ Empty message - nothing to send")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    json={
                        "chat_id": str(chat_id),
                        "text": message,
                        "parse_mode": parse_mode,
                        "disable_web_page_preview": True,
                    },
                )

                if response.status_code == 200:
                    logger.info(f"📨 Telegram message sent to {chat_id}")
                    return True

                # 🔥 Log full Telegram error so we can debug the actual cause
                try:
                    err = response.json()
                    desc = err.get("description", "unknown error")
                except Exception:
                    desc = response.text[:200]

                logger.error(
                    f"❌ Telegram send failed (HTTP {response.status_code}): {desc}"
                )
                return False

        except httpx.TimeoutException:
            logger.error("❌ Telegram request timed out")
            return False
        except httpx.HTTPError as e:
            logger.error(f"❌ Telegram HTTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Telegram unexpected error: {e}")
            return False

    async def send_to_group(self, message: str) -> bool:
        """Send a message to the public group"""
        if not self.group_chat_id:
            logger.warning("⚠️ Group Chat ID not set - message not sent")
            return False
        return await self.send_message(chat_id=self.group_chat_id, message=message)

    async def send_public_trade_alert(
        self, trade: Dict[str, Any], action: str, user: Dict[str, Any] = None
    ):
        """Send trade alert to the public group with user info"""
        symbol = trade.get("symbol", "Unknown")
        side = trade.get("side", "N/A")
        price = trade.get("entryPrice", 0)
        confidence = trade.get("aiConfidence", 0)

        # User info
        if user:
            user_name = user.get("full_name", user.get("username", "Unknown User"))
            user_email = user.get("email", "")
            user_display = f"{user_name} ({user_email})" if user_email else user_name
        else:
            user_display = "🤖 AI System"

        side_emoji = "📈" if side == "BUY" else "📉"

        if action == "OPEN":
            message = f"""
<b>🤖 JADOTA AI - New Trade</b>
━━━━━━━━━━━━━━━━━━━━━━
👤 <b>Trader:</b> {user_display}
{side_emoji} <b>{action}</b> {side_emoji} {symbol}

💰 Price: ${price:,.2f}
📊 AI Confidence: {confidence}%
━━━━━━━━━━━━━━━━━━━━━━
📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
"""
        else:
            pnl = trade.get("realizedPnl", 0)
            exit_price = trade.get("currentPrice", 0)
            pnl_emoji = "🎉💰" if pnl >= 0 else "😱💸"
            result_text = "PROFIT" if pnl >= 0 else "LOSS"
            pnl_display = f"+${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"

            message = f"""
<b>🤖 JADOTA AI - Trade Result</b>
━━━━━━━━━━━━━━━━━━━━━━
👤 <b>Trader:</b> {user_display}
{pnl_emoji} <b>{result_text}</b> {side_emoji} {symbol}

📊 Entry: ${trade.get('entryPrice', 0):,.2f}
📊 Exit: ${exit_price:,.2f}
💵 <b>P&L: {pnl_display}</b>
📊 AI Confidence: {confidence}%
━━━━━━━━━━━━━━━━━━━━━━
📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
"""

        await self.send_to_group(message)

    async def send_trade_alert(self, trade: Dict[str, Any], action: str):
        """Send private trade alert to admin/group"""
        symbol = trade.get("symbol", "Unknown")
        side = trade.get("side", "N/A")
        price = trade.get("entryPrice", 0)
        confidence = trade.get("aiConfidence", 0)
        reasoning = trade.get("aiReasoning", "")

        side_emoji = "📈" if side == "BUY" else "📉"
        action_emoji = {
            "OPEN": "✅",
            "STOP_LOSS": "🛑",
            "TAKE_PROFIT": "🎯",
            "MANUAL": "✋",
        }.get(action, "ℹ️")

        if action == "OPEN":
            message = f"""
<b>🤖 JADOTA AI - Trade Alert</b>
━━━━━━━━━━━━━━━━━━━━━━
{action_emoji} <b>{action}</b> {side_emoji} {symbol}

💰 Price: ${price:,.2f}
📊 Confidence: {confidence}%
💡 Reason: {reasoning[:60]}...
━━━━━━━━━━━━━━━━━━━━━━
📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
"""
        else:
            pnl = trade.get("realizedPnl", 0)
            exit_price = trade.get("currentPrice", 0)
            pnl_emoji = "💰" if pnl >= 0 else "💸"

            message = f"""
<b>🤖 JADOTA AI - Position Closed</b>
━━━━━━━━━━━━━━━━━━━━━━
{action_emoji} <b>{action}</b> {side_emoji} {symbol}

📊 Entry: ${trade.get('entryPrice', 0):,.2f}
📊 Exit: ${exit_price:,.2f}
{pnl_emoji} P&L: <b>${pnl:,.2f}</b>
📊 Confidence: {confidence}%
━━━━━━━━━━━━━━━━━━━━━━
📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
"""

        await self.send_to_group(message)


# Singleton
telegram_service = TelegramService()