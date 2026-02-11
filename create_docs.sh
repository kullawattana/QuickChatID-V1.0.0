#!/bin/bash

mkdir -p docs

# Implementation guide
cat > docs/IMPLEMENTATION.md << 'EOF'
# QuickChat ID - Implementation Guide

## Architecture Overview

```
User → ADK Web UI → Root Agent → Sub-Agents → Tools → Services
```

## Agent Flow

### 1. kyc_orchestrator (Root Agent)
- **Role**: Orchestrates entire KYC process
- **Responsibilities**:
  - Route to appropriate sub-agents
  - Maintain session state
  - Make final decisions
  - Issue trust badges

### 2. welcome_agent
- **Role**: Welcome & consent
- **Flow**:
  1. Greet user
  2. Explain 4-step process
  3. Request PDPA consent
  4. Transfer to personal_info_agent

### 3. personal_info_agent
- **Role**: Collect personal data
- **Tools Used**: `check_scam_intent`
- **Flow**:
  1. Request: name, phone, email
  2. Validate format
  3. Check for scam patterns
  4. Transfer to document_verify_agent

### 4. document_verify_agent
- **Role**: Verify Thai ID card
- **Tools Used**: `extract_thai_id`, `evaluate_document_risk`
- **Flow**:
  1. Guide photo taking
  2. Run OCR extraction
  3. Validate ID number
  4. Check expiry
  5. Transfer to biometric_verify_agent

### 5. biometric_verify_agent
- **Role**: Face verification
- **Tools Used**: `match_faces`, `detect_liveness`, `detect_deepfake`, `evaluate_biometric_risk`
- **Flow**:
  1. Guide selfie capture
  2. Detect liveness (>0.7)
  3. Detect deepfakes (<0.3)
  4. Match with ID photo (>0.85)
  5. Transfer back to orchestrator

### 6. Final Decision (orchestrator)
- **Tools Used**: `evaluate_final_decision`, `issue_trust_badge`
- **Flow**:
  1. Combine all data
  2. Calculate risk score
  3. Determine trust level
  4. Issue JWT certificate
  5. Display results

## Tool Details

### check_scam_intent
- Pattern-based + ML (WangchanBERTa)
- Detects: money requests, OTP, urgency, threats
- Returns: scam_score (0-1), indicators, risk_level

### extract_thai_id
- PaddleOCR for Thai text
- Extracts: ID number, name, dates
- Validates: checksum, format
- Returns: confidence score

### match_faces
- InsightFace for embeddings
- Cosine similarity comparison
- Checks: age, gender consistency
- Returns: similarity score (0-1)

### detect_liveness
- MediaPipe face mesh
- 3D depth analysis
- Texture patterns
- Returns: liveness score (0-1)

### detect_deepfake
- Deep learning model
- Artifact detection
- Returns: fake probability (0-1)

### evaluate_final_decision
- Combines all scores
- Weighted calculation:
  - Face match: 30%
  - Liveness: 25%
  - Deepfake: 20%
  - OCR: 15%
  - Scam: 10%
- Returns: trust_level, risk_score

### issue_trust_badge
- Generates JWT token
- Includes: level, score, limits, benefits, expiry
- Valid for 1 year

## Trust Levels

| Level | Score | Transaction Limit | Benefits |
|-------|-------|-------------------|----------|
| Bronze | 50-60 | ฿10,000 | Basic verification |
| Silver | 61-80 | ฿50,000 | Enhanced + priority |
| Gold | 81-95 | ฿100,000 | Premium + waived fees |
| Platinum | 96-100 | Unlimited | VIP + zero fees |

## Error Handling

### Scam Detected (score > 0.7)
- Block immediately
- Log incident
- Notify admin

### Low Confidence (<50%)
- Reject verification
- Request retry
- Suggest manual review

### Technical Errors
- Graceful degradation
- Mock data fallback
- User-friendly messages

## Testing Strategy

### Unit Tests
- Test each tool independently
- Mock external services
- Verify edge cases

### Integration Tests
- Test agent flows
- Test tool chaining
- Verify state management

### E2E Tests
- Full KYC flow
- Happy path
- Error scenarios

## Deployment

### Local Development
```bash
cd agents
adk web
```

### Cloud Run
```bash
adk deploy --platform=cloud-run --project=PROJECT_ID
```

### Vertex AI
```bash
adk deploy --platform=vertex-ai --project=PROJECT_ID --region=REGION
```

## Configuration

### Environment Variables
- `GOOGLE_GENAI_API_KEY`: Gemini API key
- `OPA_URL`: OPA server URL
- `JWT_SECRET_KEY`: JWT signing key
- `LOG_LEVEL`: Logging level

### Agent Configuration
- `temperature`: 0.6-0.8 (creativity)
- `max_tokens`: 1024-2048 (response length)
- `streaming`: true (real-time)

## Best Practices

### Security
- ✅ Encrypt all PII
- ✅ Use HTTPS only
- ✅ Validate all inputs
- ✅ Rate limit requests
- ✅ Audit all actions

### Performance
- ✅ Cache model weights
- ✅ Use GPU when available
- ✅ Async processing
- ✅ Connection pooling

### Reliability
- ✅ Graceful degradation
- ✅ Retry logic
- ✅ Circuit breakers
- ✅ Health checks

### Observability
- ✅ Structured logging
- ✅ Metrics collection
- ✅ Distributed tracing
- ✅ Error tracking

