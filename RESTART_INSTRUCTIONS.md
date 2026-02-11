# 🔄 วิธี Restart ระบบ QuickChat ID

## ปัญหาที่แก้ไข
- Agent ไม่เรียก `save_kyc_record` tool โดยอัตโนมัติ
- ข้อมูล KYC ไม่ถูกบันทึกลง database

## สิ่งที่ปรับปรุง
1. ✅ เพิ่มคำสั่งบังคับใน Agent instruction ให้เรียก `save_kyc_record()` ทุกครั้ง
2. ✅ เพิ่มกฎ CRITICAL ว่าต้องบันทึกทุกกรณี (ผ่าน/ไม่ผ่าน/บล็อก)
3. ✅ เพิ่มกลไกแจ้งเตือนใน LINE webhook ถ้า Agent ไม่บันทึก

## วิธี Restart

### 1. Stop ADK Server
```bash
# กด Ctrl+C ใน terminal ที่รัน ADK
```

### 2. Restart ADK Server
```bash
cd agents
adk web
```

### 3. ตรวจสอบว่า LINE Bot ยังรันอยู่
```bash
# ใน terminal อื่น
# ถ้ายังรันอยู่ จะเห็น "QuickChat ID LINE Bot Server"
# ถ้าไม่รัน ให้รันใหม่:
python line_webhook_app.py
```

### 4. ตรวจสอบ Dashboard
```bash
# ใน terminal อื่น
./start_dashboard.sh

# หรือ
python dashboard_app.py
```

## ทดสอบระบบใหม่

1. เปิด LINE Bot
2. ทำ KYC จนจบ (ได้ Trust Badge)
3. ตรวจสอบ Dashboard ที่ http://localhost:5002
4. ควรเห็นข้อมูลถูกบันทึกอัตโนมัติ

## ตรวจสอบ Logs

### ADK Server Log
```bash
# ดูว่า Agent เรียก save_kyc_record หรือไม่
# จะเห็น: "Function call: save_kyc_record"
```

### LINE Bot Log
```bash
# ถ้า Agent ไม่บันทึก จะเห็นคำเตือน:
# "⚠️  KYC completion detected but no recent record found!"
```

---

**อัพเดท**: 2026-02-08
**สถานะ**: พร้อมทดสอบ
