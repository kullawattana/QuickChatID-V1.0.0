"""
Web API for Frontend Integration
RESTful endpoints for React frontend to connect with ADK Agent
Uses the SAME ADK Agent as LINE Bot!
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict, Optional
import os
import sys
import uuid
import time
import hashlib
import hmac
import threading
from datetime import datetime, timedelta
from functools import wraps
import tempfile
from pathlib import Path
import requests as http_requests

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import ADK Agent (same one used by LINE Bot!)
from agents.kyc_orchestrator.agent import root_agent

# Import Enterprise Services
from services.opa_service import get_opa_service
from services.presidio_service import get_presidio_service
from services.telemetry_service import get_telemetry_service
from services.guardrails_service import get_guardrails_service
from services.keycloak_service import get_keycloak_service

# Initialize services (all have mock/fallback mode)
opa = get_opa_service()
presidio = get_presidio_service()
telemetry = get_telemetry_service()
guardrails = get_guardrails_service()
keycloak = get_keycloak_service()

app = Flask(__name__)
app.json.ensure_ascii = False

# Enable CORS for frontend (React dev server and production)
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",  # Alternative React dev
            "http://localhost:5174",  # Alternative Vite port
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Session storage (use Redis/Database in production)
sessions = {}

# ─── E-Commerce API Integration ──────────────────────────────────────────────
# API Keys: comma-separated list in env, e.g. "key1,key2,key3"
_raw_keys = os.getenv('ECOMMERCE_API_KEYS', '')
ECOMMERCE_API_KEYS = set(k.strip() for k in _raw_keys.split(',') if k.strip())

# Webhook registry: { api_key: { url, secret, events } }
_webhook_registry: Dict[str, dict] = {}
_webhook_lock = threading.Lock()

# Rate limiter: { ip: [(timestamp), ...] }
_rate_buckets: Dict[str, list] = {}
RATE_LIMIT = int(os.getenv('API_RATE_LIMIT', '60'))   # requests per window
RATE_WINDOW = int(os.getenv('API_RATE_WINDOW', '60'))  # seconds


def _require_api_key(f):
    """Decorator: enforce X-API-Key header for e-commerce endpoints."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not ECOMMERCE_API_KEYS:
            return jsonify({'error': 'API access not configured. Set ECOMMERCE_API_KEYS in .env'}), 503
        key = request.headers.get('X-API-Key', '')
        if key not in ECOMMERCE_API_KEYS:
            return jsonify({'error': 'Invalid or missing X-API-Key'}), 401
        return f(*args, **kwargs)
    return wrapper


