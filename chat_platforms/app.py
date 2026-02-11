"""
Flask App for Chat Platform Webhooks
Handles LINE and Messenger webhooks
"""

from flask import Flask, request, jsonify
import os
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.line_bot_service import get_line_bot_service
from services.messenger_bot_service import get_messenger_bot_service
from chat_platforms.adapters.adk_chat_adapter import get_adk_chat_adapter

# Create Flask app
app = Flask(__name__)

# Initialize services
line_bot = get_line_bot_service()
messenger_bot = get_messenger_bot_service()
adapter = get_adk_chat_adapter()

# Health check
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "QuickChat ID"}), 200

# LINE Webhook
@app.route('/webhook/line', methods=['POST'])
def line_webhook():
    """Handle LINE webhook events"""
    # Get signature
    signature = request.headers.get('X-Line-Signature', '')
    
    # Get body
    body = request.get_data(as_text=True)
    
    # Verify signature
    if not line_bot.verify_signature(body, signature):
        return 'Invalid signature', 403
    
    # Parse events
    import json
    try:
        data = json.loads(body)
        events = data.get('events', [])
    except:
        return 'Invalid JSON', 400
    
    # Handle each event
    for event in events:
        handle_line_event(event)
    
    return 'OK', 200

def handle_line_event(event: dict):
    """Handle single LINE event"""
    event_type = event.get('type')
    
    if event_type == 'message':
        user_id = event['source']['userId']
        message_type = event['message']['type']
        
        if message_type == 'text':
            # Text message
            text = event['message']['text']
            response = adapter.process_chat_message(user_id, text, 'line')
            
            # Send response
            line_bot.send_text_message(user_id, response['response_text'])
            
            # Send quick replies if any
            if response.get('quick_replies'):
                items = [{"label": q, "text": q} for q in response['quick_replies']]
                quick_reply = line_bot.create_quick_reply(items)
                line_bot.send_text_message(
                    user_id,
                    "เลือกหนึ่งตัวเลือก:",
                    quick_reply
                )
            
            # Send flex message for completion
            if response.get('action') == 'complete' and response.get('trust_badge_data'):
                flex = create_line_trust_badge_flex(response['trust_badge_data'])
                line_bot.send_flex_message(user_id, "Trust Badge", flex)
        
        elif message_type == 'image':
            # Image message
            message_id = event['message']['id']
            image_data = line_bot.get_message_content(message_id)
            
            if image_data:
                # Save image
                image_path = f"/tmp/{user_id}_{message_id}.jpg"
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                
                # Process image
                response = adapter.process_chat_image(user_id, image_path, 'line')
                
                # Send response
                line_bot.send_text_message(user_id, response['response_text'])
                
                # Send flex message for completion
                if response.get('action') == 'complete' and response.get('trust_badge_data'):
                    flex = create_line_trust_badge_flex(response['trust_badge_data'])
                    line_bot.send_flex_message(user_id, "Trust Badge", flex)

def create_line_trust_badge_flex(badge_data: dict) -> dict:
    """Create LINE Flex Message for Trust Badge"""
    trust_level = badge_data['trust_level']
    risk_score = badge_data['risk_score']
    limit = badge_data['transaction_limit']
    
    colors = {'bronze': '#CD7F32', 'silver': '#C0C0C0', 'gold': '#FFD700', 'platinum': '#E5E4E2'}
    emojis = {'bronze': '🥉', 'silver': '🥈', 'gold': '🥇', 'platinum': '💎'}
    
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🎉 ยืนยันตัวตนสำเร็จ",
                    "weight": "bold",
                    "size": "xl",
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "xl"
                },
                {
                    "type": "text",
                    "text": f"{emojis[trust_level]} {trust_level.upper()} BADGE",
                    "size": "xxl",
                    "weight": "bold",
                    "color": colors[trust_level],
                    "align": "center",
                    "margin": "xl"
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
                            "color": "#555555"
                        },
                        {
                            "type": "text",
                            "text": f"฿{limit:,}" if limit > 0 else "ไม่จำกัด",
                            "size": "sm",
                            "color": "#111111",
                            "align": "end"
                        }
                    ]
                }
            ]
        }
    }

