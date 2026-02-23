# QuickChat ID V1 - AI-Powered eKYC Verification

> Chat-based eKYC verification in 5-7 seconds via LINE / Web UI
> No app installation required | Built with Google ADK + Gemini 2.5 Flash

---

## Overview

QuickChat ID is a **chat-based electronic Know Your Customer (eKYC)** system that allows users to verify their identity through LINE messaging or a Web UI. The system uses a multi-agent AI architecture powered by Google ADK (Agent Development Kit) and Gemini 2.5 Flash to orchestrate the verification process.

### Key Features

- **Thai ID Card OCR** - Extract data from Thai national ID cards (Typhoon OCR / PaddleOCR)
- **Face Matching** - Compare selfie with ID card photo (AWS Rekognition, 99.80% accuracy)
- **Liveness Detection** - Anti-spoofing using texture analysis / MediaPipe / DeepFace
- **Deepfake Detection** - Detect AI-generated face images
- **Scam Intent Detection** - Detect fraud patterns in Thai text
- **Trust Badge System** - Tiered trust levels (Bronze / Silver / Gold / Platinum)
- **Enterprise Security** - OPA, Presidio, Guardrails, Keycloak, Telemetry
- **Multi-Channel** - LINE Bot + Facebook Messenger + Web UI with same AI agent
- **PDPA Compliant** - PII masking and data protection

---

## System Architecture

```
+------------------------------------------------------------------+
|                        User Channels                              |
|                                                                   |
|    +----------------+              +-----------------------+      |
|    |   LINE Bot     |              |   Web UI (React)      |      |
|    |   Messaging    |              |   localhost:5173       |      |
|    +-------+--------+              +-----------+-----------+      |
|            |                                   |                  |
+------------+-----------------------------------+------------------+
             |                                   |
             v                                   v
  +--------------------+              +------------------------+
  | LINE Webhook App   |              |   Web API (Flask)      |
  |  localhost:5001    |              |   localhost:5001        |
  |                    |              |                         |
  |  5 Enterprise      |              |  5 Enterprise           |
  |  Services          |              |  Services               |
  +--------+-----------+              +------------+-----------+
           |                                       |
           +------------------+--------------------+
                              |
                              v
            +----------------------------------+
            |   ADK Agent (Gemini 2.5 Flash)   |
            |   kyc_orchestrator               |
            |   localhost:8000                 |
            |                                  |
            |   11 AI Tools:                   |
            |   - OCR (Thai ID)                |
            |   - Face Matching (Rekognition)  |
            |   - Liveness Detection           |
            |   - Deepfake Detection           |
            |   - Scam Detection               |
            |   - Policy Evaluation            |
            |   - Trust Badge (JWT)            |
            |   - Save KYC Record              |
            +--------+----------+--------------+
                     |          |
         +-----------+          +-------------+
         v                                    v
  +---------------+  +------------+  +----------------+
  | Typhoon OCR / |  |   AWS      |  |   SQLite       |
  | PaddleOCR     |  | Rekognition|  |   Database     |
  +---------------+  +------------+  +----------------+
```

---

## KYC Verification Flow

```
 Start
   |
   v
+--------------------------------------------+
|  Step 1: Welcome & PDPA Consent            |
|  User: "สวัสดีครับ พร้อมยืนยันตัวตน"         |
|  Bot: อธิบายขั้นตอน + ขอความยินยอม PDPA     |
+---------------------+----------------------+
                      | ยินยอม
                      v
+--------------------------------------------+
|  Step 2: Personal Info Collection          |
|  User: ชื่อ-นามสกุล + เบอร์โทร + อีเมล      |
|                                            |
|  +-- check_scam_intent() --+               |
|  | scam_score > 0.7?       |               |
|  | YES -> Block            |               |
|  | NO  -> Continue         |               |
|  +-------------------------+               |
+---------------------+----------------------+
                      | ผ่าน
                      v
+--------------------------------------------+
|  Step 3: Document Verification             |
|  User: อัปโหลดรูปบัตรประชาชน                |
|                                            |
|  +-- extract_thai_id() ---------------+    |
|  | OCR: ชื่อ, เลขบัตร, วันเกิด, ที่อยู่   |    |
|  +------------------------------------+    |
|  +-- evaluate_document_risk() --------+    |
|  | ตรวจสอบความถูกต้องของเอกสาร         |    |
|  +------------------------------------+    |
+---------------------+----------------------+
                      | ผ่าน
                      v
+--------------------------------------------+
|  Step 4: Biometric Verification            |
|  User: ถ่าย Selfie                         |
|                                            |
|  +-- detect_liveness() --------------+     |
|  | ตรวจ Anti-Spoofing                 |     |
|  +-----------------------------------+     |
|  +-- detect_deepfake() --------------+     |
|  | ตรวจ Deepfake                      |     |
|  +-----------------------------------+     |
|  +-- match_faces() ------------------+     |
|  | เปรียบเทียบ Selfie vs บัตร         |     |
|  +-----------------------------------+     |
|  +-- evaluate_biometric_risk() ------+     |
|  | ประเมินความเสี่ยง Biometric         |     |
|  +-----------------------------------+     |
+---------------------+----------------------+
                      |
                      v
+--------------------------------------------+
|  Step 5: Final Decision & Trust Badge      |
|                                            |
|  +-- evaluate_final_decision() ------+     |
|  | รวมคะแนน Document + Biometric      |     |
|  | + Scam Score                       |     |
|  +----------------+------------------+     |
|                   v                        |
|  +-- issue_trust_badge() ------------+     |
|  | Platinum (96+) | Gold (81-95)     |     |
|  | Silver (61-80) | Bronze (50-60)   |     |
|  +-----------------------------------+     |
|  +-- save_kyc_record() --------------+     |
|  | บันทึกผลลง Database                |     |
|  +-----------------------------------+     |
+--------------------------------------------+
                      |
                      v
                 KYC Complete
```