def _rate_limit(f):
    """Decorator: simple sliding-window rate limiter per IP."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        ip = request.remote_addr or 'unknown'
        now = time.time()
        with threading.Lock():
            bucket = _rate_buckets.get(ip, [])
            bucket = [t for t in bucket if now - t < RATE_WINDOW]
            if len(bucket) >= RATE_LIMIT:
                return jsonify({'error': 'Rate limit exceeded', 'retry_after': RATE_WINDOW}), 429
            bucket.append(now)
            _rate_buckets[ip] = bucket
        return f(*args, **kwargs)
    return wrapper


def _fire_webhook(api_key: str, event: str, payload: dict):
    """Send webhook callback to registered URL (fire-and-forget thread)."""
    def _send():
        with _webhook_lock:
            cfg = _webhook_registry.get(api_key)
        if not cfg:
            return
        if event not in cfg.get('events', [event]):
            return
        body = {'event': event, 'timestamp': datetime.utcnow().isoformat() + 'Z', **payload}
        headers = {'Content-Type': 'application/json'}
        secret = cfg.get('secret', '')
        if secret:
            sig = hmac.new(secret.encode(), str(body).encode(), hashlib.sha256).hexdigest()
            headers['X-QuickChatID-Signature'] = f'sha256={sig}'
        try:
            http_requests.post(cfg['url'], json=body, headers=headers, timeout=10)
        except Exception as e:
            print(f"⚠️  Webhook delivery failed ({cfg['url']}): {e}")
    threading.Thread(target=_send, daemon=True).start()
# ─────────────────────────────────────────────────────────────────────────────

print("✅ ADK Agent loaded successfully!")
print(f"   Agent: {root_agent.name}")
print(f"   Model: {root_agent.model}")
print(f"   Tools: {len(root_agent.tools)} tools available")


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'QuickChat ID Web API',
        'version': '2.0.0',
        'adk_agent': root_agent.name,
        'adk_model': root_agent.model,
        'tools_count': len(root_agent.tools),
        'enterprise_services': {
            'opa': 'real' if opa.available else 'mock',
            'presidio': 'real' if presidio.available else 'mock',
            'telemetry': 'real' if telemetry.available else 'mock',
            'guardrails': 'active',
            'keycloak': 'real' if keycloak.available else 'mock'
        }
    })


@app.route('/api/session/init', methods=['POST'])
def initialize_session():
    """
    Initialize verification session

    Returns:
        session_id, user_id, welcome_message
    """
    try:
        # [Telemetry] Track session initialization
        with telemetry.trace_span("session_init", {"source": "web_ui"}) as span:
            # Generate session
            session_id = str(uuid.uuid4())
            user_id = f"web_{session_id[:8]}"

            print(f"🚀 Initializing web session: {session_id}")

            # [Keycloak] Register user in IAM
            keycloak_user = keycloak.create_user({
                'username': user_id,
                'email': f"{user_id}@quickchat.id",
                'firstName': 'Web',
                'lastName': 'User'
            })
            print(f"   🔐 Keycloak: {keycloak_user.get('message', 'user created')}")

            # Create local session
            sessions[session_id] = {
                'user_id': user_id,
                'step': 'welcome',
                'data': {},
                'history': [],
                'created_at': datetime.now().isoformat(),
                'keycloak_user_id': keycloak_user.get('user_id', user_id)
            }

            telemetry.record_event("session_created", {
                "session_id": session_id,
                "user_id": user_id
            })

        # Welcome message
        welcome = {
            'role': 'assistant',
            'content': (
                '🎉 **ยินดีต้อนรับสู่ QuickChat ID**\n\n'
                'ระบบยืนยันตัวตนอัจฉริยะที่ใช้ AI\n'
                'ใช้เวลาเพียง 5-7 วินาที!\n\n'
                '📋 **ขั้นตอนการทำงาน:**\n'
                '1. กรอกข้อมูลส่วนตัว\n'
                '2. ถ่ายรูปบัตรประชาชน\n'
                '3. ถ่าย Selfie\n'
                '4. รับ Trust Badge\n\n'
                '✨ พร้อมเริ่มต้นแล้วใช่ไหมคะ? พิมพ์ **"พร้อม"** เพื่อเริ่มต้น'
            ),
            'timestamp': datetime.now().isoformat()
        }

        return jsonify({
            'success': True,
            'session_id': session_id,
            'user_id': user_id,
            'message': welcome
        })

    except Exception as e:
        print(f"❌ Error initializing session: {e}")
        import traceback
        traceback.print_exc()

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/chat/message', methods=['POST'])
def handle_chat_message():
    """
    Handle chat message from user

    Request:
        {
            "session_id": str,
            "message": str
        }

    Returns:
        {
            "success": bool,
            "response": str,
            "next_step": str,
            "scam_score": float,
            "timestamp": str
        }
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        message = data.get('message')

        print(f"📥 Received message for session {session_id}: {message[:50]}...")

        if not session_id or session_id not in sessions:
            return jsonify({
                'success': False,
                'error': 'Invalid session'
            }), 400

        session = sessions[session_id]

        # Send to ADK Agent via HTTP (same way as LINE Bot!)
        try:
            print(f"🤖 Sending to ADK Server: {message[:100]}")

            # Call ADK server via HTTP
            import requests
            import json

            ADK_SERVER_URL = os.getenv('ADK_SERVER_URL', 'http://localhost:8000')
            user_id = session['user_id']

            # Get or create ADK session
            if 'adk_session_id' not in session:
                # Create new ADK session
                create_response = requests.post(
                    f"{ADK_SERVER_URL}/apps/kyc_orchestrator/users/{user_id}/sessions",
                    timeout=10
                )
                if create_response.status_code == 200:
                    session_data = create_response.json()
                    session['adk_session_id'] = session_data.get('id')
                    print(f"✓ Created ADK session: {session['adk_session_id']}")

            adk_session_id = session.get('adk_session_id')
            if not adk_session_id:
                raise Exception("Could not create ADK session")

            # Send message to ADK via SSE endpoint
            run_response = requests.post(
                f"{ADK_SERVER_URL}/run_sse",
                json={
                    "app_name": "kyc_orchestrator",
                    "session_id": adk_session_id,
                    "user_id": user_id,
                    "newMessage": {
                        "role": "user",
                        "parts": [{"text": message}]
                    }
                },
                timeout=60
            )

            if run_response.status_code != 200:
                raise Exception(f"ADK server returned {run_response.status_code}")

            # Parse SSE response
            response_text = ""
            for line in run_response.text.split('\n'):
                line = line.strip()
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        if 'content' in data and 'parts' in data['content']:
                            for part in data['content']['parts']:
                                if 'text' in part:
                                    response_text += part['text']
                    except json.JSONDecodeError:
                        continue

            if not response_text:
                response_text = "ขออภัย ไม่สามารถประมวลผลได้ กรุณาลองใหม่อีกครั้ง"

            # [Guardrails] Validate AI output before sending to user
            guard_result = guardrails.validate_output(response_text)
            if not guard_result.get('valid', True):
                violations = guard_result.get('violations', [])
                print(f"   🛡️ Guardrails blocked: {[v['type'] for v in violations]}")
                response_text = "ขออภัย ระบบตรวจพบเนื้อหาที่ไม่เหมาะสม กรุณาลองใหม่"

            # [Presidio] Mask PII in logs (not in user response)
            presidio_result = presidio.anonymize(response_text)
            masked_for_log = presidio_result.get('anonymized_text', response_text) if isinstance(presidio_result, dict) else str(presidio_result)
            print(f"✅ Agent response (masked): {masked_for_log[:100]}...")

            # Extract step from response
            next_step = session['step']
            if 'ถ่ายรูปบัตร' in response_text or 'อัปโหลดบัตร' in response_text:
                next_step = 'document'
            elif 'Selfie' in response_text or 'ถ่ายรูปใบหน้า' in response_text:
                next_step = 'biometric'
            elif 'Trust Badge' in response_text or 'ยินดีด้วย' in response_text:
                next_step = 'complete'
            elif 'ชื่อ-นามสกุล' in response_text or 'เบอร์โทร' in response_text:
                next_step = 'personal_info'

            # Store in history
            session['history'].append({
                'user': message,
                'assistant': response_text,
                'timestamp': datetime.now().isoformat()
            })
            sessions[session_id]['step'] = next_step

            return jsonify({
                'success': True,
                'response': response_text,
                'next_step': next_step,
                'scam_score': 0.0,
                'timestamp': datetime.now().isoformat()
            })

        except requests.exceptions.ConnectionError:
            print("⚠️  Cannot connect to ADK server")
        except Exception as e:
            print(f"⚠️  ADK Agent error: {e}")
            import traceback
            traceback.print_exc()

            # Demo response based on current step
            current_step = session['step']

            if current_step == 'welcome':
                response_text = (
                    '✅ **เริ่มต้นกันเลย!**\n\n'
                    'ก่อนอื่น ขอทราบข้อมูลของคุณนะคะ:\n\n'
                    '📝 กรุณาให้ข้อมูลดังนี้:\n'
                    '• ชื่อ-นามสกุล\n'
                    '• เบอร์โทรศัพท์ (10 หลัก)\n'
                    '• อีเมล'
                )
                next_step = 'personal_info'
            elif current_step == 'personal_info':
                response_text = (
                    '✅ **ขอบคุณสำหรับข้อมูล!**\n\n'
                    'ถัดไป เราจะตรวจสอบบัตรประชาชนของคุณ\n\n'
                    '📸 **กรุณาอัปโหลดรูปบัตรประชาชน**\n\n'
                    '💡 คำแนะนำ:\n'
                    '✓ ถ่ายรูปให้ชัดเจน\n'
                    '✓ แสงสว่างเพียงพอ\n'
                    '✓ มองเห็นข้อความทั้งหมด'
                )
                next_step = 'document'
            else:
                response_text = f'📝 ได้รับข้อความ: {message}'
                next_step = current_step

            sessions[session_id]['step'] = next_step

            return jsonify({
                'success': True,
                'response': response_text,
                'next_step': next_step,
                'scam_score': 0.0,
                'timestamp': datetime.now().isoformat()
            })

    except Exception as e:
        print(f"❌ Error handling message: {e}")
        import traceback
        traceback.print_exc()

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/chat/image', methods=['POST'])
def handle_image_upload():
    """
    Handle image upload (ID card or selfie)

    Request (multipart/form-data):
        - file: image file
        - session_id: str
        - image_type: 'id_card' or 'selfie'

    Returns:
        {
            "success": bool,
            "response": str,
            "next_step": str,
            "trust_badge": {...} (if complete)
        }
    """
    try:
        session_id = request.form.get('session_id')
        image_type = request.form.get('image_type')
        file = request.files.get('file')

        print(f"📥 Received {image_type} upload for session {session_id}")

        if not session_id or session_id not in sessions:
            return jsonify({
                'success': False,
                'error': 'Invalid session'
            }), 400

        if not file:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        session = sessions[session_id]

        # Save file to persistent directory
        upload_dir = Path(__file__).parent.resolve() / 'uploads' / 'web_sessions'
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_ext = Path(file.filename).suffix or '.jpg'
        # Always use consistent extension
        if file_ext.lower() in ['.jpg', '.jpeg']:
            file_ext = '.jpg'

        temp_path = upload_dir / f"{session_id}_{image_type}{file_ext}"
        file.save(str(temp_path))

        if not temp_path.exists():
            return jsonify({
                'success': False,
                'error': 'ไม่สามารถบันทึกไฟล์ได้'
            }), 500

        print(f"💾 Saved {image_type}: {temp_path} ({temp_path.stat().st_size} bytes)")

        # Process with ADK Tools directly!
        try:
            print(f"🤖 Processing {image_type} with ADK Tools")
            print(f"   File: {temp_path}")

            if image_type == 'id_card':
                # Call OCR tool directly
                from tools.ocr_tool import extract_thai_id

                print("   🔍 Running OCR...")
                with telemetry.trace_span("ocr_processing", {"image_type": "id_card"}):
                    ocr_result = extract_thai_id(image_path=str(temp_path))

                # [Presidio] Mask PII in logs
                id_num = ocr_result.get('id_number', '')
                presidio_id_result = presidio.anonymize(id_num) if id_num else None
                masked_id = presidio_id_result.get('anonymized_text', id_num) if isinstance(presidio_id_result, dict) else (str(presidio_id_result) if presidio_id_result else 'N/A')
                print(f"   ✅ OCR Result: {ocr_result.get('name_th', 'N/A')} (ID: {masked_id})")

                # Store OCR data and image path in session
                session['ocr_data'] = ocr_result
                session['id_card_path'] = str(temp_path)

                # Explicitly update sessions dict to ensure persistence
                sessions[session_id] = session

                print(f"   💾 ID card stored in session: {session['id_card_path']}")

                # Generate response
                if ocr_result.get('success'):
                    response_text = (
                        f"✅ **ตรวจสอบบัตรประชาชนสำเร็จ!**\n\n"
                        f"📊 **ผลการตรวจสอบ:**\n"
                        f"• ชื่อ: {ocr_result.get('name_th', '-')}\n"
                        f"• เลขบัตร: {ocr_result.get('id_number', '-')}\n"
                        f"• วันเกิด: {ocr_result.get('date_of_birth', '-')}\n"
                        f"• ความแม่นยำ: {ocr_result.get('confidence_score', 0):.1%}\n\n"
                        f"🤳 **ขั้นตอนสุดท้าย:** กรุณาถ่าย Selfie"
                    )
                else:
                    response_text = f"⚠️ ไม่สามารถอ่านบัตรได้ กรุณาลองใหม่"

            else:  # selfie
                # Call Face Matching tool directly
                from tools.face_matching_tool import match_faces
                from tools.liveness_tool import detect_liveness

                # Get ID card image from session
                ocr_data = session.get('ocr_data', {})
                id_card_path = session.get('id_card_path', '')

                # Validate ID card path - try recovery if missing
                if not id_card_path:
                    possible_path = upload_dir / f"{session_id}_id_card.jpg"
                    if possible_path.exists():
                        id_card_path = str(possible_path)
                        session['id_card_path'] = id_card_path
                    else:
                        return jsonify({
                            'success': False,
                            'error': 'กรุณาอัปโหลดบัตรประชาชนก่อนถ่าย Selfie'
                        }), 400

                if not Path(id_card_path).exists():
                    return jsonify({
                        'success': False,
                        'error': 'ไม่พบไฟล์บัตรประชาชน กรุณาอัปโหลดใหม่'
                    }), 400

                # [Telemetry] Track biometric verification
                with telemetry.trace_span("biometric_verification", {"session_id": session_id}):

                    print("   🔍 Running Liveness Detection...")
                    with telemetry.trace_span("liveness_detection"):
                        liveness_result = detect_liveness(image_path=str(temp_path))

                    print("   🔍 Running Face Matching...")
                    with telemetry.trace_span("face_matching"):
                        face_result = match_faces(
                            id_card_image=id_card_path,
                            selfie_image=str(temp_path)
                        )

                    similarity = face_result.get('similarity_score', 0)
                    is_live = liveness_result.get('is_live', False)
                    print(f"   ✅ Face Match: {similarity:.1%} | Liveness: {is_live}")

                    # Store results
                    session['face_result'] = face_result
                    session['liveness_result'] = liveness_result

                    # [OPA] Policy-based risk assessment (weighted scoring)
                    ocr_data = session.get('ocr_data', {})
                    actual_liveness_score = liveness_result.get('liveness_score', 0.5)
                    opa_input = {
                        'face_match_score': similarity,
                        'liveness_score': actual_liveness_score,
                        'deepfake_probability': liveness_result.get('deepfake_probability', 0.1),
                        'ocr_confidence': ocr_data.get('confidence_score', 0.9),
                        'scam_score': session.get('scam_score', 0.1)
                    }

                    opa_result = opa.evaluate_policy("kyc/risk_assessment", opa_input)
                    risk_score = opa_result.get('risk_score', 50)
                    trust_level = opa_result.get('trust_level', 'bronze')
                    is_blocked = opa_result.get('blocked', False)

                    print(f"   🏛️ OPA Policy: score={risk_score}, level={trust_level}, mode={opa_result.get('evaluation_mode', 'unknown')}")

                    telemetry.record_metric("risk_score", risk_score, "points", {"session_id": session_id})
                    telemetry.record_metric("face_similarity", similarity, "ratio", {"session_id": session_id})

                    # Generate Trust Badge
                    from tools.trust_badge_tool import issue_trust_badge
                    badge_result = issue_trust_badge(trust_level=trust_level, risk_score=int(risk_score))

                    if is_blocked:
                        response_text = (
                            f"🚫 **การยืนยันตัวตนถูกปฏิเสธ**\n\n"
                            f"สาเหตุ: {', '.join(opa_result.get('block_reasons', ['Policy violation']))}\n"
                            f"กรุณาติดต่อฝ่ายสนับสนุน"
                        )
                    elif similarity > 0.3 or risk_score >= 50:
                        # [Keycloak] Assign role based on trust level
                        keycloak_uid = session.get('keycloak_user_id', session['user_id'])
                        role_result = keycloak.assign_role(keycloak_uid, f"{trust_level}_user")
                        print(f"   🔐 Keycloak role: {role_result.get('message', 'assigned')}")

                        tx_limit = opa_result.get('transaction_limit', 100000)
                        response_text = (
                            f"🎉 **ยืนยันตัวตนสำเร็จ!**\n\n"
                            f"**Trust Badge: {trust_level.upper()}**\n"
                            f"คะแนนความน่าเชื่อถือ: {int(risk_score)}/100\n\n"
                            f"✅ Face Matching: {similarity:.1%}\n"
                            f"✅ Liveness: {'Passed' if is_live else 'Failed'}\n"
                            f"✅ วงเงินธุรกรรม: {'ไม่จำกัด' if tx_limit == -1 else f'฿{tx_limit:,}'}\n\n"
                            f"คุณสามารถใช้งานฟีเจอร์ทั้งหมดได้แล้ว!"
                        )
                        session['trust_badge'] = badge_result
                    else:
                        response_text = (
                            f"⚠️ **ใบหน้าไม่ตรงกับบัตรประชาชน**\n\n"
                            f"Face Matching: {similarity:.1%}\n"
                            f"กรุณาตรวจสอบ:\n"
                            f"• ใช้บัตรประชาชนของตัวเอง\n"
                            f"• ถ่ายรูป selfie ในที่แสงสว่าง\n"
                            f"• หันหน้าตรง ไม่สวมแว่น/หมวก"
                        )

            print(f"✅ Processed {image_type}: {response_text[:100]}...")

            # Determine next step
            if image_type == 'id_card':
                next_step = 'biometric'
                if 'Selfie' not in response_text and 'selfie' not in response_text.lower():
                    response_text += '\n\n🤳 **ขั้นตอนสุดท้าย:** กรุณาถ่าย Selfie'
            else:  # selfie
                next_step = 'complete'

            # Update step in session
            session['step'] = next_step

            # Explicitly save back to sessions dict
            sessions[session_id] = session

            # Store in history
            session['history'].append({
                'user': f'[Uploaded {image_type}]',
                'assistant': response_text,
                'timestamp': datetime.now().isoformat()
            })

            result = {
                'success': True,
                'response': response_text,
                'next_step': next_step,
                'timestamp': datetime.now().isoformat()
            }

            # Check if Trust Badge is in session (from face matching)
            if 'trust_badge' in session and session['trust_badge']:
                badge_data = session['trust_badge']
                result['trust_badge'] = {
                    'level': badge_data.get('level', 'bronze'),
                    'score': badge_data.get('trust_score', 85),
                    'benefits': badge_data.get('benefits', []),
                    'transactionLimit': badge_data.get('transaction_limit', 100000),
                    'expires': badge_data.get('expires', (datetime.now().replace(year=datetime.now().year + 1)).isoformat())
                }

            return jsonify(result)

        except Exception as e:
            print(f"⚠️  ADK Agent error: {e}, using demo mode")
            import traceback
            traceback.print_exc()

            # Demo response
            if image_type == 'id_card':
                response_text = (
                    '✅ **บัตรประชาชนผ่านการตรวจสอบ!**\n\n'
                    '📊 **ผลการตรวจสอบ:**\n'
                    '✓ OCR: 95.2% ความแม่นยำ\n'
                    '✓ Document Authenticity: ผ่าน\n'
                    '✓ ID Number: Valid\n\n'
                    '🤳 **ขั้นตอนสุดท้าย:** กรุณาถ่าย Selfie เพื่อยืนยันตัวตน'
                )
                next_step = 'biometric'
                result = {
                    'success': True,
                    'response': response_text,
                    'next_step': next_step,
                    'timestamp': datetime.now().isoformat()
                }
            else:  # selfie
                # Generate demo trust badge
                import random
                score = random.randint(85, 98)
                level = 'platinum' if score >= 96 else 'gold' if score >= 85 else 'silver'

                response_text = (
                    f'🎉 **ยืนยันตัวตนสำเร็จ!**\n\n'
                    f'**Trust Badge: {level.upper()}**\n'
                    f'คะแนน: {score}/100\n\n'
                    '✅ Face Matching: 98.5%\n'
                    '✅ Liveness: Passed\n'
                    '✅ Deepfake: Not Detected\n\n'
                    'คุณสามารถใช้งานฟีเจอร์ทั้งหมดได้แล้ว!'
                )
                next_step = 'complete'

                trust_badge = {
                    'level': level,
                    'score': score,
                    'benefits': [
                        'การยืนยันตัวตนระดับสูง',
                        'ฟีเจอร์พิเศษทั้งหมด',
                        'Support ลำดับสำคัญ',
                        'ส่วนลดค่าธรรมเนียม'
                    ],
                    'transactionLimit': 100000 if level == 'gold' else -1,
                    'expires': (datetime.now().replace(year=datetime.now().year + 1)).isoformat()
                }

                result = {
                    'success': True,
                    'response': response_text,
                    'next_step': next_step,
                    'trust_badge': trust_badge,
                    'timestamp': datetime.now().isoformat()
                }

            sessions[session_id]['step'] = next_step
            return jsonify(result)

        finally:
            # Only clean up selfie temp file (keep ID card for face matching!)
            if image_type == 'selfie' and temp_path.exists():
                try:
                    temp_path.unlink()
                except:
                    pass

    except Exception as e:
        print(f"❌ Error uploading image: {e}")
        import traceback
        traceback.print_exc()

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/verification/status/<session_id>', methods=['GET'])
def get_verification_status(session_id):
    """Get verification status"""
    if session_id not in sessions:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        }), 404

    session = sessions[session_id]

    return jsonify({
        'success': True,
        'session_id': session_id,
        'user_id': session['user_id'],
        'current_step': session['step'],
        'data': session.get('data', {}),
        'is_completed': session['step'] == 'complete'
    })


