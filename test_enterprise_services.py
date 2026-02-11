#!/usr/bin/env python3
"""
Test All 5 Enterprise Services
Tests: OPA, Presidio, Telemetry, Guardrails, Keycloak
"""
import sys
import os
import time
import json
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []


def record(service, test_name, passed, detail=""):
    results.append({"service": service, "test": test_name, "passed": passed, "detail": detail})
    status = PASS if passed else FAIL
    print(f"  {status} {test_name}" + (f" — {detail}" if detail else ""))


def test_opa_service():
    """Test OPA Policy Engine"""
    print("\n" + "=" * 60)
    print("🏛️  1/5  OPA Policy Engine")
    print("=" * 60)

    from services.opa_service import get_opa_service
    opa = get_opa_service()

    # Test 1: Service initialization
    record("OPA", "Service initialized", opa is not None)

    # Test 2: High-trust scenario (good scores)
    result = opa.evaluate_policy("kyc/risk_assessment", {
        'face_match_score': 0.98,
        'liveness_score': 0.95,
        'deepfake_probability': 0.02,
        'ocr_confidence': 0.95,
        'scam_score': 0.05
    })
    record("OPA", "High-trust → platinum",
           result.get('trust_level') == 'platinum',
           f"score={result.get('risk_score')}, level={result.get('trust_level')}")

    # Test 3: Medium-trust scenario
    result = opa.evaluate_policy("kyc/risk_assessment", {
        'face_match_score': 0.75,
        'liveness_score': 0.80,
        'deepfake_probability': 0.15,
        'ocr_confidence': 0.85,
        'scam_score': 0.20
    })
    record("OPA", "Medium-trust → gold/silver",
           result.get('trust_level') in ('gold', 'silver'),
           f"score={result.get('risk_score')}, level={result.get('trust_level')}")

    # Test 4: Low-trust / blocked scenario
    result = opa.evaluate_policy("kyc/risk_assessment", {
        'face_match_score': 0.10,
        'liveness_score': 0.20,
        'deepfake_probability': 0.90,
        'ocr_confidence': 0.30,
        'scam_score': 0.85
    })
    record("OPA", "Low-trust → blocked or bronze",
           result.get('blocked') is True or result.get('trust_level') == 'bronze',
           f"score={result.get('risk_score')}, blocked={result.get('blocked')}")

    # Test 5: Transaction limits
    result_high = opa.evaluate_policy("kyc/risk_assessment", {
        'face_match_score': 0.99, 'liveness_score': 0.99,
        'deepfake_probability': 0.01, 'ocr_confidence': 0.99, 'scam_score': 0.01
    })
    result_low = opa.evaluate_policy("kyc/risk_assessment", {
        'face_match_score': 0.50, 'liveness_score': 0.50,
        'deepfake_probability': 0.30, 'ocr_confidence': 0.60, 'scam_score': 0.30
    })
    high_limit = result_high.get('transaction_limit', 0)
    low_limit = result_low.get('transaction_limit', 0)
    record("OPA", "Transaction limit scaling",
           high_limit > low_limit or high_limit == -1,
           f"platinum={high_limit}, lower={low_limit}")


def test_presidio_service():
    """Test Presidio PII Masking"""
    print("\n" + "=" * 60)
    print("🔒  2/5  Presidio PII Masking")
    print("=" * 60)

    from services.presidio_service import get_presidio_service
    presidio = get_presidio_service()

    # Test 1: Service initialization
    record("Presidio", "Service initialized", presidio is not None)

    # Test 2: Mask Thai phone number
    result = presidio.anonymize("โทร 0812345678 ได้เลย")
    masked = result.get('anonymized_text', result) if isinstance(result, dict) else str(result)
    record("Presidio", "Mask Thai phone number",
           "0812345678" not in masked,
           f"'{masked}'")

    # Test 3: Mask email
    result = presidio.anonymize("ส่งมาที่ test@example.com")
    masked = result.get('anonymized_text', result) if isinstance(result, dict) else str(result)
    record("Presidio", "Mask email address",
           "test@example.com" not in masked,
           f"'{masked}'")

    # Test 4: Mask 13-digit Thai ID
    result = presidio.anonymize("เลขบัตร 1234567890123 ครับ")
    masked = result.get('anonymized_text', result) if isinstance(result, dict) else str(result)
    record("Presidio", "Mask Thai ID number (13 digits)",
           "1234567890123" not in masked,
           f"'{masked}'")

    # Test 5: No PII — should pass through unchanged
    original = "สวัสดีครับ ยินดีต้อนรับ"
    result = presidio.anonymize(original)
    masked = result.get('anonymized_text', result) if isinstance(result, dict) else str(result)
    record("Presidio", "No PII → text unchanged",
           "สวัสดี" in masked,
           f"'{masked}'")

    # Test 6: Analyze (detect PII without masking)
    if hasattr(presidio, 'analyze'):
        entities = presidio.analyze("email: admin@test.com phone: 0999999999")
        entity_types = [e.get('entity_type', '') for e in entities] if isinstance(entities, list) else []
        record("Presidio", "Analyze detects PII entities",
               len(entities) > 0 if isinstance(entities, list) else False,
               f"found: {entity_types}")