---

## Enterprise Services Flow

```
                  +-----------------+
                  |  User Request   |
                  +--------+--------+
                           |
                           v
            +--------------------------+
            |   Telemetry (Tracing)    |---- Jaeger / Prometheus
            |   trace_span() start     |
            +-------------+------------+
                          |
                          v
            +--------------------------+
            |   Keycloak (IAM)         |---- User Registration
            |   create_user()          |---- Role Assignment
            +-------------+------------+
                          |
                          v
            +--------------------------+
            |   Presidio (PII Mask)    |---- Log Masking
            |   anonymize()            |---- เลขบัตร/โทร/อีเมล
            +-------------+------------+
                          |
                          v
            +--------------------------+
            |   ADK Agent Processing   |
            |   (KYC Verification)     |
            +-------------+------------+
                          |
                          v
            +--------------------------+
            |   OPA (Policy Engine)    |---- Risk Scoring
            |   evaluate_policy()      |---- Block / Allow
            +-------------+------------+
                          |
                          v
            +--------------------------+
            |   Guardrails (Validate)  |---- Toxic Content
            |   validate_output()      |---- PII Leakage
            +-------------+------------+
                          |
                          v
            +--------------------------+
            |   Response to User       |
            +--------------------------+
```

---

## Project Structure

```
QuickChatID-V1-full-integrated/
|
|-- agents/                          # ADK Agents
|   +-- kyc_orchestrator/            #   Main KYC agent (Gemini 2.5 Flash)
|       |-- agent.py                 #   Agent definition + 11 tools
|       +-- __init__.py
|
|-- tools/                           # ADK Tools (called by Agent)
|   |-- ocr_tool.py                  #   Thai ID card OCR (Typhoon/PaddleOCR)
|   |-- face_matching_tool.py        #   Face comparison (AWS Rekognition)
|   |-- liveness_tool.py             #   Anti-spoofing detection
|   |-- deepfake_tool.py             #   Deepfake detection
|   |-- scam_detection.py            #   Thai scam intent detection
|   |-- policy_evaluation_tool.py    #   Risk scoring (Document/Biometric)
|   |-- trust_badge_tool.py          #   JWT trust certificates
|   |-- save_kyc_tool.py             #   Save results to database
|   +-- pii_masking_tool.py          #   PII masking (PDPA)
|
|-- services/                        # Backend Services
|   |-- aws_rekognition_service.py   #   AWS face matching
|   |-- ocr_service.py               #   Multi-backend OCR
|   |-- liveness_service.py          #   Liveness detection (3 methods)
|   |-- deepfake_service.py          #   Deepfake detection
|   |-- face_verification_service.py #   DeepFace/InsightFace wrapper
|   |-- opa_service.py               #   OPA policy engine
|   |-- presidio_service.py          #   Microsoft Presidio PII masking
|   |-- guardrails_service.py        #   LLM output validation
|   |-- keycloak_service.py          #   Keycloak IAM
|   +-- telemetry_service.py         #   OpenTelemetry tracing
|
|-- database/                        # Database Layer
|   |-- models.py                    #   SQLAlchemy models (KYCVerification)
|   +-- kyc_repository.py            #   CRUD operations
|
|-- frontend/                        # React Frontend
|   |-- src/
|   |   |-- components/              #   React components
|   |   |-- hooks/                   #   Custom hooks (useEKYC)
|   |   |-- App.tsx                  #   Main app
|   |   +-- main.tsx                 #   Entry point
|   |-- package.json                 #   Node.js dependencies
|   +-- vite.config.ts               #   Vite configuration
|
|-- dashboard/                       # Admin Dashboard (HTML/CSS)
|-- web_api_app.py                   # Flask Web API (port 5001)
|-- line_webhook_app.py              # LINE Bot Webhook (port 5001)
|-- dashboard_app.py                 # Admin Dashboard API (port 5002)
|
|-- docker-compose.yml               # Docker infrastructure
|-- requirements.txt                 # Python dependencies (core)
|-- requirements-enhanced.txt        # Python dependencies (full)
|-- requirements-ocr.txt             # OCR-specific dependencies
|-- requirements-face.txt            # Face verification dependencies
|-- requirements-chat.txt            # Chat platform dependencies
|
|-- test_enterprise_services.py      # Enterprise services test suite
|-- test_web_api.py                  # Web API tests
|-- test_upload.py                   # Upload flow tests
+-- .env                             # Environment variables (not in git)
```

