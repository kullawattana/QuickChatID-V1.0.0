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
                                transaction_limit: int, name: str = None,
                                issued_date: str = None, role: str = None) -> Dict:
        """Create Trust Badge result Flex Message"""
        import datetime

        badge_config = {
            'bronze': {'color': '#CD7F32', 'bg': '#FFF8F0', 'emoji': '🥉', 'label': 'BRONZE'},
            'silver': {'color': '#808080', 'bg': '#F5F5F5', 'emoji': '🥈', 'label': 'SILVER'},
            'gold':   {'color': '#B8860B', 'bg': '#FFFDE7', 'emoji': '🥇', 'label': 'GOLD'},
            'platinum': {'color': '#5C5C5C', 'bg': '#F3F0FF', 'emoji': '💎', 'label': 'PLATINUM'},
        }
        benefits_map = {
            'bronze':   ['ยืนยันตัวตนขั้นพื้นฐาน', 'ธุรกรรมมาตรฐาน', 'อีเมลซัพพอร์ต'],
            'silver':   ['ยืนยันตัวตนขั้นสูง', 'ประมวลผลด่วน', 'Chat ซัพพอร์ต', 'ค่าธรรมเนียมต่ำลง'],
            'gold':     ['ยืนยันตัวตนพรีเมียม', 'Fast-track', 'ซัพพอร์ต 24/7', 'ยกเว้นค่าธรรมเนียม', 'ฟีเจอร์พิเศษ'],
            'platinum': ['ยืนยันระดับสูงสุด', 'ประมวลผลทันที', 'ผู้จัดการเฉพาะ', 'ฟรีทุกค่าธรรมเนียม', 'สิทธิ์ VIP'],
        }
        role_config = {
            'seller': {
                'icon': '🏪', 'label': 'ผู้ขาย ที่ผ่านการยืนยัน',
                'header_color': '#E65100', 'header_bg': '#FFF3E0',
                'benefits': ['เปิดร้านค้าออนไลน์ได้', 'รับชำระเงินได้', 'วงเงินตามระดับ Badge', 'แสดงป้ายผู้ขายน่าเชื่อถือ'],
            },
            'buyer': {
                'icon': '🛒', 'label': 'ผู้ซื้อ ที่ผ่านการยืนยัน',
                'header_color': '#1565C0', 'header_bg': '#E3F2FD',
                'benefits': ['ซื้อสินค้าออนไลน์ได้', 'ความคุ้มครองผู้ซื้อ', 'วงเงินซื้อสินค้า', 'Fast checkout'],
            },
        }

        cfg = badge_config.get(trust_level.lower(), badge_config['bronze'])
        role_key = (role or '').lower()
        rcfg = role_config.get(role_key)

        # Override header bg/color and benefits if role is specified
        if rcfg:
            cfg = dict(cfg)
            cfg['bg'] = rcfg['header_bg']
            benefits = rcfg['benefits']
            header_title = f"{rcfg['icon']} {rcfg['label']}"
        else:
            benefits = benefits_map.get(trust_level.lower(), [])
            header_title = "🎉 ยืนยันตัวตนสำเร็จ!"

        limit_text = f"฿{transaction_limit:,}" if transaction_limit > 0 else "ไม่จำกัด"
        score_text = f"{risk_score:.0f}/100"
        issued_text = issued_date or datetime.datetime.now().strftime('%d/%m/%Y')
        expires_text = (datetime.datetime.now() + datetime.timedelta(days=365)).strftime('%d/%m/%Y')

        # Build benefits rows
        benefit_rows = [
            {
                "type": "box",
                "layout": "horizontal",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "✓", "size": "sm", "color": cfg['color'], "flex": 0},
                    {"type": "text", "text": b, "size": "sm", "color": "#444444", "wrap": True}
                ]
            }
            for b in benefits
        ]

        name_row = []
        if name:
            name_row = [
                {
                    "type": "text",
                    "text": name,
                    "size": "md",
                    "color": "#333333",
                    "align": "center",
                    "margin": "sm"
                }
            ]

        return {
            "type": "bubble",
            "styles": {
                "header": {"backgroundColor": cfg['bg']},
                "body": {"backgroundColor": "#FFFFFF"}
            },
            "header": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "20px",
                "contents": [
                    {
                        "type": "text",
                        "text": header_title,
                        "weight": "bold",
                        "size": "lg",
                        "align": "center",
                        "color": rcfg['header_color'] if rcfg else "#333333"
                    },
                    {
                        "type": "text",
                        "text": f"{cfg['emoji']} {cfg['label']} BADGE",
                        "size": "xxl",
                        "weight": "bold",
                        "color": cfg['color'],
                        "align": "center",
                        "margin": "md"
                    },
                    *name_row
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "paddingAll": "20px",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "คะแนนความน่าเชื่อถือ", "size": "sm", "color": "#888888", "flex": 2},
                            {"type": "text", "text": score_text, "size": "sm", "color": cfg['color'], "weight": "bold", "align": "end", "flex": 1}
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "วงเงินธุรกรรม", "size": "sm", "color": "#888888", "flex": 2},
                            {"type": "text", "text": limit_text, "size": "sm", "color": "#111111", "weight": "bold", "align": "end", "flex": 1}
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "วันที่ออก", "size": "sm", "color": "#888888", "flex": 2},
                            {"type": "text", "text": issued_text, "size": "sm", "color": "#111111", "align": "end", "flex": 1}
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "วันหมดอายุ", "size": "sm", "color": "#888888", "flex": 2},
                            {"type": "text", "text": expires_text, "size": "sm", "color": "#111111", "align": "end", "flex": 1}
                        ]
                    },
                    {"type": "separator", "margin": "md"},
                    {
                        "type": "text",
                        "text": "สิทธิประโยชน์",
                        "size": "sm",
                        "weight": "bold",
                        "color": "#555555",
                        "margin": "md"
                    },
                    *benefit_rows
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "color": cfg['color'],
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "ดูสถานะ",
                            "text": "สถานะ"
                        }
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
