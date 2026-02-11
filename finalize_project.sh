#!/bin/bash

# Create __init__ files for agents
for agent in welcome_agent personal_info_agent document_verify_agent biometric_verify_agent; do
    cat > "agents/$agent/__init__.py" << EOF
"""$agent package"""
from .agent import ${agent}
__all__ = ['${agent}']
EOF
done

# Create .env.example
cat > .env.example << 'EOF'
# Google AI / Gemini
GOOGLE_GENAI_API_KEY=your-api-key-here

# OR use Vertex AI
# GOOGLE_GENAI_USE_VERTEXAI=TRUE
# GOOGLE_CLOUD_PROJECT=your-project-id
# GOOGLE_CLOUD_LOCATION=us-central1

# Supabase (optional)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key

# OPA
OPA_URL=http://localhost:8181

# JWT
JWT_SECRET_KEY=change-this-secret-key

# Logging
LOG_LEVEL=INFO
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
# Core ADK
google-adk==0.5.0
google-generativeai==0.8.0

# AI/ML Models
paddlepaddle==3.0.0
paddleocr==2.9.1
insightface==0.7.3
mediapipe==0.10.18
torch==2.5.1
transformers==4.46.0

# Tools
opencv-python==4.10.0.84
Pillow==11.0.0
numpy==2.1.3
presidio-analyzer==2.2.355
pyjwt==2.9.0
requests==2.32.3

# Utils
python-dotenv==1.0.1
pydantic==2.9.2

# Testing
pytest==8.3.3
EOF

# Create README.md
cat > README.md << 'EOF'
# QuickChat ID - Complete Project

AI-powered KYC verification in 5-7 seconds using Google ADK.

## 🚀 Quick Start

### 1. Install

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install
pip install google-adk
pip install -r requirements.txt
```

### 2. Configure

```bash
# Copy env template
cp .env.example agents/kyc_orchestrator/.env

# Edit and add your API key
nano agents/kyc_orchestrator/.env
```

Get API key from: https://aistudio.google.com/apikey

### 3. Run

```bash
# From agents/ directory
cd agents
adk web
```

Open http://localhost:8000

### 4. Test

Select "kyc_orchestrator" and type:
```
สวัสดีครับ พร้อมยืนยันตัวตน
```

## 📁 Project Structure

```
QuickChatID-Complete/
├── agents/                     # ADK Agents
│   ├── kyc_orchestrator/      # Main orchestrator
│   ├── welcome_agent/         # Welcome & consent
│   ├── personal_info_agent/   # Data collection
│   ├── document_verify_agent/ # ID verification
│   └── biometric_verify_agent/# Face verification
├── tools/                      # ADK Tools
│   ├── scam_detection.py
│   ├── ocr_tool.py
│   ├── face_matching_tool.py
│   ├── liveness_tool.py
│   ├── deepfake_tool.py
│   ├── pii_masking_tool.py
│   ├── policy_evaluation_tool.py
│   └── trust_badge_tool.py
├── tests/                      # Test suites
├── .env.example               # Environment template
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## 🎯 Features

✅ Multi-agent orchestration with Google ADK
✅ Scam detection (WangchanBERTa)
✅ Thai ID OCR (PaddleOCR)
✅ Face matching (InsightFace)
✅ Liveness detection (MediaPipe)
✅ Deepfake detection
✅ PII masking (Presidio)
✅ Policy-based decisions (OPA)
✅ JWT trust certificates
✅ Built-in web UI
✅ Streaming responses
✅ Production-ready

## 📊 Tech Stack

| Category | Technology |
|----------|------------|
| Orchestration | Google ADK |
| LLM | Gemini 2.0 |
| OCR | PaddleOCR |
| Face Recognition | InsightFace |
| Liveness | MediaPipe |
| Scam Detection | WangchanBERTa |
| PII Masking | Microsoft Presidio |

## 🧪 Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=agents --cov=tools tests/
```

## 🚢 Deployment

### Cloud Run
```bash
adk deploy --platform=cloud-run
```

### Vertex AI
```bash
adk deploy --platform=vertex-ai
```

## 📚 Documentation

- [ADK Docs](https://google.github.io/adk-docs/)
- [Implementation Guide](docs/IMPLEMENTATION.md)

## 📝 License

MIT License

---

**QuickChat ID** - The Fastest, Simplest, and Safest way to build digital trust.
EOF

# Create basic tests
mkdir -p tests/unit tests/integration

cat > tests/test_tools.py << 'EOF'
"""Test tools"""

from tools.scam_detection import check_scam_intent
from tools.trust_badge_tool import issue_trust_badge

def test_scam_detection():
    result = check_scam_intent("สวัสดีครับ")
    assert 'scam_score' in result
    assert result['scam_score'] < 0.5

def test_scam_detection_malicious():
    result = check_scam_intent("กรุณาโอนเงิน 5000 บาทด่วน")
    assert result['scam_score'] > 0.5

def test_trust_badge():
    badge = issue_trust_badge('gold', 90.0)
    assert badge['trust_level'] == 'gold'
    assert 'jwt_token' in badge
    assert badge['transaction_limit'] == 100000
EOF

cat > tests/test_agents.py << 'EOF'
"""Test agents (basic structure tests)"""

def test_agents_importable():
    """Test that all agents can be imported"""
    try:
        from agents.kyc_orchestrator.agent import root_agent
        from agents.welcome_agent.agent import welcome_agent
        from agents.personal_info_agent.agent import personal_info_agent
        from agents.document_verify_agent.agent import document_verify_agent
        from agents.biometric_verify_agent.agent import biometric_verify_agent
        assert True
    except ImportError as e:
        assert False, f"Failed to import agents: {e}"

def test_orchestrator_has_subagents():
    """Test orchestrator has sub-agents registered"""
    from agents.kyc_orchestrator.agent import root_agent
    assert hasattr(root_agent, 'agents')
    assert len(root_agent.agents) == 4
EOF

echo "✓ Project finalized!"
echo ""
echo "📦 Project structure:"
find . -type f -name "*.py" | head -20
echo "..."
echo ""
echo "Total Python files: $(find . -type f -name '*.py' | wc -l)"
echo "Total lines of code: $(find . -type f -name '*.py' -exec wc -l {} + | tail -1 | awk '{print $1}')"