def test_telemetry_service():
    """Test Telemetry/Tracing"""
    print("\n" + "=" * 60)
    print("📊  3/5  Telemetry / OpenTelemetry Tracing")
    print("=" * 60)

    from services.telemetry_service import get_telemetry_service
    telemetry = get_telemetry_service()

    # Test 1: Service initialization
    record("Telemetry", "Service initialized", telemetry is not None)

    # Test 2: Create trace span
    telemetry.clear_spans()
    with telemetry.trace_span("test_operation", {"test_key": "test_value"}):
        time.sleep(0.1)  # Simulate work

    spans = telemetry.get_spans()
    record("Telemetry", "trace_span creates span",
           len(spans) >= 1,
           f"spans recorded: {len(spans)}")

    # Test 3: Span has correct name
    if spans:
        last_span = spans[-1]
        record("Telemetry", "Span has correct name",
               last_span.get('name') == 'test_operation',
               f"name='{last_span.get('name')}'")

    # Test 4: Span measures duration
    if spans:
        last_span = spans[-1]
        duration = last_span.get('duration_ms', 0)
        record("Telemetry", "Span measures duration",
               duration >= 50,  # Should be ~100ms
               f"duration={duration:.1f}ms")

    # Test 5: Record event
    telemetry.record_event("test_event", {"event_data": "hello"})
    record("Telemetry", "record_event works", True, "no exception")

    # Test 6: Record metric
    telemetry.record_metric("test_metric", 42.5, "points", {"source": "test"})
    record("Telemetry", "record_metric works", True, "no exception")

    # Test 7: Nested spans
    telemetry.clear_spans()
    with telemetry.trace_span("parent_op"):
        with telemetry.trace_span("child_op"):
            time.sleep(0.05)

    spans = telemetry.get_spans()
    record("Telemetry", "Nested spans recorded",
           len(spans) >= 2,
           f"spans: {[s.get('name') for s in spans]}")


def test_guardrails_service():
    """Test Guardrails LLM Output Validation"""
    print("\n" + "=" * 60)
    print("🛡️  4/5  Guardrails (LLM Output Validation)")
    print("=" * 60)

    from services.guardrails_service import get_guardrails_service
    guardrails = get_guardrails_service()

    # Test 1: Service initialization
    record("Guardrails", "Service initialized", guardrails is not None)

    # Test 2: Clean text passes all validators
    result = guardrails.validate_output("ยินดีต้อนรับสู่ QuickChat ID ครับ")
    passed = result.get('valid', result.get('passed', False))
    record("Guardrails", "Clean text → passes",
           passed is True,
           f"result={result.get('message', 'ok')}")

    # Test 3: Toxic language detected
    result = guardrails.validate_output("ไอ้โง่ ทำไมทำไม่ได้")
    passed = result.get('valid', result.get('passed', True))
    record("Guardrails", "Toxic language → blocked",
           passed is False,
           f"violations={result.get('violations', result.get('validations', {}))}")

    # Test 4: PII leakage detected
    result = guardrails.validate_output("เลขบัตรของคุณคือ 1234567890123")
    passed = result.get('valid', result.get('passed', True))
    record("Guardrails", "PII in output → blocked",
           passed is False,
           f"detected PII leakage")

    # Test 5: Compliance check (sensitive info request)
    result = guardrails.validate_output("กรุณาส่งรหัสผ่านของคุณมา")
    passed = result.get('valid', result.get('passed', True))
    record("Guardrails", "Compliance violation → blocked",
           passed is False,
           f"detected sensitive request")

    # Test 6: Phone number in output detected
    result = guardrails.validate_output("ติดต่อที่ 0891234567 ได้เลย")
    passed = result.get('valid', result.get('passed', True))
    record("Guardrails", "Phone in output → blocked",
           passed is False,
           f"detected phone PII")


