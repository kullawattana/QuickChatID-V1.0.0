# การตั้งค่า LINE Bot สำหรับ QuickChat ID

คู่มือนี้จะแนะนำวิธีการเชื่อมต่อ KYC Agent กับ LINE Messaging API

## 📋 ขั้นตอนที่ 1: ตรวจสอบ LINE Credentials

เช็คว่ามี LINE credentials ใน `.env` file แล้ว:

```bash
# ใน agents/kyc_orchestrator/.env
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token_here
LINE_CHANNEL_SECRET=your_channel_secret_here
```

หากยังไม่มี ให้ไปสร้าง LINE Bot ที่:
- https://developers.line.biz/console/

## 📦 ขั้นตอนที่ 2: ติดตั้ง Dependencies

```bash
pip install flask line-bot-sdk
```

หรือติดตั้งทั้งหมดจาก requirements.txt:

```bash
pip install -r requirements.txt
```

## 🚀 ขั้นตอนที่ 3: รัน LINE Webhook Server

### แบบที่ 1: รันในเครื่อง (Local Development)

```bash
python line_webhook_app.py
```

Server จะรันที่ `http://localhost:5000`

### แบบที่ 2: ใช้ ngrok สำหรับ Testing

เนื่องจาก LINE ต้องการ HTTPS URL ให้ใช้ ngrok:

1. ติดตั้ง ngrok:
```bash
# macOS
brew install ngrok

# หรือ download จาก https://ngrok.com/
```

2. รัน ngrok:
```bash
ngrok http 5000
```

3. คุณจะได้ URL แบบนี้:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:5000
```

4. ใช้ URL นี้ตั้งค่าใน LINE Developer Console

## ⚙️ ขั้นตอนที่ 4: ตั้งค่า Webhook ใน LINE Developer Console

1. เข้า LINE Developer Console: https://developers.line.biz/console/
2. เลือก Provider และ Channel ของคุณ
3. ไปที่แท็บ "Messaging API"
4. ที่ส่วน **Webhook settings**:
   - Webhook URL: `https://your-ngrok-url.ngrok.io/webhook/line`
   - เปิด "Use webhook": ON
   - เปิด "Redelivery": ON (optional)
5. กด "Verify" เพื่อทดสอบ connection
6. ที่ส่วน **LINE Official Account features**:
   - Auto-reply messages: OFF
   - Greeting messages: OFF (optional)

## 📱 ขั้นตอนที่ 5: ทดสอบ

1. เปิด LINE app บนมือถือ
2. สแกน QR Code ของ Bot หรือค้นหาด้วย LINE ID
3. เริ่มต้นการสนทนา:
   - พิมพ์ "เริ่มใหม่" หรือ "/start" เพื่อเริ่มต้น KYC
   - Bot จะแสดง welcome message พร้อม Flex Message
   - ทำตามขั้นตอนที่ Bot แนะนำ

## 🔍 การทดสอบ Workflow

### Test Case 1: Full KYC Flow

1. พิมพ์: `/start`
2. Bot ตอบ: Welcome message พร้อมขั้นตอน 4 ขั้น
3. พิมพ์: `พร้อม`
4. Bot ขอข้อมูล: ชื่อ-นามสกุล, เบอร์โทร, อีเมล
5. ให้ข้อมูล: `สมชาย ใจดี`
6. Bot ขอเบอร์โทร: `0812345678`
7. Bot ขออีเมล: `test@example.com`
8. Bot ขอรูปบัตรประชาชน
9. ส่งรูปบัตรประชาชน (ถ่ายรูปหรืออัปโหลด)
10. Bot แสดงผล OCR และความมั่นใจ
11. Bot ขอรูป Selfie
12. ส่งรูป Selfie
13. Bot ประมวลผล: Liveness, Deepfake, Face Matching
14. Bot แสดงผล Trust Badge (Bronze/Silver/Gold/Platinum)

### Test Case 2: Restart

- พิมพ์: `เริ่มใหม่` หรือ `/start` ตอนไหนก็ได้เพื่อเริ่มใหม่

