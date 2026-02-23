"""
LINE Webhook Application
Connects LINE Bot to ADK KYC Orchestrator Agent
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from flask import Flask, request, abort
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv('agents/kyc_orchestrator/.env')

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Suppress LINE SDK deprecation warnings (v2 API still works)
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning, module='linebot')

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage,
    TextSendMessage, FlexSendMessage
)

# Import LINE bot components
from chat_platforms.line.line_bot import LineBotHandler, create_line_bot

# Import ADK agent directly
try:
    from agents.kyc_orchestrator.agent import root_agent
    print("✓ KYC Agent imported successfully")
    agent_available = True
except Exception as e:
    print(f"⚠️  Could not import KYC agent: {e}")
    agent_available = False

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

# Configuration
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    print("❌ LINE credentials not found in .env file")
    print("Please add LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET")
    sys.exit(1)

# Initialize Flask app
app = Flask(__name__)

# Initialize LINE Bot
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
line_bot_handler = create_line_bot()

# ─── Messenger (Facebook) ────────────────────────────────────────────────────
MESSENGER_VERIFY_TOKEN      = os.getenv('MESSENGER_VERIFY_TOKEN', '')
MESSENGER_PAGE_ACCESS_TOKEN = os.getenv('MESSENGER_PAGE_ACCESS_TOKEN', '')
MESSENGER_APP_SECRET        = os.getenv('MESSENGER_APP_SECRET', '')

messenger_available = bool(MESSENGER_PAGE_ACCESS_TOKEN)  # App Secret optional (skips sig verify)
if messenger_available:
    from chat_platforms.messenger.messenger_bot import MessengerBotHandler
    messenger_bot = MessengerBotHandler(MESSENGER_PAGE_ACCESS_TOKEN, MESSENGER_APP_SECRET)
    sig_mode = "✅ Signature verify ON" if MESSENGER_APP_SECRET else "⚠️  Signature verify OFF (no App Secret)"
    print(f"✓ Messenger Bot initialized — {sig_mode}")
else:
    messenger_bot = None
    print("⚠️  Messenger not configured (set MESSENGER_PAGE_ACCESS_TOKEN to enable)")

# Session storage (in production, use Redis or database)
user_sessions: Dict[str, Dict] = {}


def get_or_create_session(user_id: str) -> Dict:
    """Get or create user session"""
    if user_id not in user_sessions:
        # [Telemetry] Track session creation
        with telemetry.trace_span("line_session_init", {"user_id": user_id, "source": "line"}) as span:
            # [Keycloak] Register user in IAM
            keycloak_user = keycloak.create_user({
                'username': f"line_{user_id[:12]}",
                'email': f"line_{user_id[:8]}@quickchat.id",
                'firstName': 'LINE',
                'lastName': 'User'
            })
            print(f"   🔐 Keycloak: {keycloak_user.get('message', 'user created')}")

            user_sessions[user_id] = {
                'session_id': None,
                'state': 'welcome',
                'uploaded_images': {},
                'user_data': {},
                'ocr_data': None,
                'created_at': datetime.now().isoformat(),
                'keycloak_user_id': keycloak_user.get('user_id', user_id)
            }

            telemetry.record_event("line_session_created", {
                "user_id": user_id,
                "source": "line"
            })

    return user_sessions[user_id]


def check_existing_kyc(user_id: str) -> dict:
    """
    Check if user already has KYC record in database.
    Uses priority order: approved > rejected > failed > pending
    to avoid phantom 'failed' records hiding real approved/rejected ones.
    Returns dict with: has_record, status, record, trust_badge
    """
    try:
        from database.models import SessionLocal, KYCVerification
        from sqlalchemy import desc

        db = SessionLocal()
        try:
            # Priority: approved first, then rejected, then failed, then pending
            # Ignore empty phantom records (no first_name AND no id_number)
            status_priority = ['approved', 'rejected', 'failed', 'pending']
            record = None

            for status in status_priority:
                candidate = (
                    db.query(KYCVerification)
                    .filter(
                        KYCVerification.user_id == user_id,
                        KYCVerification.status == status
                    )
                    .order_by(desc(KYCVerification.created_at))
                    .first()
                )
                if candidate:
                    # Skip phantom records: no name AND no id_number (empty fallback saves)
                    if candidate.first_name is None and candidate.id_number is None:
                        continue
                    record = candidate
                    break

            # If no real record found, try any record as last resort
            if not record:
                record = (
                    db.query(KYCVerification)
                    .filter(KYCVerification.user_id == user_id)
                    .order_by(desc(KYCVerification.created_at))
                    .first()
                )

        finally:
            db.close()

        if not record:
            return {'has_record': False, 'status': None, 'record': None, 'trust_badge': None}

        # Read trust_level from dedicated column (fast)
        trust_badge = record.trust_level.upper() if record.trust_level else None

        # Fallback: parse from notes field (old format "trust_level:gold")
        if not trust_badge and record.notes and 'trust_level:' in record.notes:
            trust_badge = record.notes.split('trust_level:')[1].split('\n')[0].strip().upper()

        # Fallback: parse from verification_result or notes text
        if not trust_badge:
            search_text = (record.verification_result or '') + (record.notes or '')
            for badge in ['Platinum', 'Gold', 'Silver', 'Bronze']:
                if badge.lower() in search_text.lower():
                    trust_badge = badge.upper()
                    break

        print(f"🔍 DB check for {user_id}: status={record.status}, badge={trust_badge}, score={record.risk_score}, id={record.id}")
        return {
            'has_record': True,
            'status': record.status,
            'record': record,
            'trust_badge': trust_badge,
            'risk_score': record.risk_score or 0
        }
    except Exception as e:
        print(f"⚠️  Error checking existing KYC: {e}")
        return {'has_record': False, 'status': None, 'record': None, 'trust_badge': None}


def _build_status_message(kyc_check: dict) -> str:
    """สร้างข้อความแสดงสถานะ KYC ปัจจุบัน"""
    record = kyc_check['record']
    status_emoji = {'approved': '✅', 'rejected': '❌', 'failed': '⚠️', 'pending': '⏳'}
    status_text = {'approved': 'ผ่านการยืนยัน', 'rejected': 'ไม่ผ่าน', 'failed': 'ล้มเหลว', 'pending': 'รอดำเนินการ'}
    name = f"{record.prefix or ''} {record.first_name or ''} {record.last_name or ''}".strip()
    date_str = record.created_at.strftime('%d/%m/%Y') if record.created_at else ''
    badge = kyc_check['trust_badge'] or '-'
    return (
        f"{status_emoji.get(record.status, '❓')} สถานะการยืนยันตัวตน\n\n"
        f"👤 ชื่อ: {name or 'ไม่ระบุ'}\n"
        f"📊 สถานะ: {status_text.get(record.status, record.status)}\n"
        f"🏅 Trust Badge: {badge}\n"
        f"📅 วันที่: {date_str}"
    )


def _build_approved_lock_message(kyc_check: dict) -> str:
    """ข้อความสำหรับ user ที่ approved แล้ว (Lock ห้ามทำซ้ำ)"""
    record = kyc_check['record']
    name = f"{record.prefix or ''} {record.first_name or ''} {record.last_name or ''}".strip()
    badge = kyc_check['trust_badge'] or 'BRONZE'
    date_str = ''
    if record.verified_at:
        date_str = record.verified_at.strftime('%d/%m/%Y')
    elif record.created_at:
        date_str = record.created_at.strftime('%d/%m/%Y')
    return (
        f"✅ คุณผ่านการยืนยันตัวตนแล้ว\n\n"
        f"👤 ชื่อ: {name or 'ไม่ระบุ'}\n"
        f"🏅 ระดับ: {badge} Badge\n"
        f"📅 วันที่ยืนยัน: {date_str}\n\n"
        f"ไม่สามารถยืนยันตัวตนซ้ำได้\n"
        f"พิมพ์ 'สถานะ' เพื่อดูข้อมูลการยืนยัน\n"
        f"หากมีปัญหา กรุณาติดต่อฝ่ายสนับสนุน"
    )


def _build_rejected_retry_message(kyc_check: dict) -> str:
    """ข้อความสำหรับ user ที่ rejected/failed (อนุญาตให้ลองใหม่)"""
    record = kyc_check['record']
    date_str = record.created_at.strftime('%d/%m/%Y') if record.created_at else ''
    reason = (record.verification_result or 'ไม่ทราบสาเหตุ')[:100]
    return (
        f"⚠️ พบข้อมูลการยืนยันตัวตนครั้งก่อน\n\n"
        f"📅 วันที่: {date_str}\n"
        f"❌ สถานะ: ไม่ผ่าน\n"
        f"📋 สาเหตุ: {reason}\n\n"
        f"พิมพ์ 'ยืนยันตัวตน' หรือ 'พร้อม' เพื่อเริ่มยืนยันตัวตนใหม่"
    )


def send_badge_push(user_id: str, trust_level: str, risk_score: float = 0,
                    name: str = None, issued_date: str = None, role: str = None):
    """
    Push a Trust Badge Flex Message to LINE user.
    Used after KYC completion and when returning approved users check status.
    """
    try:
        trust_level = trust_level.lower()
        limits = {'bronze': 10000, 'silver': 50000, 'gold': 100000, 'platinum': -1}
        transaction_limit = limits.get(trust_level, 10000)

        flex_content = line_bot_handler.create_trust_badge_flex(
            trust_level=trust_level,
            risk_score=risk_score,
            transaction_limit=transaction_limit,
            name=name,
            issued_date=issued_date,
            role=role
        )

        line_bot_api.push_message(
            user_id,
            FlexSendMessage(
                alt_text=f"Trust Badge: {trust_level.upper()} - ยืนยันตัวตนสำเร็จ",
                contents=flex_content
            )
        )
        print(f"🏅 Sent {trust_level.upper()} badge Flex card to {user_id}")
    except Exception as e:
        print(f"⚠️  Badge push failed: {e}")


def save_image_from_line(message_id: str, user_id: str, image_type: str) -> Optional[str]:
    """
    Download image from LINE and save to temp directory

    Args:
        message_id: LINE message ID
        user_id: LINE user ID
        image_type: 'id_card' or 'selfie'

    Returns:
        Path to saved image or None
    """
    try:
        # Get image content from LINE
        message_content = line_bot_api.get_message_content(message_id)

        # Create temp directory if not exists
        temp_dir = Path(tempfile.gettempdir()) / 'quickchat_id' / user_id
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Save image
        image_path = temp_dir / f"{image_type}_{message_id}.jpg"
        with open(image_path, 'wb') as f:
            for chunk in message_content.iter_content():
                f.write(chunk)

        print(f"✓ Image saved: {image_path}")
        return str(image_path)

    except Exception as e:
        print(f"Error saving image: {e}")
        return None


def call_adk_agent_via_http(user_id: str, message: str, image_path: Optional[str] = None) -> str:
    """
    Call ADK agent via HTTP to ADK web server

    This is simpler than calling the agent directly and handles all the complexity internally.

    Args:
        user_id: LINE user ID
        message: User message text
        image_path: Optional path to uploaded image

    Returns:
        Agent response text
    """
    import requests

    session = get_or_create_session(user_id)

    try:
        # [Presidio] Mask PII in user message logs
        presidio_msg = presidio.anonymize(message)
        masked_msg = presidio_msg.get('anonymized_text', message) if isinstance(presidio_msg, dict) else str(presidio_msg)
        print(f"📤 Calling ADK web server for user {user_id}: {masked_msg[:50]}...")

        # ADK web server URL (configurable via env for Docker)
        ADK_SERVER_URL = os.getenv('ADK_SERVER_URL', 'http://localhost:8000')

        # Get or create session ID
        if not session.get('adk_session_id'):
            # Create new session
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
            return "❌ ไม่สามารถสร้าง session ได้ กรุณาลองใหม่"

        # Send message to agent via ADK web server using SSE endpoint
        # newMessage should be a Content object with role and parts
        # Include image_path in message text so the agent can pass it to OCR/liveness/face tools
        message_text = message
        if image_path and os.path.exists(str(image_path)):
            message_text = f"{message}\n[IMAGE_FILE: {image_path}]"
            print(f"📎 Appending image path to message: {image_path}")

            # Also append the ID card path if we have it (needed for face matching)
            stored_images = session.get('uploaded_images', {})
            id_card_path = stored_images.get('id_card', '')
            if id_card_path and os.path.exists(str(id_card_path)) and str(id_card_path) != str(image_path):
                message_text += f"\n[ID_CARD_FILE: {id_card_path}]"
                print(f"📎 Appending ID card path: {id_card_path}")

        # Progress messages shown in LINE when each tool is called
        _TOOL_PROGRESS = {
            'extract_thai_id':        '🔍 กำลังอ่าน OCR บัตรประชาชน...',
            'evaluate_document_risk': '📋 กำลังตรวจสอบความถูกต้องของบัตร...',
            'check_scam_intent':      '🛡 กำลังตรวจสอบความปลอดภัย...',
            'detect_liveness':        '👁 กำลังตรวจสอบ Liveness...',
            'detect_deepfake':        '🤖 กำลังตรวจสอบ Deepfake...',
            'match_faces':            '👤 กำลังเปรียบเทียบใบหน้ากับบัตร...',
            'evaluate_biometric_risk':'📊 กำลังประเมิน Biometric Risk...',
            'evaluate_final_decision':'⚖️ กำลังตัดสินใจขั้นสุดท้าย...',
            'issue_trust_badge':      '🏅 กำลังออก Trust Badge...',
            'save_kyc_record':        '💾 กำลังบันทึกข้อมูล...',
        }
        # LINE user IDs start with 'U' and are 33 chars long
        _is_line_user = user_id.startswith('U') and len(user_id) > 20

        def _push_progress(msg: str):
            """Push a progress message to LINE (best-effort, never raises)"""
            if not _is_line_user:
                return
            try:
                line_bot_api.push_message(user_id, TextSendMessage(text=msg))
            except Exception as pe:
                print(f"   ⚠️  Progress push failed: {pe}")

        def _do_sse_call(payload: dict) -> requests.Response:
            return requests.post(
                f"{ADK_SERVER_URL}/run_sse",
                json=payload,
                stream=True,
                timeout=120
            )

        run_payload = {
            "app_name": "kyc_orchestrator",
            "session_id": adk_session_id,
            "user_id": user_id,
            "newMessage": {
                "role": "user",
                "parts": [{"text": message_text}]
            }
        }

        run_response = _do_sse_call(run_payload)

        # Session recovery: if server restarted, old session is gone — create new and retry once
        if run_response.status_code in (404, 400):
            print(f"⚠️  ADK session invalid (status {run_response.status_code}), resetting and retrying...")
            run_response.close()
            session['adk_session_id'] = None
            create_response = requests.post(
                f"{ADK_SERVER_URL}/apps/kyc_orchestrator/users/{user_id}/sessions",
                timeout=10
            )
            if create_response.status_code == 200:
                session_data = create_response.json()
                session['adk_session_id'] = session_data.get('id')
                adk_session_id = session['adk_session_id']
                print(f"✓ Created new ADK session after reset: {adk_session_id}")
                run_payload['session_id'] = adk_session_id
                _push_progress("⚠️ Session ถูก reset กรุณาเริ่มยืนยันตัวตนใหม่ พิมพ์ 'เริ่มใหม่'")
                run_response = _do_sse_call(run_payload)

        if run_response.status_code != 200:
            print(f"❌ ADK server error: {run_response.status_code}")
            body = run_response.text[:200]
            print(f"Response: {body}")
            run_response.close()
            return f"เกิดข้อผิดพลาด: ADK server returned {run_response.status_code}"

        # Stream SSE in real-time: push progress when tool calls are detected
        response_text = ""
        pushed_tools: set = set()  # avoid duplicate progress for same tool

        try:
            for raw_line in run_response.iter_lines():
                if not raw_line:
                    continue
                line = raw_line.decode('utf-8') if isinstance(raw_line, bytes) else raw_line
                if not line.startswith('data: '):
                    continue
                try:
                    data = json.loads(line[6:])
                    parts = data.get('content', {}).get('parts', [])
                    for part in parts:
                        if 'functionCall' in part:
                            tool_name = part['functionCall'].get('name', '')
                            print(f"   🔧 Tool called: {tool_name}")
                            if tool_name not in pushed_tools:
                                pushed_tools.add(tool_name)
                                progress_msg = _TOOL_PROGRESS.get(tool_name)
                                if progress_msg:
                                    _push_progress(progress_msg)
                        elif 'text' in part:
                            response_text += part['text']
                except json.JSONDecodeError:
                    continue
        finally:
            run_response.close()

        if not response_text:
            response_text = "ขออภัย ไม่สามารถประมวลผลได้ กรุณาลองใหม่อีกครั้ง"

        # [Presidio] Mask PII in agent response logs
        presidio_resp = presidio.anonymize(response_text)
        masked_resp = presidio_resp.get('anonymized_text', response_text) if isinstance(presidio_resp, dict) else str(presidio_resp)
        print(f"✅ Agent response (masked): {masked_resp[:100]}...")
        return response_text.strip()

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to ADK web server")
        return "❌ ไม่สามารถเชื่อมต่อกับ ADK server ได้\n\nกรุณาเริ่ม ADK server ก่อน:\n  cd agents && adk web"
    except requests.exceptions.Timeout:
        print("❌ ADK server timeout")
        return "⏱️ การประมวลผลใช้เวลานานเกินไป กรุณาลองใหม่อีกครั้ง"
    except Exception as e:
        print(f"❌ Error calling ADK: {e}")
        import traceback
        traceback.print_exc()
        return f"เกิดข้อผิดพลาด: {str(e)}"


def call_adk_agent(user_id: str, message: str, image_path: Optional[str] = None) -> str:
    """
    Call ADK agent (via HTTP to ADK web server)
    Also links LINE user_id with KYC record after completion
    """
    response = call_adk_agent_via_http(user_id, message, image_path)

    # Extract and store OCR data from response
    session = get_or_create_session(user_id)
    import re
    import logging
    logger = logging.getLogger(__name__)

    # Check if response contains OCR results
    # Try multiple patterns for Thai ID name
    if 'ชื่อบนบัตร' in response or 'ชื่อ' in response and 'บัตร' in response:
        logger.warning(f"🔍 Detected OCR-related response for {user_id}")
        logger.warning(f"   Response snippet: {response[:200]}")

        # Try multiple patterns
        patterns = [
            r'\*\*ชื่อบนบัตร[:\s]+\*\*\s*([^\n]+)',  # **ชื่อบนบัตร:** นาย สมชาย
            r'ชื่อบนบัตร[:\s]+([^\n]+)',             # ชื่อบนบัตร: นาย สมชาย
            r'ชื่อ[:\s]+([^\n\*]+)',                  # ชื่อ: นาย สมชาย
        ]

        name_match = None
        for pattern in patterns:
            name_match = re.search(pattern, response)
            if name_match:
                logger.warning(f"   ✓ Pattern matched: {pattern}")
                break

        if name_match:
            full_name = name_match.group(1).strip()
            # Remove any markdown formatting
            full_name = full_name.replace('**', '').replace('*', '')

            # Parse and store in session
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                session['ocr_data'] = {
                    'full_name': full_name,
                    'name_parts': name_parts
                }
                logger.warning(f"📝 Stored OCR data in session for {user_id}: {full_name}")
            else:
                logger.warning(f"   ✗ Name parts too short: {name_parts}")
        else:
            logger.warning(f"   ✗ No name pattern matched")

    # Always try to link LINE user_id with recent KYC records
    # This ensures both approved and rejected records are linked
    try:
        from database import KYCRepository
        from database.models import get_bangkok_time
        from datetime import timedelta
        import time

        # Check if response indicates FINAL KYC completion (not intermediate steps)
        # Avoid 'เสร็จสิ้น'/'ยินดีด้วย' — they also appear in mid-flow OCR messages
        completion_indicators = [
            'Trust Badge',
            'PLATINUM', 'GOLD', 'SILVER', 'BRONZE',
            'Platinum Badge', 'Gold Badge', 'Silver Badge', 'Bronze Badge',
            'ไม่ผ่านการยืนยันตัวตน', 'ปฏิเสธการยืนยัน',
            'บล็อก', 'ไม่สามารถดำเนินการต่อ',
        ]

        is_completion = any(indicator in response for indicator in completion_indicators)

        if is_completion:
            # [Telemetry] Track KYC completion
            telemetry.record_event("line_kyc_completion", {
                "user_id": user_id,
                "indicators": [ind for ind in completion_indicators if ind in response]
            })

            # [OPA] Policy-based risk assessment using shared storage data
            try:
                face_data = {}
                face_shared_dir = Path(tempfile.gettempdir()) / 'quickchat_id_face'
                if face_shared_dir.exists():
                    face_files = sorted(face_shared_dir.glob('*.json'), key=lambda x: x.stat().st_mtime, reverse=True)
                    if face_files and (time.time() - face_files[0].stat().st_mtime < 300):
                        with open(face_files[0], 'r', encoding='utf-8') as f:
                            face_data = json.load(f)

                opa_input = {
                    'face_match_score': face_data.get('similarity_score', 0.5),
                    'liveness_score': face_data.get('liveness_score', 0.7),
                    'deepfake_probability': face_data.get('deepfake_probability', 0.1),
                    'ocr_confidence': 0.9,
                    'scam_score': 0.1
                }

                opa_result = opa.evaluate_policy("kyc/risk_assessment", opa_input)
                trust_level = opa_result.get('trust_level', 'bronze')
                risk_score = opa_result.get('risk_score', 50)
                print(f"   🏛️ OPA Policy (LINE): score={risk_score}, level={trust_level}")

                telemetry.record_metric("line_risk_score", risk_score, "points", {"user_id": user_id})

                # [Keycloak] Assign role based on trust level
                keycloak_uid = session.get('keycloak_user_id', user_id)
                role_result = keycloak.assign_role(keycloak_uid, f"{trust_level}_user")
                print(f"   🔐 Keycloak role (LINE): {role_result.get('message', 'assigned')}")
            except Exception as opa_err:
                print(f"   ⚠️  OPA/Keycloak error: {opa_err}")

            # Give a moment for database to commit (if Agent called save_kyc_record)
            time.sleep(1.0)

            # Search for recent records (within last 90 seconds)
            records = KYCRepository.get_all_records(limit=20)
            current_time = get_bangkok_time()
            linked = False
            active_record = None  # Track the record we link/create for direct badge push
            _window = timedelta(seconds=90)

            for record in records:
                rec_time = record.created_at.replace(tzinfo=None)
                if rec_time <= (current_time.replace(tzinfo=None) - _window):
                    continue  # too old

                # Case 1: already linked to this LINE user (previous fallback run / proper save)
                if record.user_id == user_id:
                    print(f"✅ Record {record.id} ({record.status}) already linked to {user_id} — skip duplicate")
                    active_record = record
                    linked = True
                    break

                # Case 2: created by agent with generated user_id — link it
                if not record.user_id.startswith('U') and not record.user_id.isdigit():
                    original_user_id = record.user_id
                    _platform = 'messenger' if (user_id or '').isdigit() else 'line'
                    KYCRepository.update_kyc_record(
                        record.id,
                        user_id=user_id,
                        platform=_platform,
                        notes=f"LINE User (original: {original_user_id})"
                    )
                    print(f"✅ Linked KYC record {record.id} ({record.status}) with {user_id}")
                    # Refresh record from DB to get updated user_id
                    from database.models import SessionLocal, KYCVerification
                    _db = SessionLocal()
                    try:
                        active_record = _db.query(KYCVerification).filter(KYCVerification.id == record.id).first()
                    finally:
                        _db.close()
                    linked = True
                    break

            # If no recent record found, Agent probably didn't call save_kyc_record
            # Create fallback record
            if not linked:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"⚠️  KYC completion detected but no recent record found!")
                logger.warning(f"   Response contained: {[ind for ind in completion_indicators if ind in response]}")
                logger.warning(f"   Agent may have failed to call save_kyc_record tool")
                logger.warning(f"   User: {user_id}")
                logger.warning(f"   🔧 Creating fallback record...")
                logger.warning(f"   Response (first 500 chars): {response[:500]}")

                # Determine status from response
                status = 'failed'
                verification_result = 'Auto-saved: KYC completion detected but Agent did not save record'

                # Check badge indicators (case-insensitive, both title and upper)
                _badge_in_response = any(
                    b in response for b in ['Platinum', 'Gold', 'Silver', 'Bronze',
                                            'PLATINUM', 'GOLD', 'SILVER', 'BRONZE',
                                            'Trust Badge', 'platinum', 'gold', 'silver', 'bronze']
                )
                if _badge_in_response:
                    status = 'approved'
                    verification_result = 'Auto-saved: Verification completed with Trust Badge'
                elif any(reject in response for reject in ['ไม่ผ่าน', 'ปฏิเสธ', 'บล็อก']):
                    status = 'rejected'
                    verification_result = 'Auto-saved: Verification rejected'

                # Parse OCR data from session first, fallback to response
                import re

                first_name = None
                last_name = None
                id_number = None
                prefix = None
                date_of_birth = None
                address = None

                # Try to get OCR data from session
                session = get_or_create_session(user_id)
                if session.get('ocr_data') and session['ocr_data'].get('name_parts'):
                    name_parts = session['ocr_data']['name_parts']
                    logger.warning(f"   📦 Using OCR data from session: {name_parts}")
                    if len(name_parts) >= 3:
                        prefix = name_parts[0]
                        first_name = name_parts[1]
                        last_name = ' '.join(name_parts[2:])
                    elif len(name_parts) == 2:
                        first_name = name_parts[0]
                        last_name = name_parts[1]
                else:
                    # Try to load from shared OCR storage
                    logger.warning(f"   🔍 No session OCR data, checking shared storage...")
                    try:
                        shared_dir = Path(tempfile.gettempdir()) / 'quickchat_id_ocr'
                        if shared_dir.exists():
                            # Find most recent OCR file (within last 5 minutes)
                            ocr_files = list(shared_dir.glob('*.json'))
                            if ocr_files:
                                # Sort by modification time
                                ocr_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                                latest_file = ocr_files[0]

                                # Check if file is recent (within 5 minutes)
                                import time as time_module
                                age = time_module.time() - latest_file.stat().st_mtime
                                if age < 300:  # 5 minutes
                                    with open(latest_file, 'r', encoding='utf-8') as f:
                                        ocr_data = json.load(f)

                                    name_th = ocr_data.get('name_th', '')
                                    if name_th:
                                        logger.warning(f"   📦 Found OCR data in shared storage: {name_th}")
                                        name_parts = name_th.split()
                                        if len(name_parts) >= 3:
                                            prefix = name_parts[0]
                                            first_name = name_parts[1]
                                            last_name = ' '.join(name_parts[2:])
                                        elif len(name_parts) == 2:
                                            first_name = name_parts[0]
                                            last_name = name_parts[1]

                                        # Also get other fields from OCR
                                        if not id_number:
                                            id_number = ocr_data.get('id_number', '')
                                            if id_number:
                                                logger.warning(f"   📦 Got ID number from OCR: {id_number}")

                                        date_of_birth = ocr_data.get('date_of_birth', '')
                                        address = ocr_data.get('address', '')
                                        if date_of_birth:
                                            logger.warning(f"   📦 Got date of birth from OCR: {date_of_birth}")
                                        if address:
                                            logger.warning(f"   📦 Got address from OCR: {address[:50]}...")
                                    else:
                                        logger.warning(f"   ✗ OCR data has no name_th")
                                else:
                                    logger.warning(f"   ✗ OCR data too old ({age:.0f}s)")
                    except Exception as e:
                        logger.warning(f"   ✗ Could not load from shared storage: {e}")

                    # Final fallback: Try to extract name from response
                    if not first_name:
                        logger.warning(f"   🔍 Parsing from response as last resort")
                        name_match = re.search(r'\*\*ชื่อบนบัตร[:\s]+\*\*\s*([^\n]+)', response)
                        if name_match:
                            full_name = name_match.group(1).strip()
                            name_parts = full_name.split()
                            if len(name_parts) >= 3:
                                prefix = name_parts[0]
                                first_name = name_parts[1]
                                last_name = ' '.join(name_parts[2:])
                            elif len(name_parts) == 2:
                                first_name = name_parts[0]
                                last_name = name_parts[1]

                # Try to extract ID number from response
                id_match = re.search(r'\b(\d{1}[-\s]?\d{4}[-\s]?\d{5}[-\s]?\d{2}[-\s]?\d{1}|\d{13})\b', response)
                if id_match:
                    id_number = id_match.group(1).replace('-', '').replace(' ', '')

                # Try to get face matching results from shared storage
                face_similarity_score = None
                face_confidence = None
                try:
                    face_shared_dir = Path(tempfile.gettempdir()) / 'quickchat_id_face'
                    if face_shared_dir.exists():
                        # Find most recent face matching file (within last 5 minutes)
                        face_files = list(face_shared_dir.glob('*.json'))
                        if face_files:
                            # Sort by modification time
                            face_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                            latest_face_file = face_files[0]

                            # Check if file is recent (within 5 minutes)
                            import time as time_module
                            age = time_module.time() - latest_face_file.stat().st_mtime
                            if age < 300:  # 5 minutes
                                with open(latest_face_file, 'r', encoding='utf-8') as f:
                                    face_data = json.load(f)

                                # Get similarity score (convert from 0-1 to 0-100 if needed)
                                similarity_raw = face_data.get('similarity_score')
                                if similarity_raw is not None:
                                    # AWS returns 0-1 range, convert to 0-100
                                    if similarity_raw <= 1.0:
                                        face_similarity_score = similarity_raw * 100
                                    else:
                                        face_similarity_score = similarity_raw

                                # Get confidence (convert string to numeric)
                                confidence_raw = face_data.get('confidence')
                                if confidence_raw:
                                    if isinstance(confidence_raw, str):
                                        # Convert string confidence to numeric
                                        confidence_map = {
                                            'high': 95.0,
                                            'medium': 75.0,
                                            'low': 50.0
                                        }
                                        face_confidence = confidence_map.get(confidence_raw.lower(), 75.0)
                                    else:
                                        face_confidence = float(confidence_raw)

                                logger.warning(f"   📦 Found face matching data in shared storage")
                                logger.warning(f"      Similarity: {face_similarity_score}%")
                                logger.warning(f"      Confidence: {face_confidence}%")
                except Exception as e:
                    logger.warning(f"   ✗ Could not load face matching from shared storage: {e}")

                logger.warning(f"   📝 Parsed data summary:")
                logger.warning(f"      Name: {prefix} {first_name} {last_name}")
                logger.warning(f"      ID: {id_number}")
                logger.warning(f"      DOB: {date_of_birth}")
                logger.warning(f"      Address: {address[:50] if address else None}...")
                logger.warning(f"      Face Similarity: {face_similarity_score}")
                logger.warning(f"      Face Confidence: {face_confidence}")

                # Create record with parsed data
                try:
                    _platform = 'messenger' if (user_id or '').isdigit() else 'line'
                    try:
                        _fb_risk = risk_score
                        _fb_trust = trust_level
                    except NameError:
                        _fb_risk = None
                        _fb_trust = None
                    # Parse trust_level from response text if OPA didn't set it
                    if not _fb_trust:
                        for _bl in ['platinum', 'gold', 'silver', 'bronze']:
                            if _bl in response.lower():
                                _fb_trust = _bl
                                break
                    fallback_record = KYCRepository.create_kyc_record(
                        user_id=user_id,
                        status=status,
                        verification_result=verification_result,
                        is_verified=(status == 'approved'),
                        prefix=prefix,
                        first_name=first_name,
                        last_name=last_name,
                        id_number=id_number,
                        date_of_birth=date_of_birth,
                        address=address,
                        face_similarity_score=face_similarity_score,
                        face_confidence=face_confidence,
                        platform=_platform,
                        risk_score=_fb_risk,
                        trust_level=_fb_trust,
                        notes=f"Fallback auto-save: Agent did not call save_kyc_record.\nResponse: {response[:500]}"
                    )
                    logger.warning(f"✅ Created fallback record ID: {fallback_record.id}")
                    active_record = fallback_record
                    linked = True
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback save failed: {fallback_error}")
                    import traceback
                    traceback.print_exc()

            # [Badge Push] Send Trust Badge Flex Message if KYC is approved
            # Prefer active_record (just linked/created) for freshness; fallback to check_existing_kyc
            try:
                rec = active_record
                rec_status = rec.status if rec else None

                # If active_record is not approved, also check DB in case it was updated
                if not rec or rec_status != 'approved':
                    kyc_badge_check = check_existing_kyc(user_id)
                    if kyc_badge_check.get('status') == 'approved':
                        rec = kyc_badge_check.get('record')
                        rec_status = 'approved'

                if rec_status == 'approved' and rec:
                    name_parts = [p for p in [rec.prefix, rec.first_name, rec.last_name] if p]
                    display_name = ' '.join(name_parts) or None
                    issued = rec.created_at.strftime('%d/%m/%Y') if rec.created_at else None
                    badge_level = (rec.trust_level or 'bronze').lower()
                    # Parse trust_level from notes if not in column
                    if not rec.trust_level and rec.notes and 'trust_level:' in rec.notes:
                        badge_level = rec.notes.split('trust_level:')[1].split('\n')[0].strip().lower()
                    _score = rec.risk_score or 0
                    _role = rec.role if rec else None
                    print(f"🏅 Sending badge push: level={badge_level}, score={_score}, record={rec.id}")
                    send_badge_push(user_id, badge_level, _score, name=display_name, issued_date=issued, role=_role)
            except Exception as badge_err:
                print(f"⚠️  Could not send badge push: {badge_err}")

    except Exception as e:
        print(f"⚠️  Could not link LINE user_id: {e}")
        import traceback
        traceback.print_exc()

    return response


@app.route('/webhook/line', methods=['POST'])
@app.route('/webhook-test/line-bot', methods=['POST'])  # Support your existing webhook URL
def line_webhook():
    """LINE webhook endpoint"""

    # Get X-Line-Signature header value
    signature = request.headers.get('X-Line-Signature', '')

    if not signature:
        app.logger.error("Missing X-Line-Signature header")
        abort(400)

    # Get request body as text
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    # Handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature")
        abort(400)
    except Exception as e:
        app.logger.error(f"Error handling webhook: {e}")
        import traceback
        traceback.print_exc()

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    """Handle text messages from LINE"""
    user_id = event.source.user_id
    text = event.message.text

    print(f"📩 Message from {user_id}: {text}")

    # [1] Special reset command — ก่อนทุกอย่าง (bypass DB check)
    if text.lower() in ['/start', 'เริ่มใหม่', 'restart']:
        if user_id in user_sessions:
            del user_sessions[user_id]
        flex_message = line_bot_handler.create_kyc_welcome_flex()
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text="QuickChat ID - ยืนยันตัวตน", contents=flex_message)
        )
        return

    # [2] Status check command — ทุก user ดูสถานะได้เสมอ
    if text.lower() in ['สถานะ', 'ตรวจสอบสถานะ', 'status', '/status']:
        kyc_check = check_existing_kyc(user_id)
        if kyc_check['has_record']:
            reply_text = _build_status_message(kyc_check)
        else:
            reply_text = "ยังไม่มีข้อมูลการยืนยันตัวตน\nพิมพ์ 'พร้อม' เพื่อเริ่มยืนยันตัวตน"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        # Send badge flex card as follow-up push if approved
        if kyc_check.get('status') == 'approved':
            rec = kyc_check.get('record')
            display_name = None
            if rec:
                name_parts = [p for p in [rec.prefix, rec.first_name, rec.last_name] if p]
                display_name = ' '.join(name_parts) or None
            issued = rec.created_at.strftime('%d/%m/%Y') if rec and rec.created_at else None
            badge_level = (kyc_check.get('trust_badge') or 'bronze').lower()
            _score = kyc_check.get('risk_score') or (rec.risk_score if rec else 0) or 0
            _role = rec.role if rec else None
            send_badge_push(user_id, badge_level, _score, name=display_name, issued_date=issued, role=_role)
        return

    # [3] Pre-check: ตรวจสอบ DB เฉพาะ fresh session (ยังไม่ได้เริ่มทำ KYC รอบนี้)
    if user_id not in user_sessions:
        kyc_check = check_existing_kyc(user_id)

        if kyc_check['status'] == 'approved':
            # LOCK: ผ่านแล้ว ห้ามทำซ้ำ ไม่สร้าง session
            reply_text = _build_approved_lock_message(kyc_check)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
            # Send badge flex card as push message (reply token already used)
            rec = kyc_check.get('record')
            display_name = None
            if rec:
                name_parts = [p for p in [rec.prefix, rec.first_name, rec.last_name] if p]
                display_name = ' '.join(name_parts) or None
            issued = rec.created_at.strftime('%d/%m/%Y') if rec and rec.created_at else None
            badge_level = (kyc_check.get('trust_badge') or 'bronze').lower()
            _score = kyc_check.get('risk_score') or (rec.risk_score if rec else 0) or 0
            _role = rec.role if rec else None
            send_badge_push(user_id, badge_level, _score, name=display_name, issued_date=issued, role=_role)
            return

        elif kyc_check['status'] in ['rejected', 'failed']:
            # แสดงสาเหตุ + สร้าง session พร้อมให้ลองใหม่
            reply_text = _build_rejected_retry_message(kyc_check)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
            get_or_create_session(user_id)
            return

    # Get user session (new or existing mid-KYC session)
    session = get_or_create_session(user_id)

    # Call ADK agent
    try:
        # [Telemetry] Track text message handling
        with telemetry.trace_span("line_text_message", {"user_id": user_id}):
            response_text = call_adk_agent(user_id, text)

            # [Guardrails] Validate AI output before sending to user
            guard_result = guardrails.validate_output(response_text)
            if not guard_result.get('valid', True):
                violations = guard_result.get('violations', [])
                print(f"   🛡️ Guardrails blocked: {[v['type'] for v in violations]}")
                response_text = "ขออภัย ระบบตรวจพบเนื้อหาที่ไม่เหมาะสม กรุณาลองใหม่"

            # [Presidio] Mask PII in logs (not in user response)
            presidio_result = presidio.anonymize(response_text)
            masked_for_log = presidio_result.get('anonymized_text', response_text) if isinstance(presidio_result, dict) else str(presidio_result)
            print(f"✅ LINE response (masked): {masked_for_log[:100]}...")

        # Send response
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_text)
        )

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"เกิดข้อผิดพลาด: {str(e)}")
        )


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    """Handle image messages from LINE"""
    user_id = event.source.user_id
    message_id = event.message.id

    print(f"🖼️  Image from {user_id}: {message_id}")

    # Get user session
    session = get_or_create_session(user_id)

    # Determine image type based on conversation state
    if 'id_card' not in session['uploaded_images']:
        image_type = 'id_card'
        user_prompt = "ได้รับรูปบัตรประชาชนแล้ว กำลังตรวจสอบ..."
    elif 'selfie' not in session['uploaded_images']:
        image_type = 'selfie'
        user_prompt = "ได้รับรูป Selfie แล้ว กำลังวิเคราะห์..."
    else:
        # Already have both images
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ได้รับรูปภาพครบแล้ว หากต้องการเริ่มใหม่ พิมพ์ 'เริ่มใหม่'")
        )
        return

    # Save image
    image_path = save_image_from_line(message_id, user_id, image_type)

    if not image_path:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ไม่สามารถดาวน์โหลดรูปภาพได้ กรุณาลองใหม่")
        )
        return

    # Store image path in session
    session['uploaded_images'][image_type] = image_path

    # Send acknowledgment and call agent
    try:
        # First, acknowledge receipt
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=user_prompt)
        )

        # [Telemetry] Track image processing
        with telemetry.trace_span(f"line_image_{image_type}", {"user_id": user_id, "image_type": image_type}):
            # Call agent with image
            response_text = call_adk_agent(user_id, f"ได้รับรูป{image_type}", image_path)

            # [Guardrails] Validate AI output before sending to user
            guard_result = guardrails.validate_output(response_text)
            if not guard_result.get('valid', True):
                violations = guard_result.get('violations', [])
                print(f"   🛡️ Guardrails blocked: {[v['type'] for v in violations]}")
                response_text = "ขออภัย ระบบตรวจพบเนื้อหาที่ไม่เหมาะสม กรุณาลองใหม่"

            # [Presidio] Mask PII in logs
            presidio_result = presidio.anonymize(response_text)
            masked_for_log = presidio_result.get('anonymized_text', response_text) if isinstance(presidio_result, dict) else str(presidio_result)
            print(f"✅ LINE image response (masked): {masked_for_log[:100]}...")

        # Send agent response
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text=response_text)
        )

    except Exception as e:
        print(f"Error processing image: {e}")
        import traceback
        traceback.print_exc()
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text=f"เกิดข้อผิดพลาดในการประมวลผล: {str(e)}")
        )


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {
        'status': 'ok',
        'service': 'QuickChat ID LINE Bot',
        'version': '2.0.0',
        'active_sessions': len(user_sessions),
        'enterprise_services': {
            'opa': 'real' if opa.available else 'mock',
            'presidio': 'real' if presidio.available else 'mock',
            'telemetry': 'real' if telemetry.available else 'mock',
            'guardrails': 'active',
            'keycloak': 'real' if keycloak.available else 'mock'
        }
    }


@app.route('/')
def index():
    """Root endpoint"""
    return """
    <html>
    <head><title>QuickChat ID LINE Bot</title></head>
    <body>
        <h1>🤖 QuickChat ID LINE Bot</h1>
        <p>Webhook endpoint: <code>/webhook/line</code></p>
        <p>Health check: <code>/health</code></p>
        <hr>
        <p>Active sessions: {}</p>
    </body>
    </html>
    """.format(len(user_sessions))


# ─── Facebook Messenger Webhook ──────────────────────────────────────────────

@app.route('/webhook/messenger', methods=['GET'])
def messenger_verify():
    """Facebook webhook challenge-response verification"""
    mode      = request.args.get('hub.mode')
    token     = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode == 'subscribe' and token == MESSENGER_VERIFY_TOKEN:
        print("✅ Messenger webhook verified")
        return challenge, 200
    return 'Forbidden', 403


@app.route('/webhook/messenger', methods=['POST'])
def messenger_webhook():
    """Receive events from Facebook Messenger"""
    if not messenger_available:
        return 'OK', 200

    # Verify HMAC-SHA256 signature (only if App Secret is configured)
    sig = request.headers.get('X-Hub-Signature-256', '')
    if sig and MESSENGER_APP_SECRET and not messenger_bot.verify_signature(request.data, sig):
        abort(403)

    data = request.json
    if data.get('object') != 'page':
        return 'OK', 200

    for entry in data.get('entry', []):
        for event in entry.get('messaging', []):
            sender_id = event['sender']['id']
            if 'message' in event:
                msg = event['message']
                if msg.get('attachments'):
                    for att in msg['attachments']:
                        if att['type'] == 'image':
                            _handle_messenger_image(sender_id, att['payload']['url'])
                elif msg.get('text'):
                    _handle_messenger_text(sender_id, msg['text'])
            elif 'postback' in event:
                if event['postback']['payload'] == 'STATUS':
                    _handle_messenger_text(sender_id, 'สถานะ')

    return 'OK', 200


def _handle_messenger_text(sender_id: str, text: str):
    """Handle text messages — same KYC pre-check + ADK flow as LINE"""
    print(f"📩 Messenger from {sender_id}: {text[:50]}")

    # [1] Reset command
    if text.lower() in ['/start', 'เริ่มใหม่', 'restart']:
        user_sessions.pop(sender_id, None)
        messenger_bot.send_text_message(
            sender_id,
            "สวัสดีครับ! ยินดีต้อนรับสู่ QuickChat ID 🎉\n\n"
            "ระบบยืนยันตัวตน KYC อัจฉริยะ\n"
            "พิมพ์ 'พร้อม' เพื่อเริ่มยืนยันตัวตน"
        )
        return

    # [2] Status check command
    if text.lower() in ['สถานะ', 'ตรวจสอบสถานะ', 'status', '/status']:
        kyc_check = check_existing_kyc(sender_id)
        if kyc_check['has_record']:
            messenger_bot.send_text_message(sender_id, _build_status_message(kyc_check))
            if kyc_check.get('status') == 'approved':
                _send_messenger_badge(sender_id, kyc_check)
        else:
            messenger_bot.send_text_message(
                sender_id,
                "ยังไม่มีข้อมูลการยืนยันตัวตน\nพิมพ์ 'พร้อม' เพื่อเริ่มยืนยันตัวตน"
            )
        return

    # [3] Pre-check: fresh session only
    if sender_id not in user_sessions:
        kyc_check = check_existing_kyc(sender_id)
        if kyc_check['status'] == 'approved':
            messenger_bot.send_text_message(sender_id, _build_approved_lock_message(kyc_check))
            _send_messenger_badge(sender_id, kyc_check)
            return
        elif kyc_check['status'] in ['rejected', 'failed']:
            messenger_bot.send_text_message(sender_id, _build_rejected_retry_message(kyc_check))
            get_or_create_session(sender_id)
            return

    # [4] Call ADK agent
    get_or_create_session(sender_id)
    try:
        response_text = call_adk_agent(sender_id, text)
        guard_result = guardrails.validate_output(response_text)
        if not guard_result.get('valid', True):
            response_text = "ขออภัย ระบบตรวจพบเนื้อหาที่ไม่เหมาะสม กรุณาลองใหม่"
        messenger_bot.send_text_message(sender_id, response_text)
    except Exception as e:
        print(f"Messenger error: {e}")
        messenger_bot.send_text_message(sender_id, f"เกิดข้อผิดพลาด: {str(e)}")


def _handle_messenger_image(sender_id: str, image_url: str):
    """Download image from Facebook CDN and pass to ADK agent"""
    import uuid
    get_or_create_session(sender_id)
    tmp = Path(tempfile.gettempdir()) / f"messenger_{uuid.uuid4().hex}.jpg"
    if messenger_bot.download_image(image_url, str(tmp)):
        messenger_bot.send_text_message(sender_id, "📸 ได้รับรูปภาพแล้ว กำลังประมวลผล...")
        try:
            response_text = call_adk_agent(sender_id, "ส่งรูปภาพ", image_path=str(tmp))
            messenger_bot.send_text_message(sender_id, response_text)
        finally:
            tmp.unlink(missing_ok=True)
    else:
        messenger_bot.send_text_message(sender_id, "ไม่สามารถรับรูปภาพได้ กรุณาลองใหม่")


def _send_messenger_badge(sender_id: str, kyc_check: dict):
    """Send Trust Badge card via Messenger Generic Template"""
    rec = kyc_check.get('record')
    parts = [p for p in [rec.prefix, rec.first_name, rec.last_name] if p] if rec else []
    display_name = ' '.join(parts) or None
    issued = rec.created_at.strftime('%d/%m/%Y') if rec and rec.created_at else None
    badge_level = (kyc_check.get('trust_badge') or 'bronze').lower()
    _score = kyc_check.get('risk_score') or (rec.risk_score if rec else 0) or 0
    messenger_bot.send_badge_card(sender_id, badge_level, _score,
                                   name=display_name, issued_date=issued)


if __name__ == '__main__':
    # Use port 5001 to avoid conflict with ADK server (port 8000) or AirPlay (port 5000)
    PORT = 5001

    print("=" * 60)
    print("QuickChat ID LINE Bot Server v2.0.0")
    print("=" * 60)
    print(f"✓ LINE Channel configured")
    print(f"✓ Webhook endpoints:")
    print(f"  - /webhook/line (default)")
    print(f"  - /webhook-test/line-bot (alternative)")
    print(f"✓ Health check: /health")
    print(f"\n🏢 Enterprise Services:")
    print(f"   - OPA Policy Engine: {'✅ Real' if opa.available else '⚡ Mock'}")
    print(f"   - Presidio PII Masking: {'✅ Real' if presidio.available else '⚡ Mock'}")
    print(f"   - Telemetry/Tracing: {'✅ Real' if telemetry.available else '⚡ Mock'}")
    print(f"   - Guardrails: ✅ Active")
    print(f"   - Keycloak IAM: {'✅ Real' if keycloak.available else '⚡ Mock'}")
    print("=" * 60)
    print(f"\n🚀 Starting server on http://0.0.0.0:{PORT}")
    print(f"\n📱 Your ngrok URL:")
    print(f"   https://nongraceful-ryann-gawsy.ngrok-free.dev")
    print(f"\n✅ Webhook URL for LINE Developer Console:")
    print(f"   https://nongraceful-ryann-gawsy.ngrok-free.dev/webhook-test/line-bot")
    print("=" * 60)

    # Run Flask app
    app.run(host='0.0.0.0', port=PORT, debug=True)