def test_keycloak_service():
    """Test Keycloak IAM"""
    print("\n" + "=" * 60)
    print("🔐  5/5  Keycloak IAM")
    print("=" * 60)

    from services.keycloak_service import get_keycloak_service
    keycloak = get_keycloak_service()

    # Test 1: Service initialization
    record("Keycloak", "Service initialized", keycloak is not None)

    # Test 2: Create user
    user_result = keycloak.create_user({
        'username': 'test_user_001',
        'email': 'test@quickchat.id',
        'firstName': 'Test',
        'lastName': 'User'
    })
    record("Keycloak", "Create user",
           user_result.get('success', False) or 'user_id' in user_result,
           f"user_id={user_result.get('user_id', 'N/A')}")

    # Test 3: Assign valid role (bronze)
    user_id = user_result.get('user_id', 'test_user_001')
    role_result = keycloak.assign_role(user_id, 'bronze_user')
    record("Keycloak", "Assign role: bronze_user",
           role_result.get('success', False),
           f"{role_result.get('message', '')}")

    # Test 4: Assign valid role (platinum)
    role_result = keycloak.assign_role(user_id, 'platinum_user')
    record("Keycloak", "Assign role: platinum_user",
           role_result.get('success', False),
           f"{role_result.get('message', '')}")

    # Test 5: Assign invalid role
    role_result = keycloak.assign_role(user_id, 'super_admin_hack')
    record("Keycloak", "Invalid role → rejected",
           role_result.get('success') is False,
           f"{role_result.get('message', '')}")

    # Test 6: Authenticate user
    if hasattr(keycloak, 'authenticate'):
        auth_result = keycloak.authenticate('test_user_001', 'password123')
        has_token = 'access_token' in auth_result
        record("Keycloak", "Authenticate → returns token",
               has_token,
               f"mode={auth_result.get('mode', 'real')}, token={'yes' if has_token else 'no'}")

    # Test 7: Verify token
    if hasattr(keycloak, 'verify_token') and 'access_token' in auth_result:
        verify_result = keycloak.verify_token(auth_result['access_token'])
        record("Keycloak", "Verify token",
               verify_result.get('valid', False) or 'sub' in verify_result,
               f"user={verify_result.get('sub', verify_result.get('username', 'N/A'))}")


def test_integration_via_api():
    """Test all services via the running API"""
    print("\n" + "=" * 60)
    print("🌐  INTEGRATION TEST (via API endpoints)")
    print("=" * 60)

    API = "http://localhost:5003/api"

    # Test 1: Health check shows all services
    try:
        resp = requests.get(f"{API}/health", timeout=5)
        health = resp.json()
        services = health.get('enterprise_services', {})

        record("API", "Health endpoint reachable", resp.status_code == 200)

        for svc in ['opa', 'presidio', 'telemetry', 'guardrails', 'keycloak']:
            status = services.get(svc, 'missing')
            record("API", f"Health → {svc}",
                   status in ('real', 'mock', 'active'),
                   f"status={status}")

    except requests.ConnectionError:
        record("API", "Backend connection", False, "Backend not running on port 5003")
        print("  ⚠️  Start backend first: python web_api_app.py")
        return

    # Test 2: Session init → Telemetry + Keycloak triggered
    resp = requests.post(f"{API}/session/init")
    data = resp.json()
    session_id = data.get('session_id')
    record("API", "Session init (Telemetry + Keycloak)",
           session_id is not None,
           f"session={session_id[:8] if session_id else 'N/A'}...")

    if not session_id:
        return

    # Test 3: Chat message → Guardrails + Presidio triggered
    resp = requests.post(f"{API}/chat/message", json={
        "session_id": session_id,
        "message": "สวัสดีครับ"
    })
    data = resp.json()
    record("API", "Chat message (Guardrails + Presidio)",
           data.get('success', False) or 'response' in data,
           f"response={data.get('response', '')[:60]}...")

    print(f"\n  💡 Full KYC flow (OPA scoring) requires uploading ID card + selfie images")
    print(f"     Use: python test_upload.py  OR  open http://localhost:5173")


def print_summary():
    """Print test summary"""
    print("\n" + "=" * 60)
    print("📋  TEST SUMMARY")
    print("=" * 60)

    by_service = {}
    for r in results:
        svc = r['service']
        if svc not in by_service:
            by_service[svc] = {'pass': 0, 'fail': 0}
        if r['passed']:
            by_service[svc]['pass'] += 1
        else:
            by_service[svc]['fail'] += 1

    total_pass = sum(s['pass'] for s in by_service.values())
    total_fail = sum(s['fail'] for s in by_service.values())

    for svc, counts in by_service.items():
        icon = "✅" if counts['fail'] == 0 else "⚠️"
        print(f"  {icon} {svc:12s}  {counts['pass']} passed, {counts['fail']} failed")

    print(f"\n  {'✅' if total_fail == 0 else '❌'} Total: {total_pass} passed, {total_fail} failed out of {total_pass + total_fail} tests")

    if total_fail == 0:
        print("\n  🎉 All enterprise services are working correctly!")
    else:
        print(f"\n  ⚠️  {total_fail} test(s) need attention")


if __name__ == '__main__':
    print("=" * 60)
    print("🧪  QuickChat ID — Enterprise Services Test Suite")
    print("=" * 60)

    # Unit tests (no server required)
    test_opa_service()
    test_presidio_service()
    test_telemetry_service()
    test_guardrails_service()
    test_keycloak_service()

    # Integration test (requires running backend)
    test_integration_via_api()

    # Summary
    print_summary()
