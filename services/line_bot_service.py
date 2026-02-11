"""
LINE Bot Service
Integrate QuickChat ID with LINE Messaging API
"""

from typing import Dict, List, Optional
import requests
import json

class LINEBotService:
    """
    LINE Bot integration for QuickChat ID.
    
    Features:
    - Send/receive messages
    - Rich menus
    - Image upload handling
    - Session management
    - Quick replies
    """
    
    def __init__(self, 
                 channel_access_token: str,
                 channel_secret: str):
        """
        Initialize LINE Bot.
        
        Args:
            channel_access_token: LINE Channel Access Token
            channel_secret: LINE Channel Secret
        """
        self.channel_access_token = channel_access_token
        self.channel_secret = channel_secret
        self.api_endpoint = "https://api.line.me/v2/bot"
        
    def send_text_message(self, 
                         user_id: str, 
                         text: str,
                         quick_reply: Optional[Dict] = None) -> Dict:
        """
        Send text message to user.
        
        Args:
            user_id: LINE user ID
            text: Message text
            quick_reply: Quick reply buttons
            
        Returns:
            Response from LINE API
        """
        url = f"{self.api_endpoint}/message/push"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.channel_access_token}"
        }
        
        message = {
            "type": "text",
            "text": text
        }
        
        if quick_reply:
            message["quickReply"] = quick_reply
        
        payload = {
            "to": user_id,
            "messages": [message]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            return {"success": True, "status": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_image_message(self, user_id: str, image_url: str) -> Dict:
        """Send image message"""
        url = f"{self.api_endpoint}/message/push"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.channel_access_token}"
        }
        
        payload = {
            "to": user_id,
            "messages": [{
                "type": "image",
                "originalContentUrl": image_url,
                "previewImageUrl": image_url
            }]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            return {"success": True, "status": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_flex_message(self, user_id: str, alt_text: str, contents: Dict) -> Dict:
        """
        Send Flex Message (rich UI).
        
        Perfect for showing verification results.
        """
        url = f"{self.api_endpoint}/message/push"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.channel_access_token}"
        }
        
        payload = {
            "to": user_id,
            "messages": [{
                "type": "flex",
                "altText": alt_text,
                "contents": contents
            }]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            return {"success": True, "status": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_profile(self, user_id: str) -> Dict:
        """Get LINE user profile"""
        url = f"{self.api_endpoint}/profile/{user_id}"
        
        headers = {
            "Authorization": f"Bearer {self.channel_access_token}"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return {"success": True, "profile": response.json()}
            return {"success": False, "status": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_message_content(self, message_id: str) -> bytes:
        """
        Get image content from message.
        
        Used for retrieving ID card and selfie images.
        """
        url = f"{self.api_endpoint}/message/{message_id}/content"
        
        headers = {
            "Authorization": f"Bearer {self.channel_access_token}"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.content
            return b""
        except Exception as e:
            print(f"Error getting message content: {e}")
            return b""
    
    def create_quick_reply(self, items: List[Dict]) -> Dict:
        """
        Create quick reply buttons.
        
        Example:
            items = [
                {"label": "พร้อม", "text": "พร้อม"},
                {"label": "ยกเลิก", "text": "ยกเลิก"}
            ]
        """
        quick_reply_items = []
        
        for item in items:
            quick_reply_items.append({
                "type": "action",
                "action": {
                    "type": "message",
                    "label": item["label"],
                    "text": item["text"]
                }
            })
        
        return {
            "items": quick_reply_items
        }
    
    def create_rich_menu(self, menu_data: Dict) -> str:
        """Create rich menu (bottom menu bar)"""
        url = f"{self.api_endpoint}/richmenu"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.channel_access_token}"
        }
        
        try:
            response = requests.post(url, headers=headers, json=menu_data, timeout=10)
            if response.status_code == 200:
                return response.json().get("richMenuId", "")
            return ""
        except Exception as e:
            print(f"Error creating rich menu: {e}")
            return ""
    
    def verify_signature(self, body: str, signature: str) -> bool:
        """
        Verify webhook signature from LINE.
        
        Security check to ensure requests are from LINE.
        """
        import hmac
        import hashlib
        import base64
        
        hash_digest = hmac.new(
            self.channel_secret.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        calculated_signature = base64.b64encode(hash_digest).decode('utf-8')
        
        return calculated_signature == signature


# Singleton
_line_bot_service = None

def get_line_bot_service(
    channel_access_token: Optional[str] = None,
    channel_secret: Optional[str] = None
):
    """Get singleton instance"""
    global _line_bot_service
    
    if _line_bot_service is None:
        import os
        token = channel_access_token or os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
        secret = channel_secret or os.getenv("LINE_CHANNEL_SECRET", "")
        _line_bot_service = LINEBotService(token, secret)
    
    return _line_bot_service