# Messenger Webhook
@app.route('/webhook/messenger', methods=['GET', 'POST'])
def messenger_webhook():
    """Handle Messenger webhook events"""
    if request.method == 'GET':
        # Webhook verification
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        result = messenger_bot.verify_webhook(mode, token, challenge)
        if result:
            return result, 200
        return 'Forbidden', 403
    
    else:  # POST
        data = request.get_json()
        
        if data.get('object') == 'page':
            for entry in data.get('entry', []):
                for webhook_event in entry.get('messaging', []):
                    handle_messenger_event(webhook_event)
        
        return 'OK', 200

def handle_messenger_event(event: dict):
    """Handle single Messenger event"""
    sender_id = event['sender']['id']
    
    if event.get('message'):
        # Message event
        if event['message'].get('text'):
            # Text message
            text = event['message']['text']
            
            # Show typing
            messenger_bot.send_typing_on(sender_id)
            
            response = adapter.process_chat_message(sender_id, text, 'messenger')
            
            # Send response
            messenger_bot.send_text_message(sender_id, response['response_text'])
            
            # Send quick replies
            if response.get('quick_replies'):
                quick_replies = [
                    messenger_bot.create_quick_reply(q, q.upper())
                    for q in response['quick_replies']
                ]
                messenger_bot.send_text_message(
                    sender_id,
                    "เลือกหนึ่งตัวเลือก:",
                    quick_replies
                )
            
            # Send template for completion
            if response.get('action') == 'complete' and response.get('trust_badge_data'):
                send_messenger_trust_badge(sender_id, response['trust_badge_data'])
        
        elif event['message'].get('attachments'):
            # Image attachment
            attachments = event['message']['attachments']
            
            for attachment in attachments:
                if attachment['type'] == 'image':
                    image_url = attachment['payload']['url']
                    
                    # Download image
                    import requests
                    import uuid
                    
                    try:
                        img_response = requests.get(image_url, timeout=10)
                        image_path = f"/tmp/{sender_id}_{uuid.uuid4()}.jpg"
                        
                        with open(image_path, 'wb') as f:
                            f.write(img_response.content)
                        
                        # Show typing
                        messenger_bot.send_typing_on(sender_id)
                        
                        # Process image
                        response = adapter.process_chat_image(sender_id, image_path, 'messenger')
                        
                        # Send response
                        messenger_bot.send_text_message(sender_id, response['response_text'])
                        
                        # Send template for completion
                        if response.get('action') == 'complete' and response.get('trust_badge_data'):
                            send_messenger_trust_badge(sender_id, response['trust_badge_data'])
                    
                    except Exception as e:
                        messenger_bot.send_text_message(
                            sender_id,
                            "ขออภัย เกิดข้อผิดพลาดในการดาวน์โหลดรูปภาพ"
                        )
    
    elif event.get('postback'):
        # Postback event
        payload = event['postback']['payload']
        
        # Handle postback
        if payload == 'GET_STARTED':
            messenger_bot.send_text_message(
                sender_id,
                "ยินดีต้อนรับสู่ QuickChat ID! พิมพ์ 'พร้อม' เพื่อเริ่มยืนยันตัวตน"
            )

def send_messenger_trust_badge(recipient_id: str, badge_data: dict):
    """Send Trust Badge as Messenger template"""
    trust_level = badge_data['trust_level']
    risk_score = badge_data['risk_score']
    limit = badge_data['transaction_limit']
    
    emojis = {'bronze': '🥉', 'silver': '🥈', 'gold': '🥇', 'platinum': '💎'}
    
    elements = [{
        "title": f"{emojis[trust_level]} {trust_level.upper()} BADGE",
        "subtitle": f"Risk Score: {risk_score:.1f}/100\nวงเงิน: ฿{limit:,}" if limit > 0 else "ไม่จำกัด",
        "image_url": "https://via.placeholder.com/300x200/4285F4/FFFFFF?text=Trust+Badge"
    }]
    
    messenger_bot.send_generic_template(recipient_id, elements)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
