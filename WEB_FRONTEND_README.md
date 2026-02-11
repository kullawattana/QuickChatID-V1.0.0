# 🌐 QuickChat ID - Web Frontend Integration

## ✅ สิ่งที่เพิ่มเข้ามา

ตอนนี้ QuickChat ID มี **3 ช่องทางการใช้งาน**:

1. ✅ **LINE Bot** - ใช้งานผ่าน LINE Application
2. ✅ **Web Frontend** - ใช้งานผ่านเว็บไซต์ (ใหม่!)
3. ✅ **Dashboard** - ดูข้อมูล KYC ที่บันทึกไว้

---

## 📁 ไฟล์ที่สร้างขึ้นใหม่

```
QuickChatID-V1-full-integrated/
├── web_api_app.py              # 🆕 REST API สำหรับ Frontend
├── test_web_api.py             # 🆕 สคริปต์ทดสอบ API
├── start_web.sh                # 🆕 สคริปต์เริ่มต้นระบบ
├── START_WEB_FRONTEND.md       # 🆕 คู่มือการใช้งาน
├── WEB_FRONTEND_README.md      # 🆕 README นี้
└── frontend/
    └── .env                    # 🆕 Configuration สำหรับ Frontend
```

---

## 🚀 วิธีเริ่มต้นใช้งาน (3 ขั้นตอน)

### ขั้นตอนที่ 1: เปิด Backend API

```bash
# Terminal 1
python web_api_app.py
```

**ควรเห็น:**
```
🌐 QuickChat ID - Web API Server
🚀 Starting server on http://0.0.0.0:5001
✅ API Endpoints ready
```

### ขั้นตอนที่ 2: ทดสอบ API (Optional)

```bash
# Terminal 2
python test_web_api.py
```

**ควรเห็น:**
```
✅ All tests passed!
🎉 Web API is working correctly!
```

### ขั้นตอนที่ 3: เปิด Frontend

```bash
# Terminal 3
cd frontend
npm install    # ครั้งแรกเท่านั้น
npm run dev
```

**ควรเห็น:**
```
➜  Local:   http://localhost:5173/
```

### เปิดเบราว์เซอร์

```
http://localhost:5173
```

---

## 🎯 ความสามารถของ Web Frontend

### Features ที่มี:

- ✅ **Chat Interface** - สนทนากับ AI Agent
- ✅ **Step Indicator** - แสดงขั้นตอนปัจจุบัน (6 steps)
- ✅ **Image Upload** - อัปโหลดบัตรประชาชนและ Selfie
- ✅ **Trust Badge Display** - แสดง Trust Badge ที่ได้รับ
- ✅ **Real-time Messaging** - Chat แบบทันที
- ✅ **Responsive Design** - ใช้งานได้ทั้ง Desktop/Mobile

### Flow การทำ KYC:

1. 💬 **Welcome** - Agent ทักทาย
2. 📝 **Personal Info** - กรอกชื่อ, เบอร์, อีเมล
3. 🆔 **ID Card** - อัปโหลดบัตรประชาชน → OCR
4. 🤳 **Selfie** - ถ่ายรูปใบหน้า → Face Matching
5. 🎖️ **Trust Badge** - รับ Badge (Bronze/Silver/Gold/Platinum)
6. ✅ **Complete** - เสร็จสิ้น!

---

## 📡 Architecture

```
┌─────────────────────────────────┐
│  Frontend (React + TypeScript)  │
│  http://localhost:5173          │
│  - Chat UI                      │
│  - Image Upload                 │
│  - Trust Badge Display          │
└──────────────┬──────────────────┘
               │ REST API
               ▼
┌─────────────────────────────────┐
│  Backend API (Flask)            │
│  http://localhost:5001          │
│  - Session Management           │
│  - Message Processing           │
│  - Image Handling               │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  ADK Agent (Google Gemini)      │
│  http://localhost:8000          │
│  - OCR (PaddleOCR/Typhoon)      │
│  - Face Match (AWS Rekognition) │
│  - Liveness & Deepfake          │
│  - Trust Badge Issuance         │
└─────────────────────────────────┘
```

---

## 🔧 API Endpoints

### 1. Initialize Session
```http
POST /api/session/init

Response:
{
  "success": true,
  "session_id": "abc-123",
  "user_id": "web_abc123",
  "message": {
    "role": "assistant",
    "content": "Welcome message...",
    "timestamp": "2026-02-10T..."
  }
}
```

### 2. Send Message
```http
POST /api/chat/message

Body:
{
  "session_id": "abc-123",
  "message": "พร้อม"
}

Response:
{
  "success": true,
  "response": "Agent response...",
  "next_step": "personal_info",
  "scam_score": 0.0,
  "timestamp": "2026-02-10T..."
}
```

### 3. Upload Image
```http
POST /api/chat/image

Body (multipart/form-data):
- file: <image file>
- session_id: "abc-123"
- image_type: "id_card" | "selfie"

Response:
{
  "success": true,
  "response": "Processing result...",
  "next_step": "biometric",
  "trust_badge": {...},  // if complete
  "timestamp": "2026-02-10T..."
}
```

### 4. Get Status
```http
GET /api/verification/status/:session_id

Response:
{
  "success": true,
  "current_step": "document",
  "is_completed": false
}
```

### 5. Health Check
```http
GET /api/health

Response:
{
  "status": "healthy",
  "service": "QuickChat ID Web API",
  "version": "1.0.0"
}
```