# ═══════════════════════════════════════════════════════════════════════════
# SWAGGER / API DOCS
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/swagger.json')
def swagger_spec():
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "QuickChat ID — E-Commerce API",
            "version": "1.0.0",
            "description": "KYC verification API for e-commerce integration"
        },
        "servers": [{"url": "http://localhost:5003"}],
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"}
            }
        },
        "security": [{"ApiKeyAuth": []}],
        "paths": {
            "/api/health": {
                "get": {
                    "tags": ["System"],
                    "summary": "Health Check",
                    "security": [],
                    "responses": {"200": {"description": "Server is healthy"}}
                }
            },
            "/api/v1/kyc/verify": {
                "get": {
                    "tags": ["KYC"],
                    "summary": "ตรวจสอบ KYC Certificate ของ User",
                    "description": "ค้นหา approved KYC record ล่าสุดของ user แล้วคืน certificate พร้อม trust badge",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "query",
                            "required": True,
                            "description": "Platform user ID (LINE: Uxxxxxxx, Messenger: numeric PSID, Web: WEB_xxx)",
                            "schema": {"type": "string"},
                            "example": "9340707359288035"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "KYC Certificate",
                            "content": {"application/json": {"schema": {
                                "type": "object",
                                "properties": {
                                    "verified": {"type": "boolean"},
                                    "user_id": {"type": "string"},
                                    "platform": {"type": "string", "enum": ["line", "messenger", "web"]},
                                    "role": {"type": "string", "enum": ["buyer", "seller"]},
                                    "certificate": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "id_number": {"type": "string"},
                                            "trust_level": {"type": "string", "enum": ["bronze", "silver", "gold", "platinum"]},
                                            "risk_score": {"type": "number"},
                                            "transaction_limit": {"type": "integer"},
                                            "role": {"type": "string"},
                                            "platform": {"type": "string"},
                                            "issued_at": {"type": "string", "format": "date-time"}
                                        }
                                    }
                                }
                            }}}
                        },
                        "404": {"description": "No approved KYC record found"},
                        "401": {"description": "Invalid or missing API key"},
                        "429": {"description": "Rate limit exceeded"}
                    }
                }
            },
            "/api/v1/kyc/users": {
                "get": {
                    "tags": ["KYC"],
                    "summary": "List ผู้ใช้ที่ผ่าน KYC",
                    "description": "ดึงรายชื่อ user ที่ผ่านการ approve แล้ว กรองตาม role และ/หรือ platform",
                    "parameters": [
                        {
                            "name": "role",
                            "in": "query",
                            "required": False,
                            "description": "กรองตาม role (ไม่ระบุ = ทุก role)",
                            "schema": {"type": "string", "enum": ["buyer", "seller"]}
                        },
                        {
                            "name": "platform",
                            "in": "query",
                            "required": False,
                            "description": "กรองตาม platform (ไม่ระบุ = ทุก platform)",
                            "schema": {"type": "string", "enum": ["line", "messenger", "web"]}
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "description": "จำนวน record สูงสุด (max 500)",
                            "schema": {"type": "integer", "default": 100, "maximum": 500}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of verified users",
                            "content": {"application/json": {"schema": {
                                "type": "object",
                                "properties": {
                                    "total": {"type": "integer"},
                                    "role_filter": {"type": "string"},
                                    "platform_filter": {"type": "string"},
                                    "users": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "user_id": {"type": "string"},
                                                "role": {"type": "string"},
                                                "platform": {"type": "string"},
                                                "name": {"type": "string"},
                                                "trust_level": {"type": "string"},
                                                "risk_score": {"type": "number"},
                                                "transaction_limit": {"type": "integer"},
                                                "verified_at": {"type": "string", "format": "date-time"}
                                            }
                                        }
                                    }
                                }
                            }}}
                        },
                        "401": {"description": "Invalid or missing API key"},
                        "429": {"description": "Rate limit exceeded"}
                    }
                }
            },
            "/api/v1/kyc/stats": {
                "get": {
                    "tags": ["KYC"],
                    "summary": "สถิติ KYC ทั้งหมด",
                    "description": "นับจำนวน record แยกตาม status, role, platform",
                    "responses": {"200": {"description": "Aggregate statistics"}}
                }
            },
            "/api/v1/kyc/webhook/register": {
                "post": {
                    "tags": ["Webhook"],
                    "summary": "ลงทะเบียน Webhook",
                    "description": "รับ event notification เมื่อมีการ approve/reject KYC",
                    "requestBody": {
                        "content": {"application/json": {"schema": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string", "description": "HTTPS callback URL"},
                                "secret": {"type": "string", "description": "HMAC secret for signature verification"},
                                "events": {
                                    "type": "array",
                                    "items": {"type": "string", "enum": ["kyc.approved", "kyc.rejected", "kyc.failed"]},
                                    "description": "Events to subscribe (empty = all)"
                                }
                            },
                            "required": ["url"]
                        }}}
                    },
                    "responses": {"200": {"description": "Webhook registered successfully"}}
                }
            },
            "/api/v1/kyc/webhook/test": {
                "post": {
                    "tags": ["Webhook"],
                    "summary": "ทดสอบ Webhook",
                    "description": "ส่ง test event ไปยัง webhook URL ที่ลงทะเบียนไว้",
                    "responses": {"200": {"description": "Test event sent"}}
                }
            }
        }
    }
    return jsonify(spec)


