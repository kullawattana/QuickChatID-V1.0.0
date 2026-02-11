"""Service Integration Examples"""

from services.guardrails_service import get_guardrails_service
from services.opa_service import get_opa_service
from services.presidio_service import get_presidio_service
from services.keycloak_service import get_keycloak_service
from services.telemetry_service import get_telemetry_service

guardrails = get_guardrails_service()
opa = get_opa_service()
presidio = get_presidio_service()
keycloak = get_keycloak_service()
telemetry = get_telemetry_service()

def complete_kyc_flow(user_data: dict):
    """Complete KYC with all services"""
    
    with telemetry.trace_span("kyc.complete_flow", {"user_id": user_data['user_id']}):
        # 1. Validate
        validation = guardrails.validate_output(user_data['user_message'])
        if not validation['passed']:
            return {'success': False, 'reason': 'Validation failed'}
        
        # 2. Mask PII
        masked = presidio.anonymize(f"{user_data['name']} {user_data['phone']}")
        
        # 3. Evaluate risk
        decision = opa.evaluate_policy("kyc/risk", user_data)
        
        if not decision['allow']:
            return {'success': False, 'reasons': decision['block_reasons']}
        
        # 4. Create user & assign role
        keycloak.create_user({'username': user_data['user_id']})
        keycloak.assign_role(user_data['user_id'], f"{decision['trust_level']}_user")
        
        # 5. Issue badge
        from tools.trust_badge_tool import issue_trust_badge
        badge = issue_trust_badge(decision['trust_level'], decision['risk_score'])
        
        return {
            'success': True,
            'trust_level': decision['trust_level'],
            'jwt_token': badge['jwt_token']
        }

if __name__ == "__main__":
    test_user = {
        'user_id': 'user_123',
        'name': 'สมชาย ใจดี',
        'phone': '0812345678',
        'user_message': 'พร้อมครับ',
        'face_match_score': 0.95,
        'liveness_score': 0.92,
        'deepfake_probability': 0.05,
        'ocr_confidence': 0.98,
        'scam_score': 0.10
    }
    
    result = complete_kyc_flow(test_user)
    print("Result:", result)