---

## Installation

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+ (for frontend)
- **Docker** (optional, for enterprise services)

### Step 1: Clone & Setup Python Environment

```bash
git clone <repository-url>
cd QuickChatID-V1-full-integrated

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
```

### Step 2: Install Python Dependencies

```bash
# Option A: Install all at once
pip install -r requirements.txt

# Option B: Install by category

# --- Core (Required) ---
pip install google-adk google-generativeai
pip install flask flask-cors requests python-dotenv
pip install line-bot-sdk
pip install sqlalchemy
pip install opencv-python Pillow numpy
pip install pyjwt boto3

# --- OCR ---
pip install typhoon-ocr           # Typhoon OCR API (recommended)
pip install paddlepaddle paddleocr # PaddleOCR local (optional)

# --- Face & Biometric ---
pip install deepface mediapipe     # Liveness & deepfake detection

# --- Enterprise Services (Optional) ---
pip install presidio-analyzer presidio-anonymizer spacy
pip install opentelemetry-api opentelemetry-sdk
pip install python-keycloak
pip install guardrails-ai
```

### Step 3: Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### Step 4: Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
# ==================== Required ====================

# Google Gemini API Key (for ADK Agent)
GOOGLE_GENAI_API_KEY=your_gemini_api_key
GOOGLE_API_KEY=your_gemini_api_key

# Typhoon OCR API Key (for Thai ID card OCR)
TYPHOON_OCR_API_KEY=your_typhoon_api_key

# AWS Rekognition (for face matching)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# ==================== LINE Bot (if using LINE channel) ====================

LINE_CHANNEL_ACCESS_TOKEN=your_line_token
LINE_CHANNEL_SECRET=your_line_secret

# ==================== Optional ====================

# Database (default: SQLite)
DATABASE_URL=sqlite:///kyc_database.db

# Enable local OCR instead of Typhoon API
# ENABLE_LOCAL_OCR=1
```

**Where to get API Keys:**

| Key | URL |
|-----|-----|
| `GOOGLE_GENAI_API_KEY` | https://aistudio.google.com/apikey |
| `TYPHOON_OCR_API_KEY` | https://api.opentyphoon.ai |
| `AWS_ACCESS_KEY_ID` | https://console.aws.amazon.com/iam |
| `LINE_CHANNEL_*` | https://developers.line.biz/console |

---

## Running the Application

### Option A: Web UI (React + Flask)

Open **3 terminals**:

```bash
# Terminal 1 - ADK Agent Server
cd agents
adk web
# Running on http://localhost:8000

# Terminal 2 - Flask Backend API
python web_api_app.py
# Running on http://localhost:5001

# Terminal 3 - React Frontend
cd frontend
npm run dev
# Running on http://localhost:5173
```

Open **http://localhost:5173** in your browser.

### Option B: LINE Bot / Facebook Messenger

Open **2 terminals**:

```bash
# Terminal 1 - ADK Agent Server
cd agents
adk web
# Running on http://localhost:8000

# Terminal 2 - LINE + Messenger Webhook Server
python line_webhook_app.py
# Running on http://localhost:5001
```

For LINE Bot, you also need **ngrok** for public URL:

```bash
ngrok http 5001
# LINE Developer Console → Webhook URL:
#   https://xxxx.ngrok-free.dev/webhook-test/line-bot
#
# Facebook Developer Console → Messenger Webhook URL:
#   https://xxxx.ngrok-free.dev/webhook/messenger
```

**Platform Detection** — `platform` field ถูก set อัตโนมัติจาก user_id:

| Pattern | Platform |
|---------|----------|
| `U` + 32 chars (e.g. `Uabc123...`) | `line` |
| Numeric string (e.g. `9340707359288035`) | `messenger` |
| `WEB_` prefix | `web` |

### Option C: Admin Dashboard

```bash
python dashboard_app.py
# Running on http://localhost:5002
```

### Quick Start Scripts

```bash
# Start ADK + Backend + Frontend
./start_web.sh

