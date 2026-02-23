"""Policy Evaluation Tool"""

import os
from typing import Dict, Any

def _unwrap(d):
    """Unwrap ADK tool response wrapper: {"tool_name_response": {...}} → {...}"""
    if not isinstance(d, dict):
        return d or {}
    if len(d) == 1:
        key = next(iter(d))
        if key.endswith('_response') and isinstance(d[key], dict):
            return d[key]
    return d

# ─── Thresholds (configurable via environment variables) ──────────────────────
OCR_CONFIDENCE_THRESHOLD  = float(os.getenv('OCR_CONFIDENCE_THRESHOLD', '0.7'))

WEIGHT_LIVENESS    = float(os.getenv('WEIGHT_LIVENESS',   '0.30'))
WEIGHT_DEEPFAKE    = float(os.getenv('WEIGHT_DEEPFAKE',   '0.30'))
WEIGHT_FACE_MATCH  = float(os.getenv('WEIGHT_FACE_MATCH', '0.40'))

BADGE_PLATINUM_THRESHOLD = float(os.getenv('BADGE_PLATINUM_THRESHOLD', '96'))
BADGE_GOLD_THRESHOLD     = float(os.getenv('BADGE_GOLD_THRESHOLD',     '81'))
BADGE_SILVER_THRESHOLD   = float(os.getenv('BADGE_SILVER_THRESHOLD',   '61'))
KYC_APPROVAL_MIN_SCORE   = float(os.getenv('KYC_APPROVAL_MIN_SCORE',   '50'))

WEIGHT_DOCUMENT   = float(os.getenv('WEIGHT_DOCUMENT',  '0.35'))
WEIGHT_BIOMETRIC  = float(os.getenv('WEIGHT_BIOMETRIC', '0.55'))
WEIGHT_SCAM       = float(os.getenv('WEIGHT_SCAM',      '0.10'))
# ─────────────────────────────────────────────────────────────────────────────


def evaluate_document_risk(ocr_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate document authenticity risk from OCR data.
    """
    ocr_data = _unwrap(ocr_data)
    confidence = ocr_data.get('confidence_score', ocr_data.get('confidence', 0.9))
    risk_score = confidence * 100

    return {
        'risk_score': round(risk_score, 1),
        'authenticity': 'verified' if confidence > OCR_CONFIDENCE_THRESHOLD else 'suspicious',
        'fraud_indicators': [] if confidence > OCR_CONFIDENCE_THRESHOLD else ['low_confidence'],
        'message': f"Document verified with {risk_score:.1f}% confidence"
    }


def evaluate_biometric_risk(
    liveness_result: Dict[str, Any],
    deepfake_result: Dict[str, Any],
    face_match_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate biometric verification risk.
    """
    liveness_result   = _unwrap(liveness_result)
    deepfake_result   = _unwrap(deepfake_result)
    face_match_result = _unwrap(face_match_result)

    liveness_score = liveness_result.get('liveness_score', 0.5)
    is_live        = liveness_result.get('is_live', False)

    deepfake_prob  = deepfake_result.get('deepfake_probability', 0.5)
    is_fake        = deepfake_result.get('is_fake', True)

    face_similarity = face_match_result.get('similarity_score', 0.0)
    face_match      = face_match_result.get('match', False)

    print(f"📊 Biometric inputs (unwrapped): liveness={liveness_score:.2f}(live={is_live}), "
          f"deepfake_prob={deepfake_prob:.2f}(fake={is_fake}), face_sim={face_similarity:.3f}(match={face_match})")

    liveness_component  = liveness_score if is_live else 0.0
    deepfake_component  = (1 - deepfake_prob) if not is_fake else 0.0
    face_component      = face_similarity if face_match else 0.0

    biometric_score = (
        liveness_component * WEIGHT_LIVENESS +
        deepfake_component * WEIGHT_DEEPFAKE +
        face_component     * WEIGHT_FACE_MATCH
    ) * 100

    # Biometric trust level (intermediate, before final decision)
    if biometric_score >= 90:
        trust = 'gold'
    elif biometric_score >= 75:
        trust = 'silver'
    else:
        trust = 'bronze'

    return {
        'risk_score': round(biometric_score, 1),
        'trust_level': trust,
        'liveness_pass': is_live,
        'deepfake_pass': not is_fake,
        'face_match_pass': face_match,
        'message': f"Biometric verified: {trust.upper()} level ({biometric_score:.1f}%)"
    }


def evaluate_risk(data: Dict[str, Any]) -> Dict[str, Any]:
    """General risk evaluation (legacy)."""
    return {
        'risk_score': 85,
        'trust_level': 'silver',
        'message': "Risk evaluation complete"
    }


def evaluate_final_decision(
    document_risk: Dict[str, Any],
    biometric_risk: Dict[str, Any],
    scam_score: float = 0.0
) -> Dict[str, Any]:
    """
    Make final KYC decision based on all verification results.
    """
    document_risk = _unwrap(document_risk)
    biometric_risk = _unwrap(biometric_risk)

    doc_score       = document_risk.get('risk_score', 0) / 100
    bio_score       = biometric_risk.get('risk_score', 0) / 100

    print(f"📊 Final decision inputs: doc={doc_score*100:.1f}%, bio={bio_score*100:.1f}%, scam={scam_score:.2f}")
    scam_component  = 1 - scam_score

    final_score = (
        doc_score      * WEIGHT_DOCUMENT  +
        bio_score      * WEIGHT_BIOMETRIC +
        scam_component * WEIGHT_SCAM
    ) * 100

    if final_score >= BADGE_PLATINUM_THRESHOLD:
        trust = 'platinum'
    elif final_score >= BADGE_GOLD_THRESHOLD:
        trust = 'gold'
    elif final_score >= BADGE_SILVER_THRESHOLD:
        trust = 'silver'
    else:
        trust = 'bronze'

    return {
        'risk_score': round(final_score, 1),
        'trust_level': trust,
        'allow': final_score >= KYC_APPROVAL_MIN_SCORE,
        'document_score': round(doc_score * 100, 1),
        'biometric_score': round(bio_score * 100, 1),
        'scam_score': round(scam_score * 100, 1),
        'message': f"Final Decision: {trust.upper()} badge with {final_score:.1f}% confidence"
    }
