"""
Webhook Handler for LINE and Messenger
Routes webhook events to appropriate handlers
"""

from flask import Flask, request, abort
from typing import Dict, Callable
import json
import hmac
import hashlib

class WebhookHandler:
    """
    Universal webhook handler for chat platforms.
    
    Supports:
    - LINE Messaging API
    - Facebook Messenger
    """
    
    def __init__(self, app: Flask):
        """
        Initialize webhook handler.
        
        Args:
            app: Flask application
        """
        self.app = app
        self.handlers = {
            'line': {},
            'messenger': {}
        }
    
    def register_line_handler(self, event_type: str, handler: Callable):
        """Register handler for LINE events"""
        self.handlers['line'][event_type] = handler
    
    def register_messenger_handler(self, event_type: str, handler: Callable):
        """Register handler for Messenger events"""
        self.handlers['messenger'][event_type] = handler
    
    def setup_line_webhook(self, path: str = '/webhook/line'):
        """Setup LINE webhook endpoint"""
        
        @self.app.route(path, methods=['POST'])
        def line_webhook():
            # Get signature
            signature = request.headers.get('X-Line-Signature', '')
            
            # Get request body
            body = request.get_data(as_text=True)
            
            # Verify signature
            if not self._verify_line_signature(body, signature):
                abort(400)
            
            # Parse events
            try:
                events = json.loads(body).get('events', [])
            except:
                abort(400)
            
            # Handle events
            for event in events:
                event_type = event.get('type')
                handler = self.handlers['line'].get(event_type)
                
                if handler:
                    handler(event)
            
            return 'OK', 200
    
    def setup_messenger_webhook(self, path: str = '/webhook/messenger'):
        """Setup Messenger webhook endpoint"""
        
        @self.app.route(path, methods=['GET', 'POST'])
        def messenger_webhook():
            if request.method == 'GET':
                # Webhook verification
                mode = request.args.get('hub.mode')
                token = request.args.get('hub.verify_token')
                challenge = request.args.get('hub.challenge')
                
                from services.messenger_bot_service import get_messenger_bot_service
                messenger = get_messenger_bot_service()
                
                result = messenger.verify_webhook(mode, token, challenge)
                if result:
                    return result, 200
                else:
                    abort(403)
            
            else:  # POST
                # Handle events
                data = request.get_json()
                
                if data.get('object') == 'page':
                    entries = data.get('entry', [])
                    
                    for entry in entries:
                        webhooks = entry.get('messaging', [])
                        
                        for webhook_event in webhooks:
                            # Determine event type
                            if webhook_event.get('message'):
                                event_type = 'message'
                            elif webhook_event.get('postback'):
                                event_type = 'postback'
                            else:
                                continue
                            
                            handler = self.handlers['messenger'].get(event_type)
                            
                            if handler:
                                handler(webhook_event)
                
                return 'OK', 200
    
    def _verify_line_signature(self, body: str, signature: str) -> bool:
        """Verify LINE signature"""
        try:
            from services.line_bot_service import get_line_bot_service
            line_bot = get_line_bot_service()
            return line_bot.verify_signature(body, signature)
        except:
            return True  # Skip verification if service not available


def create_webhook_app() -> Flask:
    """Create Flask app with webhook handlers"""
    app = Flask(__name__)
    handler = WebhookHandler(app)
    
    # Setup webhooks
    handler.setup_line_webhook()
    handler.setup_messenger_webhook()
    
    return app, handler
