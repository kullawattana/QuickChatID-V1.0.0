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

    try:
        # Generate user_id if not provided
        if not user_id:
            # Try to extract from personal_info or ocr_data
            if personal_info and 'phone' in personal_info:
                user_id = f"user_{personal_info['phone']}"
            elif ocr_data and 'thai_id_card' in ocr_data:
                id_num = ocr_data['thai_id_card'].get('id_number')
                if id_num:
                    user_id = f"user_{id_num}"
            else:
                # Generate temporary user_id
                import time
                user_id = f"kyc_user_{int(time.time())}"

            print(f"⚠️  Generated user_id: {user_id}")

        # Extract personal information
        prefix = None
        first_name = None
        last_name = None
        id_number = None
        date_of_birth = None
        address = None

        if ocr_data and 'thai_id_card' in ocr_data:
            thai_id = ocr_data['thai_id_card']
            prefix = thai_id.get('prefix')
            first_name = thai_id.get('first_name')
            last_name = thai_id.get('last_name')
            id_number = thai_id.get('id_number')
            date_of_birth = thai_id.get('date_of_birth')
            address = thai_id.get('address')

        # If not from OCR, try from personal_info
        if personal_info and not first_name:
            full_name = personal_info.get('name', '')
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:])

        # Extract face matching scores
        face_similarity_score = None
        face_confidence = None

        if face_match_result:
            # Get similarity score (convert from 0-1 to 0-100 if needed)
            similarity_raw = face_match_result.get('similarity_score')
            if similarity_raw is not None:
                # AWS returns 0-1 range, convert to 0-100
                if similarity_raw <= 1.0:
                    face_similarity_score = similarity_raw * 100
                else:
                    face_similarity_score = similarity_raw

            # Get confidence (convert string to numeric)
            confidence_raw = face_match_result.get('confidence')
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

        # Extract image paths/URLs
        id_card_image_path = None
        selfie_image_path = None

        if ocr_data:
            id_card_image_path = ocr_data.get('image_path')

        if face_match_result:
            selfie_image_path = face_match_result.get('target_image')

        # Determine verification status
        status = 'pending'
        is_verified = False
        verification_result = None

        if final_decision:
            allow = final_decision.get('allow', False)
            risk_score = final_decision.get('risk_score', 0)

            if allow and risk_score >= 80:
                status = 'approved'
                is_verified = True
            elif allow and risk_score >= 50:
                status = 'approved'
                is_verified = True
            elif scam_score > 0.7:
                status = 'rejected'
                verification_result = 'Rejected: High scam risk detected'
            elif risk_score < 50:
                status = 'rejected'
                verification_result = f'Rejected: Low confidence ({risk_score}%)'
            else:
                status = 'failed'
                verification_result = 'Verification failed'

            if is_verified:
                verification_result = final_decision.get('message', 'Verification successful')

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
            'is_verified': is_verified
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
