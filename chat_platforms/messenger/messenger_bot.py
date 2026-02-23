"""
Facebook Messenger Bot Handler for QuickChat ID
Mirrors structure of chat_platforms/line/line_bot.py
"""

import hashlib
import hmac
import requests
from typing import Optional


class MessengerBotHandler:
    """
    Facebook Messenger bot handler for QuickChat ID KYC process.

    Uses Facebook Graph API v18.0 Send API to deliver messages.
    Badge displayed as Generic Template (Messenger equivalent of LINE Flex Message).
    """

    API_BASE = "https://graph.facebook.com/v18.0/me"

    def __init__(self, page_access_token: str, app_secret: str):
        """
        Initialize Messenger bot.

        Args:
            page_access_token: Facebook Page Access Token
            app_secret: Facebook App Secret (for signature verification)
        """
        self.page_access_token = page_access_token
        self.app_secret = app_secret

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify X-Hub-Signature-256 header from Facebook webhook.

        Args:
            payload: Raw request body bytes
            signature: Value of X-Hub-Signature-256 header (format: 'sha256=...')
        """
        expected = 'sha256=' + hmac.new(
            self.app_secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def send_text_message(self, recipient_id: str, text: str):
        """
        Send plain text message. Auto-splits if over 2000 chars (Messenger limit).

        Args:
            recipient_id: Facebook Page-scoped user ID (PSID)
            text: Message text
        """
        chunks = [text[i:i+2000] for i in range(0, len(text), 2000)]
        for chunk in chunks:
            self._call_send_api({
                "recipient": {"id": recipient_id},
                "message": {"text": chunk}
            })

    def send_badge_card(self, recipient_id: str, trust_level: str,
                        risk_score: float, name: str = None, issued_date: str = None):
        """
        Send Trust Badge as Generic Template card (Messenger equivalent of LINE Flex Message).

        Args:
            recipient_id: Facebook PSID
            trust_level: 'bronze', 'silver', 'gold', or 'platinum'
            risk_score: Numeric score 0-100
            name: User's full name (optional)
            issued_date: Issue date string e.g. '20/02/2026' (optional)
        """
        badge_emoji = {
            'bronze': '🥉',
            'silver': '🥈',
            'gold': '🥇',
            'platinum': '💎'
        }
        level = trust_level.lower()
        title = f"{badge_emoji.get(level, '🏅')} {level.upper()} BADGE — ยืนยันตัวตนสำเร็จ"

        subtitle_parts = [f"คะแนน: {risk_score:.0f}/100"]
        if name:
            subtitle_parts.insert(0, f"👤 {name}")
        if issued_date:
            subtitle_parts.append(f"วันที่: {issued_date}")

        self._call_send_api({
            "recipient": {"id": recipient_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "generic",
                        "elements": [{
                            "title": title,
                            "subtitle": " | ".join(subtitle_parts),
                            "buttons": [{
                                "type": "postback",
                                "title": "ดูสถานะ",
                                "payload": "STATUS"
                            }]
                        }]
                    }
                }
            }
        })

    def download_image(self, url: str, save_path: str) -> bool:
        """
        Download image from Facebook CDN (requires page access token).

        Args:
            url: Facebook attachment URL
            save_path: Local file path to save image

        Returns:
            True if successful, False otherwise
        """
        try:
            r = requests.get(
                url,
                params={'access_token': self.page_access_token},
                timeout=30
            )
            if r.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(r.content)
                return True
            else:
                print(f"⚠️  FB image download HTTP {r.status_code}")
        except Exception as e:
            print(f"⚠️  Messenger image download failed: {e}")
        return False

    def _call_send_api(self, payload: dict):
        """Internal: POST to Messenger Send API"""
        try:
            r = requests.post(
                f"{self.API_BASE}/messages",
                params={"access_token": self.page_access_token},
                json=payload,
                timeout=10
            )
            if r.status_code != 200:
                print(f"⚠️  Messenger API error: {r.status_code} {r.text[:200]}")
        except Exception as e:
            print(f"⚠️  Messenger send failed: {e}")
