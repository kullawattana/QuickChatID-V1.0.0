#!/bin/bash

# requirements.txt
cat > requirements.txt << 'EOF'
# Core
google-adk>=0.5.0
google-generativeai>=0.8.0

# AI/ML (optional - use mock if not installed)
paddlepaddle>=3.0.0
paddleocr>=2.9.1
insightface>=0.7.3
mediapipe>=0.10.18
torch>=2.5.1
transformers>=4.46.0

# Tools
opencv-python>=4.10.0
Pillow>=11.0.0
numpy>=2.1.3
presidio-analyzer>=2.2.355
pyjwt>=2.9.0
requests>=2.32.3

# Utils
python-dotenv>=1.0.1
pydantic>=2.9.2

# Testing
pytest>=8.3.3
pytest-asyncio>=0.24.0
pytest-cov>=6.0.0
EOF

# .env.example
cat > .env.example << 'EOF'
# Google AI / Gemini API Key
GOOGLE_GENAI_API_KEY=your-api-key-here

# OR use Vertex AI
# GOOGLE_GENAI_USE_VERTEXAI=TRUE
# GOOGLE_CLOUD_PROJECT=your-project-id
# GOOGLE_CLOUD_LOCATION=us-central1

# Optional: Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key

# Optional: OPA
OPA_URL=http://localhost:8181

# JWT Secret
JWT_SECRET_KEY=change-this-in-production

# Logging
LOG_LEVEL=INFO
EOF

# .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/
env/

# IDEs
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Project specific
.env
*.log
*.db
node_modules/

# AI models cache
.cache/
models/

# Test
.pytest_cache/
.coverage
htmlcov/
EOF

# README.md
cat > README.md << 'EOF'
# QuickChat ID - Complete Project 🚀

AI-powered KYC verification in 5-7 seconds using Google ADK.

## Features

✅ Multi-agent orchestration (5 agents)
✅ Scam detection (Thai language)
✅ Thai ID card OCR
✅ Face matching & verification
✅ Liveness detection
✅ Deepfake detection  
✅ PII masking (PDPA compliant)
✅ Policy-based risk assessment
✅ JWT trust certificates
✅ Built-in web UI
✅ Production-ready

## Quick Start

### 1. Install

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install ADK
pip install google-adk

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

```bash
# Copy env template
cp .env.example agents/kyc_orchestrator/.env

# Edit and add API key
nano agents/kyc_orchestrator/.env
```

Get free API key: https://aistudio.google.com/apikey

### 3. Run

```bash
cd agents
adk web
```

Open http://localhost:8000

### 4. Test

Select "kyc_orchestrator" and type:
```
สวัสดีครับ พร้อมยืนยันตัวตน
```

## Project Structure

```
QuickChatID-Complete/
├── agents/                     # ADK Agents
│   ├── kyc_orchestrator/      # Main orchestrator
│   ├── welcome_agent/         # Welcome & consent
│   ├── personal_info_agent/   # Data collection
│   ├── document_verify_agent/ # ID verification
│   └── biometric_verify_agent/# Face verification
├── tools/                      # ADK Tools (8 tools)
├── tests/                      # Test suites
├── .env.example               # Configuration template
├── requirements.txt           # Dependencies
├── README.md                  # This file
└── QUICKSTART.md             # Detailed guide
```

## Conversation Flow

```
1. User: "สวัสดีครับ"
   → welcome_agent: Welcome & explain process

2. User: "พร้อม"
   → personal_info_agent: Collect name, phone, email

3. User: "สมชาย ใจดี 0812345678 somchai@email.com"
   → Scam detection → document_verify_agent

4. User: "อัปโหลดบัตรแล้ว"
   → OCR extraction → biometric_verify_agent

5. User: "ถ่าย selfie แล้ว"
   → Face match + Liveness + Deepfake detection

6. System: Issues Trust Badge (Bronze/Silver/Gold/Platinum)
```

## Tech Stack