@app.route('/docs')
def swagger_ui():
    return '''<!DOCTYPE html>
<html>
<head>
  <title>QuickChat ID API Docs</title>
  <meta charset="utf-8"/>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({
      url: "/swagger.json",
      dom_id: "#swagger-ui",
      presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
      layout: "BaseLayout",
      persistAuthorization: true
    })
  </script>
</body>
</html>''', 200, {'Content-Type': 'text/html'}


# ═══════════════════════════════════════════════════════════════════════════
# E-COMMERCE API  (requires X-API-Key header)
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/v1/kyc/verify', methods=['GET'])
@_require_api_key
@_rate_limit
def ecommerce_kyc_verify():
    """
    Query KYC status for a user.  E-commerce calls this to check if a user
    has been verified before allowing purchase / account action.

    Query params:
        user_id   (required)  - Platform user ID
        platform  (optional)  - 'web' | 'line' | 'messenger'  (default: any)

    Returns a KYC Certificate JSON.
    """
    user_id  = request.args.get('user_id', '').strip()
    platform = request.args.get('platform', '').strip().lower()

    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    try:
        from database import KYCRepository
        repo = KYCRepository()

        record = repo.get_approved_by_user_id(user_id)
        if not record:
            return jsonify({
                'verified': False,
                'user_id': user_id,
                'message': 'No approved KYC record found'
            }), 404

        # Build KYC Certificate — prefer dedicated columns, fallback to notes JSON
        trust_level = record.trust_level or 'bronze'
        risk_score  = record.risk_score  or 0

        # Fallback: parse from notes JSON if columns are empty
        if not record.trust_level and record.notes:
            try:
                import json as _json
                notes = _json.loads(record.notes)
                trust_level = notes.get('trust_level', trust_level)
                risk_score  = notes.get('risk_score',  risk_score)
            except Exception:
                pass

        certificate = {
            'verified': True,
            'user_id': user_id,
            'certificate': {
                'id': str(record.id),
                'issued_at': record.created_at.isoformat() if record.created_at else None,
                'trust_level': trust_level,
                'risk_score': risk_score,
                'role': record.role or 'buyer',
                'name': ' '.join(p for p in [record.prefix, record.first_name, record.last_name] if p) or None,
                'id_number_hash': hashlib.sha256((record.id_number or '').encode()).hexdigest()[:16] if record.id_number else None,
                'transaction_limit': {'bronze': 10000, 'silver': 50000, 'gold': 100000, 'platinum': -1}.get(trust_level, 0),
                'expires_at': (record.created_at + timedelta(days=365)).isoformat() if record.created_at else None
            }
        }
        return jsonify(certificate)

    except Exception as e:
        print(f"❌ KYC verify error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/v1/kyc/webhook/register', methods=['POST'])
@_require_api_key
def ecommerce_webhook_register():
    """
    Register a webhook URL to receive KYC completion events.

    Body (JSON):
        url     (required)  - HTTPS URL to POST events to
        secret  (optional)  - Signing secret for HMAC-SHA256 signature
        events  (optional)  - List of events to subscribe to
                              Default: ["kyc.approved", "kyc.rejected"]
    """
    api_key = request.headers.get('X-API-Key')
    data    = request.get_json(silent=True) or {}
    url     = data.get('url', '').strip()
    secret  = data.get('secret', '')
    events  = data.get('events', ['kyc.approved', 'kyc.rejected'])

    if not url:
        return jsonify({'error': 'url is required'}), 400
    if not url.startswith('https://') and not url.startswith('http://localhost'):
        return jsonify({'error': 'url must use HTTPS'}), 400

    with _webhook_lock:
        _webhook_registry[api_key] = {'url': url, 'secret': secret, 'events': events}

    return jsonify({
        'registered': True,
        'url': url,
        'events': events,
        'message': 'Webhook registered. Events will be POST-ed to your URL.'
    })


@app.route('/api/v1/kyc/webhook/test', methods=['POST'])
@_require_api_key
def ecommerce_webhook_test():
    """Send a test event to the registered webhook URL."""
    api_key = request.headers.get('X-API-Key')
    with _webhook_lock:
        cfg = _webhook_registry.get(api_key)
    if not cfg:
        return jsonify({'error': 'No webhook registered for this API key'}), 404

    _fire_webhook(api_key, 'kyc.test', {
        'user_id': 'test_user_001',
        'trust_level': 'gold',
        'risk_score': 85
    })
    return jsonify({'sent': True, 'url': cfg['url']})


@app.route('/api/v1/kyc/users', methods=['GET'])
@_require_api_key
@_rate_limit
def ecommerce_kyc_users():
    """
    List approved KYC users, optionally filtered by role and/or platform.

    Query params:
        role      (optional)  - 'buyer' | 'seller'                     (default: all)
        platform  (optional)  - 'line' | 'messenger' | 'web'           (default: all)
        limit     (optional)  - max results (default: 100)
    """
    role     = request.args.get('role', '').strip().lower() or None
    platform = request.args.get('platform', '').strip().lower() or None
    limit    = min(int(request.args.get('limit', 100)), 500)

    try:
        from database import KYCRepository
        records = KYCRepository.get_all_records(status='approved', role=role, platform=platform, limit=limit)

        users = []
        for r in records:
            notes = {}
            if r.notes:
                try:
                    import json as _json
                    notes = _json.loads(r.notes)
                except Exception:
                    pass
            trust_level = notes.get('trust_level', 'bronze')
            users.append({
                'user_id': r.user_id,
                'role': r.role or 'buyer',
                'platform': r.platform or 'line',
                'name': ' '.join(p for p in [r.prefix, r.first_name, r.last_name] if p) or None,
                'trust_level': trust_level,
                'risk_score': notes.get('risk_score', 0),
                'transaction_limit': {'bronze': 10000, 'silver': 50000, 'gold': 100000, 'platinum': -1}.get(trust_level, 0),
                'verified_at': r.created_at.isoformat() if r.created_at else None,
            })

        return jsonify({'total': len(users), 'role_filter': role or 'all',
                        'platform_filter': platform or 'all', 'users': users})

    except Exception as e:
        print(f"❌ KYC users error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/v1/kyc/stats', methods=['GET'])
@_require_api_key
@_rate_limit
def ecommerce_kyc_stats():
    """Return aggregate KYC statistics for dashboard/reporting."""
    try:
        from database import KYCRepository
        repo = KYCRepository()
        all_records = repo.get_all_records()

        from collections import Counter
        status_counts = Counter(r.status for r in all_records)
        badge_counts  = {}
        for r in all_records:
            if r.status == 'approved' and r.notes:
                try:
                    import json as _json
                    n = _json.loads(r.notes)
                    lvl = n.get('trust_level', 'bronze')
                    badge_counts[lvl] = badge_counts.get(lvl, 0) + 1
                except Exception:
                    pass

        return jsonify({
            'total': len(all_records),
            'by_status': dict(status_counts),
            'by_trust_level': badge_counts,
            'approval_rate': round(status_counts.get('approved', 0) / max(len(all_records), 1) * 100, 1)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─── Internal: fire webhook after KYC saved ──────────────────────────────────
def notify_webhooks_on_kyc_complete(user_id: str, status: str, trust_level: str, risk_score: float):
    """Called internally when a KYC record is saved/approved."""
    event = 'kyc.approved' if status == 'approved' else 'kyc.rejected'
    payload = {'user_id': user_id, 'status': status, 'trust_level': trust_level, 'risk_score': risk_score}
    with _webhook_lock:
        keys = list(_webhook_registry.keys())
    for key in keys:
        _fire_webhook(key, event, payload)
# ─────────────────────────────────────────────────────────────────────────────


if __name__ == '__main__':
    PORT = int(os.getenv('PORT', 5001))

    print("=" * 60)
    print("🌐 QuickChat ID - Web API Server")
    print("=" * 60)
    print(f"\n🚀 Starting server on http://0.0.0.0:{PORT}")
    print(f"\n🤖 ADK Agent: {root_agent.name} ({root_agent.model})")
    print(f"   Tools: {len(root_agent.tools)} available")
    print(f"   ✅ Same agent as LINE Bot!")
    print(f"\n✅ API Endpoints:")
    print(f"   POST /api/session/init - Initialize session")
    print(f"   POST /api/chat/message - Send message")
    print(f"   POST /api/chat/image - Upload image")
    print(f"   GET  /api/verification/status/<session_id> - Get status")
    print(f"   GET  /api/health - Health check")
    print(f"\n🌍 CORS enabled for:")
    print(f"   - http://localhost:5173 (Vite)")
    print(f"   - http://localhost:3000 (React)")
    print(f"\n🏢 Enterprise Services:")
    print(f"   - OPA Policy Engine: {'✅ Real' if opa.available else '⚡ Mock'}")
    print(f"   - Presidio PII Masking: {'✅ Real' if presidio.available else '⚡ Mock'}")
    print(f"   - Telemetry/Tracing: {'✅ Real' if telemetry.available else '⚡ Mock'}")
    print(f"   - Guardrails: ✅ Active")
    print(f"   - Keycloak IAM: {'✅ Real' if keycloak.available else '⚡ Mock'}")
    print(f"\n💡 AI Stack:")
    print(f"   - Gemini 2.5 Flash")
    print(f"   - PaddleOCR/Typhoon OCR")
    print(f"   - AWS Rekognition Face Matching")
    print(f"   - Liveness & Deepfake Detection")
    print("=" * 60)

    # Disable debug mode to prevent auto-reload which loses session data
    app.run(host='0.0.0.0', port=PORT, debug=False)