# Start ADK + LINE Bot
./start_line_bot.sh

# Start Dashboard
./start_dashboard.sh
```

---

## Port Summary

| Service | Port | URL |
|---------|------|-----|
| ADK Agent (Gemini) | 8000 | http://localhost:8000 |
| Flask Web API | 5003 | http://localhost:5003 |
| LINE / Messenger Webhook | 5001 | http://localhost:5001 |
| React Frontend | 5173 | http://localhost:5173 |
| Admin Dashboard | 5002 | http://localhost:5002 |
| Swagger UI | 5003 | http://localhost:5003/docs |

---

## API Endpoints

### Web API (`web_api_app.py`) — port 5003

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check + enterprise services status |
| `POST` | `/api/session/init` | Initialize new KYC session |
| `POST` | `/api/chat/message` | Send text message to agent |
| `POST` | `/api/chat/image` | Upload ID card or selfie image |
| `GET` | `/api/verification/status/<session_id>` | Get verification status |
| `GET` | `/docs` | Swagger UI (API documentation) |
| `GET` | `/swagger.json` | OpenAPI 3.0 spec |

### E-Commerce API (requires `X-API-Key` header)

| Method | Endpoint | Query Params | Description |
|--------|----------|-------------|-------------|
| `GET` | `/api/v1/kyc/verify` | `user_id` | ดึง KYC Certificate ของ user |
| `GET` | `/api/v1/kyc/users` | `role`, `platform`, `limit` | List ผู้ใช้ที่ผ่าน KYC |
| `GET` | `/api/v1/kyc/stats` | — | สถิติ KYC รวม |
| `POST` | `/api/v1/kyc/webhook/register` | — | ลงทะเบียน Webhook callback |
| `POST` | `/api/v1/kyc/webhook/test` | — | ทดสอบ Webhook |

**Platform filter ตัวอย่าง:**
```bash
# เฉพาะ Messenger users
GET /api/v1/kyc/users?platform=messenger

# Seller บน LINE เท่านั้น
GET /api/v1/kyc/users?platform=line&role=seller
```

### Dashboard API (`dashboard_app.py`) — port 5002

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/statistics` | KYC statistics (total/approved/pending/rejected) |
| `GET` | `/api/verifications` | List all records (pagination + status filter) |
| `GET` | `/api/verifications/<id>` | Get single record |
| `GET` | `/api/search/id_number/<id>` | Search by Thai ID number |
| `GET` | `/api/search/name?name=<name>` | Search by name |
| `DELETE` | `/api/verifications/<id>` | Delete record |

### LINE / Messenger Webhook (`line_webhook_app.py`) — port 5001

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/webhook/line` | LINE webhook |
| `POST` | `/webhook-test/line-bot` | LINE webhook (ngrok testing) |
| `POST` | `/webhook/messenger` | Facebook Messenger webhook |
| `GET` | `/health` | Health check |

---

## Tech Stack

### AI & ML

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Agent Orchestration | Google ADK | Multi-tool AI agent framework |
| LLM | Gemini 2.5 Flash | Conversational AI (Thai language) |
| Thai ID OCR | Typhoon OCR / PaddleOCR | Extract text from ID cards (82.68% accuracy) |
| Face Matching | AWS Rekognition | Compare selfie vs ID card (99.80% accuracy) |
| Liveness Detection | Texture / MediaPipe / DeepFace | Anti-spoofing (3 methods) |
| Deepfake Detection | Texture / DeepFace | Detect AI-generated faces |
| Scam Detection | Pattern Matching (Thai) | Detect fraud intent in messages |

### Enterprise Services

| Service | Technology | Purpose |
|---------|-----------|---------|
| Policy Engine | OPA (Open Policy Agent) | Risk scoring & blocking rules |
| PII Masking | Microsoft Presidio | Mask personal data in logs (PDPA) |
| IAM | Keycloak | User management & role assignment |
| Observability | OpenTelemetry | Tracing, metrics, events |
| Output Validation | Guardrails | Block toxic/PII content in AI responses |

### Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend | Flask + Python | REST API server |
| Frontend | React + TypeScript + Vite | Web UI |
| Styling | Tailwind CSS | UI components |
| Database | SQLAlchemy + SQLite | KYC record storage |
| LINE Bot | LINE Bot SDK v3 | Messaging integration |
| Facebook Messenger | Messenger Platform API | Messaging integration |
| Containers | Docker Compose | Enterprise services |

---

## OPA Risk Scoring

The OPA policy engine calculates a **weighted risk score**:

```
Risk Score = (Face Match x 30%) + (Liveness x 25%) + (Anti-Deepfake x 20%)
           + (OCR Confidence x 15%) + (Anti-Scam x 10%)