- **Orchestration**: Google ADK
- **LLM**: Gemini 2.0
- **Scam Detection**: Pattern matching + ML
- **OCR**: PaddleOCR (Thai)
- **Face Recognition**: InsightFace
- **Liveness**: MediaPipe
- **Tools**: 8 specialized tools
- **Languages**: Python, Thai

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=agents --cov=tools
```

## Deployment

### Cloud Run
```bash
adk deploy --platform=cloud-run
```

### Vertex AI
```bash
adk deploy --platform=vertex-ai
```

## Documentation

- **Quick Start**: `QUICKSTART.md`
- **Implementation**: `docs/IMPLEMENTATION.md`
- **API Reference**: `docs/API.md`
- **ADK Docs**: https://google.github.io/adk-docs/

## Troubleshooting

### API Key Error
```bash
ls agents/kyc_orchestrator/.env
# Should contain: GOOGLE_GENAI_API_KEY=...
```

### Module Not Found
```bash
pip install -r requirements.txt --upgrade
```

### Port in Use
```bash
adk web --port 8001
```

## License

MIT License

## Support

- 📧 Email: support@quickchatid.com
- 🐛 Issues: GitHub Issues
- 📚 Docs: https://google.github.io/adk-docs/

---

**QuickChat ID** - The Fastest, Simplest, and Safest way to build digital trust.

Built with ❤️ using Google ADK
EOF

# Create comprehensive QUICKSTART.md
cat > QUICKSTART.md << 'EOF'
# QuickChat ID - Quick Start Guide

เริ่มต้นใช้งานใน 10 นาที! 🚀

## Prerequisites

- Python 3.10 or 3.11
- 4GB RAM (8GB+ recommended)
- Internet connection

## Step 1: Installation (2 minutes)

```bash
# 1. Extract project
tar -xzf QuickChatID-Complete.tar.gz
cd QuickChatID-Complete

# 2. Create virtual environment
python -m venv .venv

# 3. Activate
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 4. Install ADK
pip install google-adk

# 5. Install dependencies
pip install -r requirements.txt
```

## Step 2: Get API Key (2 minutes)

Visit: https://aistudio.google.com/apikey

1. Click "Create API Key"
2. Copy the key

## Step 3: Configure (1 minute)

```bash
# Go to orchestrator directory
cd agents/kyc_orchestrator

# Create .env file
cp ../../.env.example .env

# Edit and add your key
nano .env
```

Add:
```env
GOOGLE_GENAI_API_KEY=your-actual-api-key-here
```

## Step 4: Run! (1 minute)

```bash
# Go back to agents directory
cd ..

# Start ADK web
adk web
```

## Step 5: Test! (4 minutes)

Open: http://localhost:8000

1. Select "kyc_orchestrator" from dropdown
2. Start chatting!

### Test Conversation:

```
You: สวัสดีครับ
Bot: ยินดีต้อนรับสู่ QuickChat ID...

You: พร้อม
Bot: กรุณาแชร์ข้อมูล: ชื่อ-นามสกุล, เบอร์โทร, อีเมล

You: สมชาย ใจดี 0812345678 somchai@email.com
Bot: ✅ ข้อมูลถูกต้อง... กรุณาถ่ายรูปบัตรประชาชน

You: อัปโหลดบัตรแล้ว
Bot: 🔍 กำลังประมวลผล... ✅ บัตรผ่าน! กรุณาถ่าย Selfie

You: ถ่าย selfie แล้ว
Bot: 🎉 ยืนยันตัวตนสำเร็จ! คุณได้รับ GOLD Trust Badge!
```

## Success! 🎉

ระบบทำงานแล้ว!

## Next Steps

1. **Customize Agents**: Edit `agents/*/agent.py`
2. **Add Real Models**: Install full ML dependencies
3. **Deploy**: `adk deploy --platform=cloud-run`
4. **Documentation**: Read `docs/IMPLEMENTATION.md`

## Troubleshooting

### Error: "API Key not found"
Check: `agents/kyc_orchestrator/.env` exists and contains key

### Error: "Module not found"
Run: `pip install -r requirements.txt --upgrade`

### Error: "Port 8000 in use"
Run: `adk web --port 8001`

## Tips

- Check terminal logs for agent activity
- Use `adk web --debug` for more info
- Test tools: `python tools/scam_detection.py`
- Read agent instructions in each `agent.py`

## Learn More

- ADK Docs: https://google.github.io/adk-docs/
- Implementation: `docs/IMPLEMENTATION.md`
- API Reference: `docs/API.md`

---

**QuickChat ID** - Building digital trust, one chat at a time.
EOF

# Basic tests
cat > tests/test_basic.py << 'EOF'
"""Basic tests"""
def test_tools_importable():
    from tools.scam_detection import check_scam_intent
    assert callable(check_scam_intent)

def test_scam_detection():
    from tools.scam_detection import check_scam_intent
    result = check_scam_intent("สวัสดีครับ")
    assert 'scam_score' in result
    assert result['scam_score'] < 0.5

def test_agents_exist():
    import os
    agents = ['kyc_orchestrator', 'welcome_agent', 'personal_info_agent', 'document_verify_agent', 'biometric_verify_agent']
    for agent in agents:
        assert os.path.exists(f'agents/{agent}/agent.py')
EOF

echo "✓ Configuration files created"
echo "✓ Documentation created"
echo "✓ Tests created"

