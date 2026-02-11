"""
LINE Bot Handler for QuickChat ID
Integrates ADK agents with LINE Messaging API
"""

from typing import Dict, List, Optional
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

class LineBotHandler:
    """
    LINE Bot handler for QuickChat ID KYC process.
    
    Integrates ADK agents with LINE Messaging API.
    """
    
    def __init__(self, channel_access_token: str, channel_secret: str):
        """
        Initialize LINE Bot.
        
        Args:
            channel_access_token: LINE Channel Access Token
            channel_secret: LINE Channel Secret
        """
        self.channel_access_token = channel_access_token
        self.channel_secret = channel_secret
        
        # Initialize LINE Bot API (will check if library available)
        self._init_line_api()
        
        # Session storage (use Redis in production)
        self.sessions = {}
    
    def _init_line_api(self):
        """Initialize LINE Bot API"""
        try:
            from linebot import LineBotApi, WebhookHandler
            self.line_bot_api = LineBotApi(self.channel_access_token)
            self.handler = WebhookHandler(self.channel_secret)
            self.line_available = True
        except ImportError:
            print("⚠️  LINE Bot SDK not installed. Install with: pip install line-bot-sdk")
            self.line_available = False
    
    def send_text_message(self, user_id: str, text: str):
        """Send text message to user"""
        if not self.line_available:
            print(f"[MOCK] Send to {user_id}: {text}")
            return
        
        try:
            from linebot.models import TextSendMessage
            self.line_bot_api.push_message(
                user_id,
                TextSendMessage(text=text)
            )
        except Exception as e:
            print(f"LINE API Error: {e}")
    
    def send_quick_reply(self, user_id: str, text: str, options: List[str]):
        """Send message with quick reply buttons"""
        if not self.line_available:
            print(f"[MOCK] Quick Reply to {user_id}: {text}")
            print(f"[MOCK] Options: {options}")
            return
        
        try:
            from linebot.models import TextSendMessage, QuickReply, QuickReplyButton, MessageAction
            
            quick_reply_buttons = [
                QuickReplyButton(action=MessageAction(label=opt, text=opt))
                for opt in options
            ]
            
            self.line_bot_api.push_message(
                user_id,
                TextSendMessage(
                    text=text,
                    quick_reply=QuickReply(items=quick_reply_buttons)
                )
            )
        except Exception as e:
            print(f"LINE API Error: {e}")
    
    def send_flex_message(self, user_id: str, alt_text: str, flex_content: Dict):
        """Send Flex Message (for rich UI)"""
        if not self.line_available:
            print(f"[MOCK] Flex Message to {user_id}: {alt_text}")
            return
        
        try:
            from linebot.models import FlexSendMessage
            self.line_bot_api.push_message(
                user_id,
                FlexSendMessage(
                    alt_text=alt_text,
                    contents=flex_content
                )
            )
        except Exception as e:
            print(f"LINE API Error: {e}")
    
    def create_kyc_welcome_flex(self) -> Dict:
        """Create welcome Flex Message for KYC"""
        return {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://via.placeholder.com/1040x1040/4285F4/FFFFFF?text=QuickChat+ID",
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "QuickChat ID",
                        "weight": "bold",
                        "size": "xl"
                    },
                    {
                        "type": "text",
                        "text": "ยืนยันตัวตนใน 5-7 วินาที",
                        "size": "sm",
                        "color": "#999999",
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "xxl"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "xxl",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "text",
                                "text": "📝 ขั้นตอน:",
                                "weight": "bold"
                            },
                            {
                                "type": "text",
                                "text": "1️⃣ แชร์ข้อมูลพื้นฐาน",
                                "size": "sm",
                                "color": "#555555"
                            },
                            {
                                "type": "text",
                                "text": "2️⃣ ถ่ายรูปบัตรประชาชน",
                                "size": "sm",
                                "color": "#555555"
                            },
                            {
                                "type": "text",
                                "text": "3️⃣ ถ่าย Selfie",
                                "size": "sm",
                                "color": "#555555"
                            },
                            {
                                "type": "text",
                                "text": "4️⃣ รับ Trust Badge",
                                "size": "sm",
                                "color": "#555555"
                            }
                        ]
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "เริ่มยืนยันตัวตน",
                            "text": "พร้อม"
                        }
                    }
                ],
                "flex": 0
            }
        }
    
    def create_trust_badge_flex(self, trust_level: str, risk_score: float, 
                                transaction_limit: int) -> Dict:
        """Create Trust Badge result Flex Message"""
        
        badge_colors = {
            'bronze': '#CD7F32',
            'silver': '#C0C0C0',
            'gold': '#FFD700',
            'platinum': '#E5E4E2'
        }
        
        badge_emojis = {
            'bronze': '🥉',
            'silver': '🥈',
            'gold': '🥇',
            'platinum': '💎'
        }
        
        color = badge_colors.get(trust_level, '#999999')
        emoji = badge_emojis.get(trust_level, '✅')
        
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🎉 ยืนยันตัวตนสำเร็จ!",
                        "weight": "bold",
                        "size": "xl",
                        "align": "center"
                    },
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "xl",
                        "spacing": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"{emoji} {trust_level.upper()} BADGE",
                                "size": "xxl",
                                "weight": "bold",
                                "color": color,
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": f"Risk Score: {risk_score:.1f}/100",
                                "size": "sm",
                                "color": "#999999",
                                "align": "center"
                            },
                            {
                                "type": "separator",
                                "margin": "xl"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "margin": "xl",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "วงเงินธุรกรรม:",
                                        "size": "sm",
                                        "color": "#555555",
                                        "flex": 0
                                    },
                                    {
                                        "type": "text",
                                        "text": f"฿{transaction_limit:,}" if transaction_limit > 0 else "ไม่จำกัด",
                                        "size": "sm",
                                        "color": "#111111",
                                        "align": "end"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }


# Factory function
def create_line_bot(channel_access_token: str = None, 
                   channel_secret: str = None) -> LineBotHandler:
    """
    Create LINE Bot instance.
    
    Reads from environment variables if not provided.
    """
    if not channel_access_token:
        channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    
    if not channel_secret:
        channel_secret = os.getenv('LINE_CHANNEL_SECRET')
    
    if not channel_access_token or not channel_secret:
        raise ValueError("LINE credentials not provided")
    
    return LineBotHandler(channel_access_token, channel_secret)