---

## 🎨 Frontend Tech Stack

- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite 5
- **Styling:** Tailwind CSS
- **Icons:** Lucide React
- **State:** React Hooks (useState, useCallback)

### Key Files:

```
frontend/src/
├── hooks/
│   └── useEKYC.ts          # Main KYC logic
├── components/
│   ├── ChatMessage.tsx     # Chat bubble
│   ├── ChatInput.tsx       # Message input
│   ├── StepIndicator.tsx   # Progress indicator
│   └── TrustBadge.tsx      # Badge display
├── App.tsx                 # Main app component
└── main.tsx                # Entry point
```

---

## 🔄 โหมดการทำงาน

### Demo Mode (ไม่ต้องมี ADK)

ถ้า ADK Server ไม่รัน:
- ✅ Frontend ทำงานได้ปกติ
- ✅ ใช้ Mock Data
- ⚠️ ไม่มี AI จริง

### Full AI Mode (มี ADK)

ถ้ารัน ADK Server:
```bash
cd agents
adk web
```

จะได้:
- ✅ Gemini 2.5 Flash AI
- ✅ OCR จริง (PaddleOCR/Typhoon)
- ✅ Face Matching จริง (AWS Rekognition)
- ✅ บันทึกลง Database

---

## 📊 เปรียบเทียบช่องทาง

| Feature | LINE Bot | Web Frontend | Dashboard |
|---------|----------|--------------|-----------|
| สนทนา AI | ✅ | ✅ | ❌ |
| อัปโหลดรูป | ✅ | ✅ | ❌ |
| OCR | ✅ | ✅ | ❌ |
| Face Matching | ✅ | ✅ | ❌ |
| Trust Badge | ✅ | ✅ | ❌ |
| ดูข้อมูล | ❌ | ❌ | ✅ |
| ค้นหา | ❌ | ❌ | ✅ |

---

## 🚀 Production Deployment

### Backend API (Cloud Run)

```bash
# Deploy to Google Cloud Run
gcloud run deploy quickchatid-api \
  --source . \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --port 5001 \
  --set-env-vars ADK_SERVER_URL=https://your-adk-server.com
```

### Frontend (Vercel)

```bash
# Build
cd frontend
npm run build

# Deploy
vercel deploy --prod
```

### Update Frontend .env

```bash
# Production
VITE_API_URL=https://quickchatid-api-xxx.a.run.app/api
```

---

## 🐛 Troubleshooting

### ปัญหา: Port 5001 ถูกใช้งานอยู่

```bash
# หา process ที่ใช้ port 5001
lsof -i :5001

# Kill process
kill -9 <PID>
```

### ปัญหา: Frontend ไม่เชื่อมต่อ Backend

1. เช็ค Backend รันอยู่หรือไม่
```bash
curl http://localhost:5001/api/health
```

2. เช็ค CORS config ใน `web_api_app.py`

3. เช็ค `.env` ใน frontend folder

### ปัญหา: CORS Error

- ตรวจสอบว่า Frontend รันที่ port 5173
- Restart Backend API
- Clear browser cache

---

## 📝 การพัฒนาต่อ

### เพิ่ม Features ใหม่:

1. **Authentication** - Login/Register
2. **History** - ดูประวัติการทำ KYC
3. **Profile** - จัดการข้อมูลส่วนตัว
4. **Analytics** - Dashboard สำหรับ Admin
5. **Multi-language** - รองรับหลายภาษา

### ปรับแต่ง UI:

- แก้สี theme ใน `tailwind.config.js`
- ปรับ layout ใน `App.tsx`
- เพิ่ม animations

---

## 📚 คู่มือเพิ่มเติม

- [START_WEB_FRONTEND.md](START_WEB_FRONTEND.md) - วิธีเริ่มต้นใช้งานแบบละเอียด
- [RESTART_INSTRUCTIONS.md](RESTART_INSTRUCTIONS.md) - วิธี Restart ระบบ
- [docs/FRONTEND_INTEGRATION.md](docs/documents/FRONTEND_INTEGRATION.md) - เอกสาร Integration แบบเต็ม

---

## ✅ Checklist สำหรับทดสอบ

- [ ] Backend API รันได้ที่ port 5001
- [ ] Health check ผ่าน (`curl http://localhost:5001/api/health`)
- [ ] Frontend รันได้ที่ port 5173
- [ ] สามารถเริ่ม session ใหม่ได้
- [ ] สามารถส่งข้อความได้
- [ ] สามารถอัปโหลดบัตรประชาชนได้
- [ ] สามารถอัปโหลด Selfie ได้
- [ ] แสดง Trust Badge เมื่อเสร็จ
- [ ] Step Indicator เปลี่ยนถูกต้อง

---

## 🎉 สรุป

ตอนนี้ QuickChat ID มีทั้งหมด **3 interfaces**:

1. **LINE Bot** → สำหรับผู้ใช้ LINE
2. **Web Frontend** → สำหรับ Web Browser
3. **Dashboard** → สำหรับ Admin

**ทั้ง 3 ช่องทาง ใช้ AI Backend เดียวกัน!**

---

**🚀 พร้อมใช้งานแล้ว!**

ลองเริ่มต้นด้วย:
```bash
python web_api_app.py
```

แล้วเปิด browser ที่ http://localhost:5173

**มีคำถาม?** ดูได้ที่ [START_WEB_FRONTEND.md](START_WEB_FRONTEND.md)