### Test Case 3: Error Handling

- ส่งรูปที่ไม่ใช่บัตรประชาชน → Bot จะแจ้งเตือนให้ส่งใหม่
- ส่งข้อความแปลกๆ → Scam detection จะตรวจจับ

## 🐛 Debugging

### เช็ค Logs

รัน server จะแสดง logs แบบนี้:

```bash
📩 Message from U1234567890abcde: สวัสดี
✓ Image saved: /tmp/quickchat_id/U1234567890abcde/id_card_123.jpg
🖼️  Image from U1234567890abcde: 123456789
```

### Health Check

เช็คว่า server ทำงานปกติ:

```bash
curl http://localhost:5000/health
```

Response:
```json
{
  "status": "ok",
  "service": "QuickChat ID LINE Bot",
  "active_sessions": 3
}
```

### Webhook Verification

ทดสอบว่า LINE webhook ทำงาน:

1. ใน LINE Developer Console → Messaging API → Webhook URL
2. กด "Verify"
3. ควรได้ผล "Success"

## 🔐 Security Notes

1. **Signature Verification**: App จะตรวจสอบ LINE signature อัตโนมัติ
2. **HTTPS Required**: LINE ต้องการ HTTPS - ใช้ ngrok สำหรับ testing
3. **Environment Variables**: อย่า commit `.env` ลง git
4. **Rate Limiting**: LINE จำกัด message rate - ใช้ reply_message แทน push_message เมื่อเป็นไปได้

## 📊 Architecture

```
LINE User → LINE Platform → Webhook (Flask)
                              ↓
                        LINE Webhook App
                              ↓
                        ADK KYC Agent
                              ↓
                    Tools (OCR, Face Match, etc.)
                              ↓
                        LINE Webhook App
                              ↓
                        LINE Platform → LINE User
```

## 🚀 Production Deployment

สำหรับ production ควร:

1. Deploy บน cloud platform (AWS, GCP, Azure, Heroku)
2. ใช้ HTTPS certificate (Let's Encrypt)
3. ใช้ Redis หรือ Database สำหรับ session storage
4. ตั้งค่า rate limiting และ monitoring
5. ใช้ async processing สำหรับ image handling

### ตัวอย่าง: Deploy บน Heroku

```bash
# สร้าง Procfile
echo "web: python line_webhook_app.py" > Procfile

# สร้าง runtime.txt
echo "python-3.11" > runtime.txt

# Deploy
heroku create your-app-name
git push heroku main
heroku config:set LINE_CHANNEL_ACCESS_TOKEN=your_token
heroku config:set LINE_CHANNEL_SECRET=your_secret
```

จากนั้นตั้งค่า webhook URL เป็น:
`https://your-app-name.herokuapp.com/webhook/line`

## 📝 Notes

- Session data เก็บใน memory (จะหายเมื่อ restart) - ใช้ Redis ใน production
- Image files เก็บใน `/tmp` - ใช้ S3 หรือ Cloud Storage ใน production
- ADK agent รันใน same process - พิจารณาแยก service ใน production

## 🆘 Troubleshooting

### ปัญหา: Bot ไม่ตอบ

- เช็ค webhook URL ใน LINE Console
- เช็ค logs ใน terminal
- ทดสอบด้วย curl: `curl -X POST http://localhost:5000/health`

### ปัญหา: Invalid signature

- เช็คว่า `LINE_CHANNEL_SECRET` ถูกต้อง
- เช็ค request headers มี `X-Line-Signature`

### ปัญหา: Agent ไม่ทำงาน

- เช็คว่า ADK server ทำงาน: `cd agents && adk web`
- หรือใช้ direct agent import (fallback mode)

### ปัญหา: Image ไม่ได้รับ

- เช็คว่ามี permission เขียนไฟล์ใน `/tmp`
- เช็ค LINE API rate limits

## 📞 Support

หากมีปัญหา:
1. เช็ค logs ใน terminal
2. ใช้ `/health` endpoint เพื่อดู status
3. ทดสอบ agent ผ่าน ADK web UI ก่อน (http://localhost:8000)
