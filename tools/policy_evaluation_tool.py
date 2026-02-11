"""Policy Evaluation Tool"""

from typing import Dict, Any

def evaluate_document_risk(ocr_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate document authenticity risk from OCR data.

    Args:
        ocr_data: OCR extraction results containing confidence and extracted fields

    Returns:
        Document risk evaluation with risk_score, authenticity, and fraud indicators
    """
    confidence = ocr_data.get('confidence', 0.9)

    # Calculate risk score based on OCR confidence
    risk_score = confidence * 100

    return {
        'risk_score': round(risk_score, 1),
        'authenticity': 'verified' if confidence > 0.7 else 'suspicious',
        'fraud_indicators': [] if confidence > 0.7 else ['low_confidence'],
        'message': f"Document verified with {risk_score:.1f}% confidence"
    }

def evaluate_biometric_risk(
    liveness_result: Dict[str, Any],
    deepfake_result: Dict[str, Any],
    face_match_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate biometric verification risk.

    Args:
        liveness_result: Liveness detection result with is_live and liveness_score
        deepfake_result: Deepfake detection result with is_fake and deepfake_probability
        face_match_result: Face matching result with similarity_score and match status

    Returns:
        Biometric risk evaluation with overall risk_score and trust_level
    """
    # Extract scores
    liveness_score = liveness_result.get('liveness_score', 0.5)
    is_live = liveness_result.get('is_live', False)

    deepfake_prob = deepfake_result.get('deepfake_probability', 0.5)
    is_fake = deepfake_result.get('is_fake', True)

    face_similarity = face_match_result.get('similarity_score', 0.0)
    face_match = face_match_result.get('match', False)

    # Calculate weighted biometric score
    # Liveness: 30%, Deepfake: 30%, Face Match: 40%
    liveness_component = liveness_score if is_live else 0.0
    deepfake_component = (1 - deepfake_prob) if not is_fake else 0.0
    face_component = face_similarity if face_match else 0.0

    biometric_score = (
        liveness_component * 0.30 +
        deepfake_component * 0.30 +
        face_component * 0.40
    ) * 100

    # Determine trust level
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
    """
    General risk evaluation (legacy function).

    Args:
        data: Mixed verification data

    Returns:
        Risk evaluation results
    """
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

    Args:
        document_risk: Document risk evaluation result
        biometric_risk: Biometric risk evaluation result
        scam_score: Scam detection score (0-1, higher = more suspicious)

    Returns:
        Final decision with overall risk_score, trust_level, and approval status
    """
    # Extract component scores
    doc_score = document_risk.get('risk_score', 0) / 100
    bio_score = biometric_risk.get('risk_score', 0) / 100
    scam_component = 1 - scam_score

    # Calculate weighted final score
    # Document: 35%, Biometric: 55%, Scam check: 10%
    final_score = (
        doc_score * 0.35 +
        bio_score * 0.55 +
        scam_component * 0.10
    ) * 100

    # Determine trust level
    if final_score >= 96:
        trust = 'platinum'
    elif final_score >= 81:
        trust = 'gold'
    elif final_score >= 61:
        trust = 'silver'
    else:
        trust = 'bronze'

    return {
        'risk_score': round(final_score, 1),
        'trust_level': trust,
        'allow': final_score >= 50,
        'document_score': round(doc_score * 100, 1),
        'biometric_score': round(bio_score * 100, 1),
        'scam_score': round(scam_score * 100, 1),
        'message': f"Final Decision: {trust.upper()} badge with {final_score:.1f}% confidence"
    }
