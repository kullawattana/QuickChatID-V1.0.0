# 🌐 วิธีเปิดใช้งาน Web Frontend

## 📋 ภาพรวม

ระบบ QuickChat ID มี 2 ส่วนหลัก:
1. **Backend API** (`web_api_app.py`) - รัน Agent และ AI Services
2. **Frontend Web** (`frontend/`) - React UI สำหรับผู้ใช้

---

## 🚀 วิธีเริ่มต้น (Quick Start)

### ขั้นตอนที่ 1: เปิด Backend API

```bash
# Terminal 1
cd /Users/topgun/QuickChatID-V1-full-integrated

# รัน Web API Server
python web_api_app.py
```

**ผลลัพธ์ที่ควรเห็น:**
```
============================================================
🌐 QuickChat ID - Web API Server
============================================================

🚀 Starting server on http://0.0.0.0:5001

📡 ADK Server: http://localhost:8000

✅ API Endpoints:
   POST /api/session/init - Initialize session
   POST /api/chat/message - Send message
   POST /api/chat/image - Upload image
   GET  /api/verification/status/<session_id> - Get status
   GET  /api/health - Health check

🌍 CORS enabled for:
   - http://localhost:5173 (Vite)
   - http://localhost:3000 (React)
============================================================
```

---

### ขั้นตอนที่ 2: เปิด Frontend

```bash
# Terminal 2
cd /Users/topgun/QuickChatID-V1-full-integrated/frontend

# ติดตั้ง dependencies (ครั้งแรกเท่านั้น)
npm install

# รัน development server
npm run dev
```

**ผลลัพธ์ที่ควรเห็น:**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
➜  press h + enter to show help
```

---

### ขั้นตอนที่ 3: เปิดเว็บไซต์

เปิดเบราว์เซอร์ไปที่:
```
http://localhost:5173
```

---

## 🎯 โหมดการทำงาน

### โหมดที่ 1: Demo Mode (ไม่ต้องมี ADK Server)

ถ้า ADK Server ไม่รัน ระบบจะทำงานใน **Demo Mode**:
- ✅ Frontend ใช้งานได้ปกติ
- ✅ แสดง UI และ Chat Interface
- ✅ ทดสอบ Flow การทำ KYC
- ⚠️ ใช้ข้อมูล Mock (ไม่มี AI จริง)

### โหมดที่ 2: Full AI Mode (มี ADK Server)

ถ้าต้องการใช้ AI จริง ให้รัน ADK Server ด้วย:

```bash
# Terminal 3 (เพิ่มเติม)
cd /Users/topgun/QuickChatID-V1-full-integrated/agents
adk web
```

เมื่อ ADK รันแล้ว:
- ✅ ใช้ Gemini 2.5 Flash จริง
- ✅ OCR ด้วย PaddleOCR/Typhoon
- ✅ Face Matching ด้วย AWS Rekognition
- ✅ บันทึกข้อมูลลง Database

---

## 📱 การใช้งาน

### Flow การทำ KYC ผ่าน Web:

1. **เปิดหน้าเว็บ** → เห็นหน้า Chat Interface
2. **กดเริ่มต้น** → Agent ทักทาย
3. **กรอกข้อมูลส่วนตัว** → ชื่อ, เบอร์โทร, อีเมล
4. **อัปโหลดบัตรประชาชน** → OCR ดึงข้อมูล
5. **ถ่าย Selfie** → Face Matching + Liveness
6. **รับ Trust Badge** → เสร็จสิ้น!

---

## 🔧 Troubleshooting

### ปัญหา: Frontend ไม่เชื่อมต่อ Backend

**อาการ:** เห็น "Demo Mode" ใน chat

**แก้ไข:**
1. ตรวจสอบว่า Backend API รันอยู่ที่ port 5001
```bash
lsof -i :5001
```

2. ตรวจสอบ health check
```bash
curl http://localhost:5001/api/health
```

3. ดู logs ใน Terminal ที่รัน `web_api_app.py`

---

### ปัญหา: CORS Error

**อาการ:** Console แสดง "CORS policy blocked"

**แก้ไข:**
1. ตรวจสอบว่า Frontend รันที่ port 5173
2. เช็ค CORS config ใน `web_api_app.py`
3. Restart Backend API

---

### ปัญหา: Image Upload ไม่ได้

**อาการ:** อัปโหลดรูปแล้วไม่มีการตอบกลับ

**แก้ไข:**
1. ตรวจสอบ file size (ควร < 10MB)
2. ตรวจสอบ file type (JPG, PNG)
3. ดู logs ใน Backend

---

## 📊 Port ที่ใช้งาน

| Service | Port | URL |
|---------|------|-----|
| Backend API | 5001 | http://localhost:5001 |
| Frontend (Vite) | 5173 | http://localhost:5173 |
| ADK Server | 8000 | http://localhost:8000 |
| LINE Bot | 5001 | http://localhost:5001 |
| Dashboard | 5002 | http://localhost:5002 |

---

## 🎨 Frontend Features

Frontend มี features ดังนี้:

- ✅ **Chat Interface** - พูดคุยกับ Agent
- ✅ **Step Indicator** - แสดงขั้นตอนปัจจุบัน (1-6)
- ✅ **Image Upload** - อัปโหลดบัตรและ Selfie
- ✅ **Trust Badge Display** - แสดง Badge ที่ได้รับ
- ✅ **Responsive Design** - ใช้งานได้ทั้ง Desktop/Mobile
- ✅ **Real-time Messaging** - Chat แบบ realtime

---

## 🚀 Production Deployment

### Backend (Cloud Run):

```bash
# Build and deploy
gcloud run deploy quickchatid-api \
  --source . \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --port 5001
```

### Frontend (Vercel):

```bash
# Build
cd frontend
npm run build

# Deploy
vercel deploy --prod
```

อัปเดท `.env`:
```bash
VITE_API_URL=https://quickchatid-api-xxx.a.run.app/api
```

---

## 📚 ข้อมูลเพิ่มเติม

### API Endpoints ทั้งหมด:

1. **POST /api/session/init**
   - Initialize session ใหม่
   - Returns: session_id, welcome_message

2. **POST /api/chat/message**
   - ส่งข้อความ chat
   - Body: `{session_id, message}`
   - Returns: response, next_step

3. **POST /api/chat/image**
   - อัปโหลดรูปภาพ
   - Form-data: `file, session_id, image_type`
   - Returns: response, trust_badge (ถ้าเสร็จ)

4. **GET /api/verification/status/:session_id**
   - ดูสถานะการ verify
   - Returns: current_step, is_completed

5. **GET /api/health**
   - Health check
   - Returns: status, version

---

## 🎯 Next Steps

1. **ทดสอบระบบ** - ทดลองทำ KYC จนจบ
2. **ปรับแต่ง UI** - แก้สี, font, layout ตามต้องการ
3. **เพิ่ม Features** - เช่น history, analytics
4. **Deploy Production** - ขึ้น Cloud Run + Vercel

---

**สร้างโดย:** Claude Sonnet 4.5
**วันที่:** 2026-02-10
**เวอร์ชัน:** 1.0.0