## Troubleshooting

### Agent not responding
- Check API key
- Verify network connectivity
- Check quotas/limits

### Tools failing
- Check service availability
- Verify dependencies installed
- Check file permissions

### Low accuracy
- Improve image quality
- Adjust thresholds
- Fine-tune models

## Next Steps

1. Fine-tune scam detection model
2. Add more document types
3. Implement real OPA policies
4. Add monitoring dashboard
5. Enable production logging
EOF

# API documentation
cat > docs/API.md << 'EOF'
# QuickChat ID - API Reference

## Agent API

### Root Agent: kyc_orchestrator

```python
from agents.kyc_orchestrator.agent import root_agent

# Access via ADK
# No direct API calls needed - use ADK web interface
```

## Tools API

### check_scam_intent

```python
from tools.scam_detection import check_scam_intent

result = check_scam_intent(text="ข้อความที่ต้องการตรวจสอบ")

# Returns:
{
    'scam_score': 0.15,        # 0-1
    'is_scam': False,          # bool
    'confidence': 0.85,        # 0-1
    'indicators': [],          # List[str]
    'risk_level': 'low',       # low|medium|high|critical
    'message': 'Detected 0 scam indicators'
}
```

### extract_thai_id

```python
from tools.ocr_tool import extract_thai_id

result = extract_thai_id(image_path="/path/to/id_card.jpg")

# Returns:
{
    'id_number': '1234567890123',
    'name_th': 'สมชาย ใจดี',
    'confidence_score': 0.95,
    'success': True,
    'message': 'OCR completed with 95% confidence'
}
```

### match_faces

```python
from tools.face_matching_tool import match_faces

result = match_faces(
    id_card_image="/path/to/id.jpg",
    selfie_image="/path/to/selfie.jpg",
    threshold=0.85
)

# Returns:
{
    'similarity_score': 0.95,
    'match': True,
    'age_diff': 2,
    'gender_match': True,
    'message': 'Face match: 95%'
}
```

### detect_liveness

```python
from tools.liveness_tool import detect_liveness

result = detect_liveness(image_path="/path/to/selfie.jpg")

# Returns:
{
    'liveness_score': 0.92,
    'is_live': True,
    'confidence': 'high',
    'message': 'Liveness: 92%'
}
```

### detect_deepfake

```python
from tools.deepfake_tool import detect_deepfake

result = detect_deepfake(image_path="/path/to/image.jpg")

# Returns:
{
    'deepfake_probability': 0.05,
    'is_fake': False,
    'confidence': 0.95,
    'message': 'Deepfake probability: 5%'
}
```

### evaluate_final_decision

```python
from tools.policy_evaluation_tool import evaluate_final_decision

result = evaluate_final_decision({
    'face_match_score': 0.95,
    'liveness_score': 0.92,
    'deepfake_probability': 0.05,
    'ocr_confidence': 0.98,
    'scam_score': 0.10
})

# Returns:
{
    'risk_score': 94.5,
    'trust_level': 'gold',
    'allow': True,
    'message': 'Final decision: GOLD badge with 94.5% confidence'
}
```

### issue_trust_badge

```python
from tools.trust_badge_tool import issue_trust_badge

badge = issue_trust_badge(
    trust_level='gold',
    risk_score=94.5,
    user_data={'id': 'user123'}
)

# Returns:
{
    'jwt_token': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
    'trust_level': 'gold',
    'risk_score': 94.5,
    'transaction_limit': 100000,
    'benefits': ['Premium verification', 'Fast-track', ...],
    'expires_at': '2026-01-30T12:00:00',
    'message': 'Trust badge issued: GOLD'
}
```

## Data Structures

### UserData
```python
{
    'full_name': str,        # ชื่อ-นามสกุล
    'phone': str,            # เบอร์โทร 10 หลัก
    'email': str,            # อีเมล
    'consent_given': bool    # ความยินยอม PDPA
}
```

### DocumentData
```python
{
    'id_number': str,        # เลขบัตร 13 หลัก
    'name_th': str,          # ชื่อภาษาไทย
    'date_of_birth': str,    # วันเกิด
    'expiry_date': str,      # วันหมดอายุ
    'ocr_confidence': float  # ความมั่นใจ OCR
}
```

### BiometricData
```python
{
    'face_match_score': float,      # 0-1
    'liveness_score': float,        # 0-1
    'deepfake_probability': float,  # 0-1
    'age_estimated': int,           # อายุประมาณการ
    'gender_detected': str          # M/F
}
```

## Error Codes

| Code | Description | Action |
|------|-------------|--------|
| SCAM_DETECTED | Scam score > 0.7 | Block user |
| LOW_CONFIDENCE | Confidence < 0.5 | Request retry |
| NO_FACE_DETECTED | Face not found | Guide user |
| ID_EXPIRED | ID card expired | Reject |
| DEEPFAKE_DETECTED | Fake probability > 0.7 | Block user |
| API_ERROR | Service unavailable | Retry later |

## Rate Limits

- API calls: 100/minute/user
- OCR requests: 20/minute/user
- Face matching: 50/minute/user

## Authentication

JWT tokens are issued after successful verification:

```python
import jwt

# Decode token
payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

# Verify
if payload['expires_at'] > now():
    # Token valid
    trust_level = payload['trust_level']
    transaction_limit = payload['transaction_limit']
```
EOF

echo "✓ Documentation created!"

