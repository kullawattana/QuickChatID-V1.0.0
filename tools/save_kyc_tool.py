"""
Save KYC Tool
Saves KYC verification results to database
"""

from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import database
try:
    from database import KYCRepository
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Database not available: {e}")
    DATABASE_AVAILABLE = False


def save_kyc_record(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    personal_info: Optional[Dict[str, Any]] = None,
    ocr_data: Optional[Dict[str, Any]] = None,
    face_match_result: Optional[Dict[str, Any]] = None,
    liveness_result: Optional[Dict[str, Any]] = None,
    deepfake_result: Optional[Dict[str, Any]] = None,
    document_risk: Optional[Dict[str, Any]] = None,
    biometric_risk: Optional[Dict[str, Any]] = None,
    final_decision: Optional[Dict[str, Any]] = None,
    trust_badge: Optional[Dict[str, Any]] = None,
    scam_score: float = 0.0
) -> Dict[str, Any]:
    """
    Save KYC verification record to database.

    Args:
        user_id: LINE user ID or unique user identifier
        session_id: ADK session ID (optional)
        personal_info: Dict containing name, phone, email
        ocr_data: Thai ID OCR extraction results
        face_match_result: Face matching results from AWS Rekognition
        liveness_result: Liveness detection results
        deepfake_result: Deepfake detection results
        document_risk: Document risk evaluation
        biometric_risk: Biometric risk evaluation
        final_decision: Final KYC decision
        trust_badge: Issued trust badge
        scam_score: Scam detection score

    Returns:
        Confirmation with record ID and status
    """
    if not DATABASE_AVAILABLE:
        return {
            'success': False,
            'error': 'Database not available',
            'message': 'KYC completed but not saved to database (database module not available)'
        }

    def _unwrap(d: Optional[Dict]) -> Optional[Dict]:
        """
        ADK wraps tool results as {"tool_name_response": {...actual data...}}
        when agents pass them between tools. Unwrap one level if needed.
        """
        if not isinstance(d, dict):
            return d
        # If exactly one key ending with '_response', unwrap it
        if len(d) == 1:
            key = next(iter(d))
            if key.endswith('_response') and isinstance(d[key], dict):
                return d[key]
        return d

    try:
        # Unwrap all ADK-wrapped tool responses up front
        ocr_data        = _unwrap(ocr_data)
        face_match_result = _unwrap(face_match_result)
        liveness_result = _unwrap(liveness_result)
        deepfake_result = _unwrap(deepfake_result)
        document_risk   = _unwrap(document_risk)
        biometric_risk  = _unwrap(biometric_risk)
        final_decision  = _unwrap(final_decision)
        trust_badge     = _unwrap(trust_badge)

        # Generate user_id if not provided
        if not user_id:
            if personal_info and 'phone' in personal_info:
                user_id = f"user_{personal_info['phone']}"
            elif ocr_data and ocr_data.get('id_number'):
                user_id = f"user_{ocr_data['id_number']}"
            else:
                import time
                user_id = f"kyc_user_{int(time.time())}"
            print(f"⚠️  Generated user_id: {user_id}")

        # ── Extract OCR fields ────────────────────────────────────────
        # extract_thai_id returns: id_number, name_th, name_en,
        #                          date_of_birth, address, confidence_score
        prefix = None
        first_name = None
        last_name = None
        id_number = None
        date_of_birth = None
        address = None

        if ocr_data:
            id_number     = ocr_data.get('id_number')
            date_of_birth = ocr_data.get('date_of_birth')
            address       = ocr_data.get('address')

            # Parse Thai name → prefix / first_name / last_name
            name_th = ocr_data.get('name_th', '')
            if name_th:
                thai_prefixes = ['นาย', 'นาง', 'นางสาว', 'ด.ช.', 'ด.ญ.', 'Mr.', 'Mrs.', 'Miss']
                parts = name_th.strip().split()
                if parts and any(parts[0] == p for p in thai_prefixes):
                    prefix = parts[0]
                    if len(parts) >= 3:
                        first_name = parts[1]
                        last_name  = ' '.join(parts[2:])
                    elif len(parts) == 2:
                        first_name = parts[1]
                else:
                    if len(parts) >= 2:
                        first_name = parts[0]
                        last_name  = ' '.join(parts[1:])
                    elif parts:
                        first_name = parts[0]

            print(f"✅ OCR extracted: id={id_number}, name={prefix} {first_name} {last_name}")

        # If name still missing, try personal_info
        if personal_info and not first_name:
            full_name = personal_info.get('name', '')
            parts = full_name.split()
            if len(parts) >= 2:
                first_name = parts[0]
                last_name  = ' '.join(parts[1:])

        # ── Extract face matching scores ──────────────────────────────
        face_similarity_score = None
        face_confidence = None

        if face_match_result:
            similarity_raw = face_match_result.get('similarity_score')
            if similarity_raw is not None:
                face_similarity_score = similarity_raw * 100 if similarity_raw <= 1.0 else similarity_raw

            confidence_raw = face_match_result.get('confidence')
            if confidence_raw:
                if isinstance(confidence_raw, str):
                    face_confidence = {'high': 95.0, 'medium': 75.0, 'low': 50.0}.get(confidence_raw.lower(), 75.0)
                else:
                    face_confidence = float(confidence_raw)
            print(f"✅ Face match: similarity={face_similarity_score}, confidence={face_confidence}")

        # ── Image paths ───────────────────────────────────────────────
        id_card_image_path = ocr_data.get('image_path') if ocr_data else None
        selfie_image_path  = face_match_result.get('target_image') if face_match_result else None

        # ── Determine verification status ─────────────────────────────
        status = 'pending'
        is_verified = False
        verification_result = None

        if final_decision:
            allow      = final_decision.get('allow', False)
            risk_score = float(final_decision.get('risk_score', 0))

            import os as _os
            _approval_min = float(_os.getenv('KYC_APPROVAL_MIN_SCORE', '50'))
            _scam_block   = float(_os.getenv('SCAM_BLOCK_THRESHOLD',   '0.7'))

            if allow and risk_score >= _approval_min:
                status      = 'approved'
                is_verified = True
            elif scam_score > _scam_block:
                status = 'rejected'
                verification_result = 'Rejected: High scam risk detected'
            elif risk_score < _approval_min:
                status = 'rejected'
                verification_result = f'Rejected: Low confidence ({risk_score:.0f}%)'
            else:
                status = 'failed'
                verification_result = 'Verification failed'

            if is_verified:
                verification_result = final_decision.get('message', 'Verification successful')

            print(f"✅ Final decision: allow={allow}, risk={risk_score}, status={status}")

        # ── Extract trust_level and risk_score ────────────────────────
        trust_level_str = ''
        risk_score_val  = None

        if trust_badge and isinstance(trust_badge, dict):
            trust_level_str = trust_badge.get('trust_level', '')
            if 'risk_score' in trust_badge:
                risk_score_val = float(trust_badge['risk_score'])

        if risk_score_val is None and final_decision and isinstance(final_decision, dict):
            if 'risk_score' in final_decision:
                risk_score_val = float(final_decision['risk_score'])

        # Detect platform from user_id pattern
        if user_id.startswith('U') and len(user_id) > 10:
            platform = 'line'
        elif user_id.isdigit():
            platform = 'messenger'
        elif user_id.startswith('WEB_') or user_id.startswith('web_'):
            platform = 'web'
        else:
            platform = 'line'

        # Build complete data
        record_data = {
            'user_id': user_id,
            'session_id': session_id,
            'id_number': id_number,
            'prefix': prefix,
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': date_of_birth,
            'address': address,
            'id_card_data': ocr_data,
            'face_similarity_score': face_similarity_score,
            'face_confidence': face_confidence,
            'rekognition_data': face_match_result,
            'id_card_image_path': id_card_image_path,
            'selfie_image_path': selfie_image_path,
            'status': status,
            'verification_result': verification_result,
            'is_verified': is_verified,
            'platform': platform,
            'risk_score': risk_score_val,
            'trust_level': trust_level_str.lower() if trust_level_str else None,
            'notes': f"trust_level:{trust_level_str}" if trust_level_str else None
        }

        # Save to database
        record = KYCRepository.create_kyc_record(**record_data)

        return {
            'success': True,
            'record_id': record.id,
            'status': status,
            'is_verified': is_verified,
            'message': f'✅ KYC record saved successfully (ID: {record.id})'
        }

    except Exception as e:
        print(f"❌ Error saving KYC record: {e}")
        import traceback
        traceback.print_exc()

        return {
            'success': False,
            'error': str(e),
            'message': f'KYC completed but failed to save to database: {str(e)}'
        }
