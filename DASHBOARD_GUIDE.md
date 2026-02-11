# QuickChat ID - KYC Dashboard Guide

## 📊 ภาพรวม

Dashboard สำหรับจัดเก็บและแสดงข้อมูล KYC verification ทั้งหมดจากระบบ QuickChat ID

### ✨ Features

- **แสดงสถิติ KYC** - ทั้งหมด, ผ่าน, รอตรวจสอบ, ไม่ผ่าน
- **รายการ Verification** - ดูข้อมูลทั้งหมดแบบ real-time
- **ค้นหา** - ค้นหาด้วยชื่อ หรือ เลขบัตรประชาชน
- **กรอง** - กรองตามสถานะ (approved, pending, rejected, failed)
- **รายละเอียด** - ดูข้อมูลแต่ละรายการแบบละเอียด
- **รูปภาพ** - ดูรูปบัตรประชาชนและ Selfie
- **Auto-refresh** - อัพเดทข้อมูลอัตโนมัติทุก 30 วินาที

---

## 🚀 การติดตั้ง

### 1. ติดตั้ง Dependencies

```bash
pip install sqlalchemy
```

หรือติดตั้งทั้งหมดจาก requirements.txt:

```bash
pip install -r requirements.txt
```

### 2. Initialize Database

Database จะถูกสร้างอัตโนมัติเมื่อรัน dashboard ครั้งแรก:

```bash
python -c "from database import init_db; init_db()"
```

---

## 🎯 การใช้งาน

### เริ่มต้น Dashboard

#### วิธีที่ 1: ใช้ startup script (แนะนำ)

```bash
./start_dashboard.sh
```

#### วิธีที่ 2: รันโดยตรง

```bash
python dashboard_app.py
```

### เข้าถึง Dashboard

Dashboard จะรันที่:
- **URL**: http://localhost:5002
- **Port**: 5002 (ไม่ทับกับ LINE Bot port 5001 และ ADK port 8000)

---

## 📡 API Endpoints

Dashboard มี REST API สำหรับดึงข้อมูล KYC:

### Statistics

```bash
GET /api/statistics
```

ดึงสถิติ KYC ทั้งหมด:
- `total` - จำนวนทั้งหมด
- `approved` - จำนวนที่ผ่าน
- `pending` - จำนวนรอตรวจสอบ
- `rejected` - จำนวนไม่ผ่าน

### Get All Verifications

```bash
GET /api/verifications?limit=100&offset=0&status=approved
```

Parameters:
- `limit` (optional) - จำนวนที่ต้องการดึง (default: 100)
- `offset` (optional) - เริ่มจากลำดับที่ (default: 0)
- `status` (optional) - กรองตามสถานะ (approved, pending, rejected, failed)

### Get Specific Verification

```bash
GET /api/verifications/<record_id>
```

ดึงข้อมูล KYC รายการเดียวตาม ID

### Get User's Latest Verification

```bash
GET /api/verifications/user/<user_id>
```

ดึงข้อมูล KYC ล่าสุดของ user (LINE user ID)

### Search by ID Number

```bash
GET /api/search/id_number/<id_number>
```

ค้นหาด้วยเลขบัตรประชาชน 13 หลัก

### Search by Name

```bash
GET /api/search/name?name=<name>
```

ค้นหาด้วยชื่อ หรือ นามสกุล (รองรับ partial match)

### Delete Verification

```bash
DELETE /api/verifications/<record_id>
```

ลบรายการ KYC

---

## 💾 Database Schema

### KYCVerification Model

```python
{
    'id': int,                      # Primary key
    'user_id': str,                 # LINE user ID
    'session_id': str,              # ADK session ID
    'id_number': str,               # เลขบัตรประชาชน 13 หลัก
    'prefix': str,                  # คำนำหน้า (นาย, นาง, นางสาว)
    'first_name': str,              # ชื่อ
    'last_name': str,               # นามสกุล
    'date_of_birth': str,           # วันเกิด
    'address': str,                 # ที่อยู่
    'id_card_data': dict,           # ข้อมูล OCR เต็ม
    'face_similarity_score': float, # คะแนนความคล้าย (0-100)
    'face_confidence': float,       # Confidence (0-100)
    'rekognition_data': dict,       # ข้อมูล AWS Rekognition
    'id_card_image_path': str,      # Path รูปบัตรประชาชน
    'id_card_s3_url': str,          # S3 URL รูปบัตรประชาชน
    'selfie_image_path': str,       # Path รูป Selfie
    'selfie_s3_url': str,           # S3 URL รูป Selfie
    'status': str,                  # pending, approved, rejected, failed
    'verification_result': str,     # ข้อความผลการตรวจสอบ
    'is_verified': bool,            # ผ่านการยืนยันหรือไม่
    'created_at': datetime,         # วันที่สร้าง
    'updated_at': datetime,         # วันที่อัพเดทล่าสุด
    'verified_at': datetime,        # วันที่ยืนยันเสร็จ
    'notes': str                    # หมายเหตุเพิ่มเติม
}
```

---

## 🔄 ระบบการบันทึก KYC

KYC agent จะบันทึกข้อมูลอัตโนมัติหลังจากเสร็จสิ้นการยืนยันตัวตน:

### Flow

1. User ทำ KYC ผ่าน LINE Bot
2. KYC agent ประมวลผล (OCR, Face Matching, Liveness, etc.)
3. เรียก `evaluate_final_decision()` - ตัดสินผล
4. เรียก `issue_trust_badge()` - ออก Trust Badge
5. **เรียก `save_kyc_record()`** - บันทึกลง database 💾
6. แสดงผลให้ User