```

### Trust Badge Levels

| Badge | Score Range | Transaction Limit |
|-------|-------------|-------------------|
| Platinum | 96 - 100 | Unlimited |
| Gold | 81 - 95 | 100,000 THB |
| Silver | 61 - 80 | 50,000 THB |
| Bronze | 50 - 60 | 10,000 THB |
| Blocked | < 50 | Rejected |

### Hard Block Conditions

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Scam Score | > 0.7 | Immediate block |
| Deepfake Probability | > 0.7 | Immediate block |
| Liveness Score | < 0.3 | Immediate block |

---

## Docker Infrastructure (Optional)

For full enterprise services with real backends:

```bash
docker-compose up -d
```

| Service | Port | Purpose |
|---------|------|---------|
| OPA | 8181 | Policy engine |
| Keycloak | 8080 | Identity & access management |
| PostgreSQL | 5432 | Database (for Keycloak) |
| Redis | 6379 | Caching |
| Jaeger | 16686 | Distributed tracing UI |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3001 | Monitoring dashboards |

> Without Docker, all enterprise services automatically run in **mock/fallback mode** - the system still works fully.

---

## Database Schema

### KYCVerification Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Auto-increment ID |
| `user_id` | String | LINE user ID or web session ID |
| `session_id` | String | ADK session ID |
| `id_number` | String | Thai ID card number (13 digits) |
| `prefix` | String | Title (นาย / นาง / นางสาว) |
| `first_name` | String | First name |
| `last_name` | String | Last name |
| `date_of_birth` | String | Date of birth |
| `address` | Text | Address from ID card |
| `id_card_data` | JSON | Full OCR result data |
| `face_similarity_score` | Float | Face match score (0-100) |
| `face_confidence` | Float | Confidence level (0-100) |
| `rekognition_data` | JSON | AWS Rekognition raw response |
| `status` | String | pending / approved / rejected / failed |
| `is_verified` | Boolean | Verification passed |
| `role` | String | buyer / seller / null |
| `platform` | String | line / messenger / web (auto-detected from user_id) |
| `notes` | Text | trust_level, risk_score, source metadata |
| `created_at` | DateTime | Record creation (Bangkok UTC+7) |
| `verified_at` | DateTime | Verification timestamp |

---

## Graceful Degradation

All services have built-in **mock/fallback modes**. The system works even without external services:

| Missing Component | Fallback Behavior |
|-------------------|-------------------|
| AWS credentials | Mock face match result (for testing) |
| Typhoon OCR API key | Falls back to PaddleOCR (local) |
| Docker not running | Enterprise services use mock mode |
| DeepFace not installed | Uses texture-based analysis |
| MediaPipe not installed | Uses texture-based analysis |
| Database unavailable | In-memory session storage |

---

## Testing

### Enterprise Services Test (39 tests)

```bash
python test_enterprise_services.py
```

Tests all 5 services: OPA, Presidio, Telemetry, Guardrails, Keycloak

### Web API Test

```bash
python test_web_api.py     # API endpoint tests
python test_upload.py      # Image upload flow test
```

### Unit Tests

```bash
pytest tests/
pytest --cov=agents --cov=tools --cov=services
```

---

## Troubleshooting

### API Key Error
```bash
cat .env | grep API_KEY
# Should show: GOOGLE_GENAI_API_KEY=AIza...
```

### ADK Agent Not Starting
```bash
cd agents
adk web --port 8000
```

### Port Already in Use
```bash
lsof -ti:5001 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

### Module Not Found
```bash
pip install -r requirements.txt --upgrade
```

### LINE Bot Webhook Not Working
```bash
# Start ngrok
ngrok http 5001

# Set webhook URL in LINE Developer Console:
# https://your-url.ngrok-free.dev/webhook-test/line-bot
```

### Face Matching Returns 0%
```bash
# Verify AWS credentials
aws sts get-caller-identity
```

---

## License

MIT License

---

**QuickChat ID** - The Fastest, Simplest, and Safest way to build digital trust.

Built with Google ADK + Gemini 2.5 Flash
