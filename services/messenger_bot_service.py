"""
Facebook Messenger Bot Service
Integrate QuickChat ID with Messenger Platform
"""

from typing import Dict, List, Optional
import requests
import json

class MessengerBotService:
    """
    Messenger Bot integration for QuickChat ID.
    
    Features:
    - Send/receive messages
    - Templates
    - Quick replies
    - Image upload handling
    - Session management
    """
    
    def __init__(self,
                 page_access_token: str,
                 verify_token: str):
        """
        Initialize Messenger Bot.
        
        Args:
            page_access_token: Facebook Page Access Token
            verify_token: Webhook verification token
        """
        self.page_access_token = page_access_token
        self.verify_token = verify_token
        self.api_endpoint = "https://graph.facebook.com/v18.0/me/messages"
    
    def send_text_message(self,
                         recipient_id: str,
                         text: str,
                         quick_replies: Optional[List[Dict]] = None) -> Dict:
        """
        Send text message to user.
        
        Args:
            recipient_id: Messenger user ID (PSID)
            text: Message text
            quick_replies: Quick reply buttons
            
        Returns:
            Response from Messenger API
        """
        params = {"access_token": self.page_access_token}
        
        message = {
            "text": text
        }
        
        if quick_replies:
            message["quick_replies"] = quick_replies
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": message
        }
        
        try:
            response = requests.post(
                self.api_endpoint,
                params=params,
                json=payload,
                timeout=10
            )
            return {"success": True, "status": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_image_message(self, recipient_id: str, image_url: str) -> Dict:
        """Send image message"""
        params = {"access_token": self.page_access_token}
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": {
                "attachment": {
                    "type": "image",
                    "payload": {
                        "url": image_url,
                        "is_reusable": True
                    }
                }
            }
        }
        
        try:
            response = requests.post(
                self.api_endpoint,
                params=params,
                json=payload,
                timeout=10
            )
            return {"success": True, "status": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_button_template(self,
                            recipient_id: str,
                            text: str,
                            buttons: List[Dict]) -> Dict:
        """
        Send button template message.
        
        Perfect for showing options.
        """
        params = {"access_token": self.page_access_token}
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": text,
                        "buttons": buttons
                    }
                }
            }
        }
        
        try:
            response = requests.post(
                self.api_endpoint,
                params=params,
                json=payload,
                timeout=10
            )
            return {"success": True, "status": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_generic_template(self,
                             recipient_id: str,
                             elements: List[Dict]) -> Dict:
        """
        Send generic template (carousel).
        
        Perfect for showing verification results.
        """
        params = {"access_token": self.page_access_token}
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "generic",
                        "elements": elements
                    }
                }
            }
        }
        
        try:
            response = requests.post(
                self.api_endpoint,
                params=params,
                json=payload,
                timeout=10
            )
            return {"success": True, "status": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_profile(self, user_id: str) -> Dict:
        """Get Messenger user profile"""
        url = f"https://graph.facebook.com/{user_id}"
        
        params = {
            "fields": "first_name,last_name,profile_pic",
            "access_token": self.page_access_token
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return {"success": True, "profile": response.json()}
            return {"success": False, "status": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_typing_on(self, recipient_id: str):
        """Send typing indicator"""
        params = {"access_token": self.page_access_token}
        
        payload = {
            "recipient": {"id": recipient_id},
            "sender_action": "typing_on"
        }
        
        try:
            requests.post(self.api_endpoint, params=params, json=payload, timeout=5)
        except:
            pass
    
    def send_typing_off(self, recipient_id: str):
        """Turn off typing indicator"""
        params = {"access_token": self.page_access_token}
        
        payload = {
            "recipient": {"id": recipient_id},
            "sender_action": "typing_off"
        }
        
        try:
            requests.post(self.api_endpoint, params=params, json=payload, timeout=5)
        except:
            pass
    
    def create_quick_reply(self, title: str, payload: str) -> Dict:
        """
        Create quick reply button.
        
        Example:
            quick_reply = create_quick_reply("พร้อม", "READY")
        """
        return {
            "content_type": "text",
            "title": title,
            "payload": payload
        }
    
    def create_postback_button(self, title: str, payload: str) -> Dict:
        """Create postback button"""
        return {
            "type": "postback",
            "title": title,
            "payload": payload
        }
    
    def create_url_button(self, title: str, url: str) -> Dict:
        """Create URL button"""
        return {
            "type": "web_url",
            "title": title,
            "url": url
        }
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verify webhook from Facebook.
        
        Used during webhook setup.
        """
        if mode == "subscribe" and token == self.verify_token:
            return challenge
        return None


# Singleton
_messenger_bot_service = None

def get_messenger_bot_service(
    page_access_token: Optional[str] = None,
    verify_token: Optional[str] = None
):
    """Get singleton instance"""
    global _messenger_bot_service
    
    if _messenger_bot_service is None:
        import os
        token = page_access_token or os.getenv("MESSENGER_PAGE_ACCESS_TOKEN", "")
        verify = verify_token or os.getenv("MESSENGER_VERIFY_TOKEN", "")
        _messenger_bot_service = MessengerBotService(token, verify)
    
    return _messenger_bot_service
