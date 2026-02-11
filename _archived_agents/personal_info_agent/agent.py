"""Personal Info Agent"""
from google.adk.agents.llm_agent import LlmAgent
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from tools.scam_detection import check_scam_intent

personal_info_agent = LlmAgent(
    model='gemini-2.0-flash-thinking-exp',
    name='personal_info_agent',
    description='Collect personal info with fraud detection',
    instruction="""คุณเก็บข้อมูลส่วนตัวพร้อมตรวจจับหลอกลวง

**ข้อมูลที่ต้องการ:**
- ชื่อ-นามสกุล (ไทยเต็ม)
- เบอร์โทร (10 หลัก 0X-XXXX-XXXX)
- อีเมล

**ถาม:**
"ขอข้อมูลเพื่อยืนยันตัวตนครับ:
📝 ชื่อ-นามสกุล:
📱 เบอร์โทร:
📧 อีเมล:
*แชร์พร้อมกัน หรือทีละส่วนก็ได้"

**ตรวจสอบ:**
1. เช็ครูปแบบ
2. เรียก check_scam_intent(text) ทุกข้อความ
3. ถ้า scam_score > 0.7 → แจ้งเตือน หยุด
4. ถ้าผ่าน → ยืนยันข้อมูล

**สัญญาณ scam:**
- ขอเงิน/โอนเงิน
- ขอ OTP/รหัสผ่าน
- ขอข้อมูลบัตรเครดิต

**เมื่อเสร็จ:** ยืนยันข้อมูล → transfer_back()
""",
    tools=[check_scam_intent]
)

__all__ = ['personal_info_agent']
