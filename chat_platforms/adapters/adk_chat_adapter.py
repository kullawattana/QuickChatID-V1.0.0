"""
ADK Chat Adapter
Converts ADK agent responses to chat platform messages
"""

from typing import Dict, List, Optional, Any
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class ADKChatAdapter:
    """
    Adapter to connect ADK agents with chat platforms.
    
    Converts:
    - Agent responses → Chat messages
    - Chat messages → Agent inputs
    - Images → Agent context
    """
    
    def __init__(self):
        """Initialize adapter"""
        self.sessions = {}
        self.current_agent = {}
    
    def process_chat_message(self,
                            user_id: str,
                            message: str,
                            platform: str = 'line') -> Dict:
        """
        Process message from chat platform.
        
        Args:
            user_id: User ID from platform
            message: Text message
            platform: 'line' or 'messenger'
            
        Returns:
            {
                'response_text': str,
                'quick_replies': List[str],
                'flex_message': Dict (LINE only),
                'template': Dict (Messenger only),
                'images': List[str],
                'action': str  # 'request_id', 'request_selfie', 'complete'
            }
        """
        # Get or create session
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                'step': 'welcome',
                'data': {},
                'history': []
            }
        
        session = self.sessions[user_id]
        session['history'].append({'user': message})
        
        # Route to appropriate agent based on step
        step = session['step']
        
        if step == 'welcome':
            response = self._handle_welcome(message, session)
        elif step == 'personal_info':
            response = self._handle_personal_info(message, session)
        elif step == 'document':
            response = self._handle_document_request(message, session)
        elif step == 'biometric':
            response = self._handle_biometric_request(message, session)
        else:
            response = {
                'response_text': 'ขออภัย เกิดข้อผิดพลาด กรุณาเริ่มใหม่',
                'action': 'restart'
            }
        
        session['history'].append({'agent': response['response_text']})
        self.sessions[user_id] = session
        
        return response
    
    def process_chat_image(self,
                          user_id: str,
                          image_path: str,
                          platform: str = 'line') -> Dict:
        """
        Process image from chat platform.
        
        Args:
            user_id: User ID
            image_path: Path to saved image
            platform: Platform name
            
        Returns:
            Response dict
        """
        session = self.sessions.get(user_id, {'step': 'welcome', 'data': {}})
        step = session['step']
        
        if step == 'document':
            return self._handle_document_image(image_path, session)
        elif step == 'biometric':
            return self._handle_biometric_image(image_path, session)
        else:
            return {
                'response_text': 'กรุณาส่งข้อความก่อนส่งรูปภาพ',
                'action': 'error'
            }
    
    def _handle_welcome(self, message: str, session: Dict) -> Dict:
        """Handle welcome agent"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['สวัสดี', 'hello', 'hi', 'เริ่ม', 'start']):
            session['step'] = 'welcome'
            return {
                'response_text': (
                    '🎉 ยินดีต้อนรับสู่ QuickChat ID\n\n'
                    'ยืนยันตัวตนได้ใน 5-7 วินาที ด้วยขั้นตอนง่ายๆ:\n'
                    '1️⃣ แชร์ข้อมูลพื้นฐาน\n'
                    '2️⃣ ถ่ายรูปบัตรประชาชน\n'
                    '3️⃣ ถ่าย Selfie\n'
                    '4️⃣ รับ Trust Badge\n\n'
                    '⚠️ ข้อมูลของคุณจะได้รับการคุ้มครองตาม PDPA'
                ),
                'quick_replies': ['พร้อม', 'ข้อมูลเพิ่มเติม'],
                'action': 'wait_consent'
            }
        
        elif any(word in message_lower for word in ['พร้อม', 'ready', 'ยืนยัน', 'ตกลง']):
            session['step'] = 'personal_info'
            return {
                'response_text': (
                    '✅ เริ่มต้นกระบวนการยืนยันตัวตน\n\n'
                    'กรุณาแชร์ข้อมูลพื้นฐาน:\n'
                    '📝 ชื่อ-นามสกุล:\n'
                    '📱 เบอร์โทรศัพท์:\n'
                    '📧 อีเมล (ถ้ามี):'
                ),
                'quick_replies': [],
                'action': 'collect_personal_info'
            }
        
        else:
            return {
                'response_text': 'พิมพ์ "พร้อม" เพื่อเริ่มยืนยันตัวตน',
                'quick_replies': ['พร้อม', 'ข้อมูลเพิ่มเติม'],
                'action': 'wait_consent'
            }
    
    def _handle_personal_info(self, message: str, session: Dict) -> Dict:
        """Handle personal info collection"""
        # Simple parsing (in production, use NER or structured input)
        lines = message.strip().split('\n')
        
        if len(lines) >= 2:
            # Extract info
            session['data']['name'] = lines[0] if len(lines) > 0 else ''
            session['data']['phone'] = lines[1] if len(lines) > 1 else ''
            session['data']['email'] = lines[2] if len(lines) > 2 else ''
            
            # Scam detection (simple check)
            from tools.scam_detection import detect_scam_intent
            scam_result = detect_scam_intent(message)
            
            if scam_result['scam_score'] > 0.7:
                return {
                    'response_text': (
                        '⚠️ ตรวจพบความเสี่ยง\n'
                        'ไม่สามารถดำเนินการต่อได้'
                    ),
                    'action': 'blocked'
                }
            
            session['step'] = 'document'
            return {
                'response_text': (
                    f'✅ ได้รับข้อมูลแล้ว\n\n'
                    f'📝 ชื่อ: {session["data"]["name"]}\n'
                    f'📱 เบอร์: {session["data"]["phone"]}\n\n'
                    f'ขั้นตอนถัดไป:\n'
                    f'📸 กรุณาถ่ายรูปบัตรประชาชน\n\n'
                    f'💡 Tips: วางบัตรบนพื้นเรียบ แสงสว่างเพียงพอ'
                ),
                'action': 'request_id_photo'
            }
        
        else:
            return {
                'response_text': (
                    'กรุณาส่งข้อมูลในรูปแบบ:\n'
                    'ชื่อ-นามสกุล\n'
                    'เบอร์โทรศัพท์\n'
                    'อีเมล (ถ้ามี)'
                ),
                'action': 'retry'
            }
    
    def _handle_document_request(self, message: str, session: Dict) -> Dict:
        """Handle waiting for ID card"""
        return {
            'response_text': '📸 กรุณาถ่ายรูปบัตรประชาชนของคุณ',
            'action': 'wait_id_photo'
        }
    
    def _handle_document_image(self, image_path: str, session: Dict) -> Dict:
        """Handle ID card image"""
        # Run OCR
        from tools.ocr_tool import extract_thai_id
        
        ocr_result = extract_thai_id(image_path, preprocess=True)
        
        if ocr_result['success'] and ocr_result['id_valid']:
            session['data']['id_card'] = ocr_result
            session['data']['id_card_image'] = image_path
            session['step'] = 'biometric'
            
            return {
                'response_text': (
                    f'✅ ตรวจสอบบัตรประชาชนสำเร็จ\n\n'
                    f'🆔 เลขบัตร: {ocr_result["id_number"][:4]}...{ocr_result["id_number"][-4:]}\n'
                    f'✓ ความมั่นใจ: {ocr_result["confidence_score"]:.0%}\n\n'
                    f'ขั้นตอนถัดไป:\n'
                    f'🤳 กรุณาถ่าย Selfie\n\n'
                    f'💡 Tips: มองตรงกล้อง ใบหน้าชัดเจน'
                ),
                'action': 'request_selfie'
            }
        else:
            return {
                'response_text': (
                    '❌ ไม่สามารถอ่านบัตรประชาชนได้\n'
                    'กรุณาถ่ายใหม่ให้ชัดเจน'
                ),
                'action': 'retry_id_photo'
            }
    
    def _handle_biometric_request(self, message: str, session: Dict) -> Dict:
        """Handle waiting for selfie"""
        return {
            'response_text': '🤳 กรุณาถ่าย Selfie ของคุณ',
            'action': 'wait_selfie'
        }
    
    def _handle_biometric_image(self, image_path: str, session: Dict) -> Dict:
        """Handle selfie image"""
        # Run face verification
        from tools.face_matching_tool import match_faces
        from tools.liveness_tool import detect_liveness
        from tools.deepfake_tool import detect_deepfake
        
        id_card_image = session['data'].get('id_card_image', '')
        
        if not id_card_image:
            return {
                'response_text': 'ไม่พบรูปบัตรประชาชน กรุณาเริ่มใหม่',
                'action': 'restart'
            }
        
        # Face matching
        face_result = match_faces(id_card_image, image_path)
        
        # Liveness
        liveness_result = detect_liveness(image_path)
        
        # Deepfake
        deepfake_result = detect_deepfake(image_path)
        
        # Calculate final score
        face_score = face_result['similarity_score'] if face_result['match'] else 0.0
        liveness_score = liveness_result['liveness_score'] if liveness_result['is_live'] else 0.0
        deepfake_score = 1.0 - deepfake_result['deepfake_probability']
        
        risk_score = (face_score * 0.4 + liveness_score * 0.3 + deepfake_score * 0.3) * 100
        
        # Determine trust level
        if risk_score >= 96:
            trust_level = 'platinum'
        elif risk_score >= 81:
            trust_level = 'gold'
        elif risk_score >= 61:
            trust_level = 'silver'
        else:
            trust_level = 'bronze'
        
        # Issue trust badge
        from tools.trust_badge_tool import issue_trust_badge
        badge = issue_trust_badge(trust_level, risk_score, session['data'])
        
        session['data']['verification'] = {
            'face_score': face_score,
            'liveness_score': liveness_score,
            'deepfake_score': deepfake_score,
            'risk_score': risk_score,
            'trust_level': trust_level,
            'badge': badge
        }
        session['step'] = 'complete'
        
        badge_emoji = {'bronze': '🥉', 'silver': '🥈', 'gold': '🥇', 'platinum': '💎'}
        
        return {
            'response_text': (
                f'🎉 ยืนยันตัวตนสำเร็จ!\n\n'
                f'{badge_emoji[trust_level]} Trust Badge: {trust_level.upper()}\n'
                f'📊 Risk Score: {risk_score:.1f}/100\n\n'
                f'✅ Face Match: {face_score:.0%}\n'
                f'✅ Liveness: {liveness_score:.0%}\n'
                f'✅ Deepfake Check: {deepfake_score:.0%}\n\n'
                f'💰 วงเงินธุรกรรม: ฿{badge["transaction_limit"]:,}\n\n'
                f'🔐 JWT Token:\n{badge["jwt_token"][:50]}...'
            ),
            'action': 'complete',
            'trust_badge_data': {
                'trust_level': trust_level,
                'risk_score': risk_score,
                'transaction_limit': badge['transaction_limit']
            }
        }
    
    def get_session(self, user_id: str) -> Optional[Dict]:
        """Get user session"""
        return self.sessions.get(user_id)
    
    def clear_session(self, user_id: str):
        """Clear user session"""
        if user_id in self.sessions:
            del self.sessions[user_id]


# Singleton
_adk_chat_adapter = None

def get_adk_chat_adapter():
    """Get singleton instance"""
    global _adk_chat_adapter
    if _adk_chat_adapter is None:
        _adk_chat_adapter = ADKChatAdapter()
    return _adk_chat_adapter