### การบันทึกข้อมูล

Tool `save_kyc_record` จะรวบรวมข้อมูลจากทุกขั้นตอน:
- Personal info (name, phone, email)
- OCR data (Thai ID card)
- Face matching results (AWS Rekognition)
- Liveness detection
- Deepfake detection
- Document risk
- Biometric risk
- Final decision
- Trust badge
- Scam score

---

## 🧪 การทดสอบ

### 1. ทดสอบ Dashboard

```bash
# เปิด dashboard
./start_dashboard.sh

# เปิดเบราว์เซอร์
open http://localhost:5002
```

### 2. ทดสอบ API

```bash
# ดูสถิติ
curl http://localhost:5002/api/statistics

# ดูรายการทั้งหมด
curl http://localhost:5002/api/verifications

# ค้นหาด้วยชื่อ
curl "http://localhost:5002/api/search/name?name=สมชาย"
```

### 3. ทดสอบการบันทึก

```bash
# 1. เริ่ม ADK server
cd agents && adk web

# 2. เริ่ม LINE Bot (terminal ใหม่)
python line_webhook_app.py

# 3. เริ่ม Dashboard (terminal ใหม่)
./start_dashboard.sh

# 4. ทำ KYC ผ่าน LINE Bot
# 5. ตรวจสอบว่าข้อมูลถูกบันทึกใน Dashboard
```

---

## 🗃️ Database Location

Database file (SQLite):
```
/Users/topgun/QuickChatID-V1-full-integrated/database/kyc_data.db
```

### การ Backup

```bash
# Backup database
cp database/kyc_data.db database/kyc_data.backup.db

# Restore from backup
cp database/kyc_data.backup.db database/kyc_data.db
```

### การย้ายไป Production

สำหรับ production แนะนำให้ใช้ PostgreSQL:

1. ติดตั้ง PostgreSQL
2. เปลี่ยน `DATABASE_URL` ใน `.env`:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/kyc_db
```

3. Database จะถูกสร้างอัตโนมัติเมื่อรัน

---

## 📊 Dashboard Features Detail

### 1. Statistics Cards

แสดง:
- **ทั้งหมด** - จำนวน verification ทั้งหมด
- **ผ่านการตรวจสอบ** (สีเขียว) - status = approved
- **รอการตรวจสอบ** (สีเหลือง) - status = pending
- **ไม่ผ่าน** (สีแดง) - status = rejected

### 2. Search & Filter

- **ค้นหาด้วยชื่อ** - รองรับชื่อ/นามสกุล (partial match)
- **ค้นหาด้วยเลขบัตร** - เลขบัตรประชาชน 13 หลัก (exact match)
- **กรองตามสถานะ** - approved, pending, rejected, failed

### 3. Verification Table

แสดงคอลัมน์:
- **ID** - Record ID
- **วันที่/เวลา** - เวลาที่ทำ KYC
- **ชื่อ-นามสกุล** - จาก OCR
- **เลขบัตร** - เลขบัตรประชาชน
- **ความคล้าย** - Face similarity score (%)
- **สถานะ** - Badge แสดงสถานะ
- **รูปภาพ** - Preview รูปบัตร/Selfie (click เพื่อขยาย)
- **จัดการ** - ปุ่มดูรายละเอียด/ลบ

### 4. Detail Modal

แสดงข้อมูลละเอียด:
- ข้อมูลส่วนตัว (ชื่อ, เลขบัตร, วันเกิด, ที่อยู่)
- ผลการตรวจสอบ (สถานะ, คะแนน, เวลา)
- ผลการยืนยันตัวตน
- หมายเหตุ

### 5. Auto-refresh

- Dashboard จะ auto-refresh ทุก 30 วินาที
- Statistics และ Table จะอัพเดทอัตโนมัติ

---

## 🔧 Troubleshooting

### Database Error

```bash
# ลบ database แล้วสร้างใหม่
rm database/kyc_data.db
python -c "from database import init_db; init_db()"
```

### Port Already in Use

```bash
# เปลี่ยน port ใน dashboard_app.py
PORT = 5003  # เปลี่ยนเป็น port อื่น
```

### Import Error

```bash
# ติดตั้ง dependencies
pip install sqlalchemy flask
```

---

## 🎨 การ Customize

### เปลี่ยนธีม UI

แก้ไขใน `dashboard/templates/dashboard.html`:

```css
.navbar {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

### เพิ่ม API Endpoint

แก้ไขใน `dashboard_app.py`:

```python
@app.route('/api/custom-endpoint')
def custom_endpoint():
    # Your code here
    return jsonify(result)
```

---

## 📝 Notes

1. **Database** - SQLite สำหรับ development, PostgreSQL สำหรับ production
2. **Images** - ควรใช้ S3 สำหรับเก็บรูปภาพใน production
3. **Authentication** - Dashboard ยังไม่มี authentication, ควรเพิ่มใน production
4. **HTTPS** - ควรใช้ HTTPS สำหรับ production
5. **Backup** - ควร backup database เป็นประจำ

---

## 🆘 Support

หากมีปัญหาหรือข้อสงสัย:

1. ตรวจสอบ logs ใน terminal
2. ตรวจสอบ database file exists
3. ตรวจสอบ dependencies ติดตั้งครบ
4. ทดสอบ API endpoints ด้วย curl

---

**สร้างโดย**: QuickChat ID Team
**เวอร์ชัน**: 1.0.0
**อัพเดทล่าสุด**: 2026-02-08
