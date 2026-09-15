#!/usr/bin/env python
"""
Test Group Telegram Notification
Run: python test_group.py
"""

import sys
import os
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.telegram_service import telegram_service

async def test_group():
    """Test sending a message to the group"""
    bot_token = "8695108065:AAFlfehpafput0kfRiNSdCr2URyO3Fd7Stc"
    group_chat_id = "-5400784433"
    
    telegram_service.initialize(bot_token, group_chat_id)
    
    message = """
<b>🧪 JADOTA AI - Group Test</b>
━━━━━━━━━━━━━━━━━━━━━━
✅ Group Telegram is working!
📊 Your AI trading alerts will appear here.
📈 Auto-Trade alerts: OPEN, STOP_LOSS, TAKE_PROFIT
━━━━━━━━━━━━━━━━━━━━━━
👤 This message is from the JADOTA AI Bot
📅 {timestamp}
"""
    success = await telegram_service.send_to_group(message.format(
        timestamp=__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    ))
    
    if success:
        print("✅ Group test notification sent! Check your Telegram group @JADOTA AI TRADE")
    else:
        print("❌ Failed to send group notification. Check group chat ID and bot permissions.")

if __name__ == "__main__":
    asyncio.run(test_group())