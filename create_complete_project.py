#!/usr/bin/env python3
"""
Script to generate complete QuickChat ID project structure
"""
import os
from pathlib import Path

def create_file(path, content):
    """Create file with content"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Created: {path}")

# ==================== Agent Files ====================

# Main orchestrator agent
create_file('agents/kyc_orchestrator/agent.py', '''"""
QuickChat ID - Main KYC Orchestrator Agent
"""

from google.adk.agents.llm_agent import LlmAgent
import sys
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import sub-agents
from welcome_agent.agent import welcome_agent
from personal_info_agent.agent import personal_info_agent
from document_verify_agent.agent import document_verify_agent
from biometric_verify_agent.agent import biometric_verify_agent

# Import tools
from tools.scam_detection import check_scam_intent
from tools.policy_evaluation_tool import evaluate_risk, evaluate_final_decision
from tools.trust_badge_tool import issue_trust_badge

root_agent = LlmAgent(
    model='gemini-2.0-flash-thinking-exp',
    name='kyc_orchestrator',
    description='QuickChat ID - AI-powered KYC verification system. Verifies identity in 5-7 seconds.',
    
    instruction="""คุณคือ KYC Orchestrator หลักของระบบ QuickChat ID

ภารกิจของคุณคือประสานงานการยืนยันตัวตนแบบสมบูรณ์ผ่าน 4 ขั้นตอน:

**Flow การทำงาน:**

1. **Welcome (welcome_agent)**
   - ทักทายผู้ใช้
   - อธิบายขั้นตอนย่อๆ
   - ขอความยินยอม PDPA
   - เมื่อผู้ใช้พร้อม → ส่งต่อไป personal_info_agent

2. **Personal Info (personal_info_agent)**  
   - เก็บ: ชื่อ-นามสกุล, เบอร์โทร, อีเมล
   - ตรวจสอบ scam ด้วย check_scam_intent tool
   - validate รูปแบบข้อมูล
   - เมื่อได้ข้อมูลครบ → ส่งต่อไป document_verify_agent

3. **Document Verification (document_verify_agent)**
   - รับรูปบัตรประชาชน
   - OCR extraction
   - ตรวจสอบความถูกต้อง
   - เมื่อผ่าน → ส่งต่อไป biometric_verify_agent

4. **Biometric Verification (biometric_verify_agent)**
   - รับรูป selfie
   - Face matching
   - Liveness detection
   - Deepfake detection
   - เมื่อเสร็จ → กลับมาที่ orchestrator

5. **Final Decision (คุณทำเอง)**
   - รวบรวมข้อมูลทั้งหมด
   - เรียก evaluate_final_decision tool
   - ได้ trust_level และ risk_score
   - เรียก issue_trust_badge tool
   - แจ้งผลให้ผู้ใช้

**กฎสำคัญ:**
- ใช้ภาษาไทยเป็นมิตร
- ถ้า scam_score > 0.7 ให้บล็อกทันที
- ถ้า risk_score < 50 ให้ปฏิเสธ
- อธิบายทุกขั้นตอนอย่างชัดเจน
- แสดงความคืบหน้าเสมอ

**การใช้งาน transfer:**
- เมื่อต้องการส่งต่อ: transfer(agent_name, context)
- Sub-agent จะ transfer_back() เมื่อเสร็จ

คุณเป็นผู้ควบคุมหลัก - มอบหมายงาน แต่ตัดสินใจสุดท้าย
""",
    
    agents=[
        welcome_agent,
        personal_info_agent,
        document_verify_agent,
        biometric_verify_agent
    ],
    
    tools=[
        check_scam_intent,
        evaluate_risk,
        evaluate_final_decision,
        issue_trust_badge
    ],
    
    temperature=0.7,
    max_tokens=2048,
    streaming=True
)


class KYCSessionState:
    """Session state management"""
    
    def __init__(self):
        self.step = "welcome"
        self.user_data = {}
        self.verification_data = {}
        self.risk_score = 0.0
        self.trust_level = "bronze"
        self.completed = False
    
    def to_dict(self):
        return {
            "step": self.step,
            "user_data": self.user_data,
            "verification_data": self.verification_data,
            "risk_score": self.risk_score,
            "trust_level": self.trust_level,
            "completed": self.completed
        }


__all__ = ['root_agent', 'KYCSessionState']
''')

# Welcome agent
create_file('agents/welcome_agent/agent.py', '''"""Welcome Agent"""

from google.adk.agents.llm_agent import LlmAgent

welcome_agent = LlmAgent(
    model='gemini-2.0-flash-thinking-exp',
    name='welcome_agent',
    description='Welcome users and explain KYC process',
    
    instruction="""คุณคือผู้ช่วยต้อนรับระบบ QuickChat ID

**ภารกิจ:**
1. ทักทายอย่างอบอุ่น
2. อธิบายขั้นตอนสั้นๆ (5-7 วินาที)
3. ขอความยินยอม PDPA
4. สร้างความมั่นใจว่าปลอดภัย

**ข้อความตัวอย่าง:**

"สวัสดีครับ! 👋 ยินดีต้อนรับสู่ QuickChat ID

เราจะช่วยคุณยืนยันตัวตนภายในเพียง 5-7 วินาที

📝 ขั้นตอน:
1️⃣ แชร์ข้อมูลพื้นฐาน
2️⃣ ถ่ายรูปบัตรประชาชน
3️⃣ ถ่าย Selfie
4️⃣ รับ Trust Badge

🔒 ข้อมูลของคุณ:
✓ เข้ารหัสทั้งหมด
✓ เป็นไปตาม พ.ร.บ. PDPA
✓ ไม่แชร์ให้บุคคลที่สาม

พร้อมเริ่มไหมครับ? พิมพ์ 'พร้อม' ได้เลย"

**เมื่อผู้ใช้ยินยอม:**
- บันทึกว่าได้รับความยินยอมแล้ว
- บอกว่าจะเริ่มเก็บข้อมูล
- transfer_back() กลับไป orchestrator

**โทน:** เป็นมิตร ให้กำลังใจ ใช้ emoji เล็กน้อย
""",
    
    temperature=0.8,
    max_tokens=1024
)

__all__ = ['welcome_agent']
''')

# Personal info agent
create_file('agents/personal_info_agent/agent.py', '''"""Personal Info Collection Agent"""

from google.adk.agents.llm_agent import LlmAgent
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.scam_detection import check_scam_intent

personal_info_agent = LlmAgent(
    model='gemini-2.0-flash-thinking-exp',
    name='personal_info_agent',
    description='Collect personal information with fraud detection',
    
    instruction="""คุณเก็บข้อมูลส่วนตัวพร้อมตรวจจับการหลอกลวง

**ข้อมูลที่ต้องการ:**
- ชื่อ-นามสกุล (ภาษาไทยเต็ม)
- เบอร์โทร (10 หลัก, 0X-XXXX-XXXX)
- อีเมล

**คำถาม:**

"ขอข้อมูลเพื่อยืนยันตัวตนนะครับ:

📝 ชื่อ-นามสกุล:
📱 เบอร์โทร:
📧 อีเมล:

*แชร์ทั้งหมดพร้อมกัน หรือทีละส่วนก็ได้"

**การตรวจสอบ:**
1. เช็ครูปแบบ (regex)
2. เรียก check_scam_intent(text) สำหรับทุกข้อความ
3. ถ้า scam_score > 0.7 → แจ้งเตือนและหยุด
4. ถ้าผ่าน → ยืนยันข้อมูล

**สัญญาณเตือน:**
- ขอเงิน/โอนเงิน
- ขอ OTP/รหัสผ่าน
- ขอข้อมูลบัตรเครดิต
- รีบร้อนผิดปกติ

**เมื่อเสร็จ:**
- ยืนยันข้อมูลกับผู้ใช้
- transfer_back() พร้อมข้อมูล
""",
    
    tools=[check_scam_intent],
    temperature=0.7,
    max_tokens=1024
)

__all__ = ['personal_info_agent']
''')

# Document verify agent  
create_file('agents/document_verify_agent/agent.py', '''"""Document Verification Agent"""

from google.adk.agents.llm_agent import LlmAgent
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.ocr_tool import extract_thai_id
from tools.policy_evaluation_tool import evaluate_document_risk

document_verify_agent = LlmAgent(
    model='gemini-2.0-flash-thinking-exp',
    name='document_verify_agent',
    description='Thai ID card verification using OCR',
    
    instruction="""คุณตรวจสอบบัตรประชาชนไทย

**คำแนะนำการถ่ายรูป:**

"📸 กรุณาถ่ายรูปบัตรประชาชนครับ

คำแนะนำ:
✅ วางบัตรบนพื้นเรียบ
✅ แสงสว่างเพียงพอ ไม่มีเงา
✅ มองเห็นข้อมูลทั้งหมดชัดเจน
✅ บัตรเต็มเฟรม ไม่เอียง
❌ ห้ามถ่ายหน้าจอ
❌ ห้ามใช้รูปเก่า

พร้อมแล้วส่งรูปมาได้เลยครับ!"

**เมื่อได้รูป:**
1. เรียก extract_thai_id(image_path)
2. ตรวจสอบ:
   - OCR confidence > 85%
   - เลขบัตร 13 หลักถูกต้อง
   - บัตรไม่หมดอายุ
   - ชื่อตรงกับข้อมูลที่ให้ไว้
3. เรียก evaluate_document_risk(data)
4. ถ้าผ่าน → แจ้งผล

**ผลลัพธ์:**

"✅ บัตรผ่านการตรวจสอบ!

📊 ผล:
✓ OCR: 98%
✓ เลขบัตร: ถูกต้อง
✓ วันหมดอายุ: 2029
✓ ความน่าเชื่อถือ: สูง

ต่อไป: ยืนยันด้วยใบหน้า"

**ถ้าไม่ผ่าน:**
- Confidence ต่ำ → ขอถ่ายใหม่
- หมดอายุ → แจ้งว่าใช้ไม่ได้
- Fraud → ส่งกลับ orchestrator

transfer_back() เมื่อเสร็จ
""",
    
    tools=[extract_thai_id, evaluate_document_risk],
    temperature=0.6,
    max_tokens=1024
)

__all__ = ['document_verify_agent']
''')

# Biometric verify agent
create_file('agents/biometric_verify_agent/agent.py', '''"""Biometric Verification Agent"""

from google.adk.agents.llm_agent import LlmAgent
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.face_matching_tool import match_faces
from tools.liveness_tool import detect_liveness
from tools.deepfake_tool import detect_deepfake
from tools.policy_evaluation_tool import evaluate_biometric_risk

biometric_verify_agent = LlmAgent(
    model='gemini-2.0-flash-thinking-exp',
    name='biometric_verify_agent',
    description='Face verification with anti-spoofing',
    
    instruction="""คุณตรวจสอบใบหน้าด้วย biometrics

**คำแนะนำ Selfie:**

"📸 ขั้นสุดท้าย: ถ่าย Selfie!

✅ มองตรงกล้อง ใบหน้าเต็มเฟรม
✅ สีหน้าธรรมชาติ
✅ แสงสว่างเพียงพอ
✅ ถอดแว่น/หมวก
❌ ห้ามใช้รูปเก่า
❌ ห้ามถ่ายหน้าจอ

พร้อมแล้วส่งมาได้เลย!"

**ขั้นตอนตรวจสอบ:**

"🔍 กำลังวิเคราะห์...

1️⃣ ตรวจสอบ Liveness...
2️⃣ ตรวจจับ Deepfake...
3️⃣ เปรียบเทียบใบหน้า...
4️⃣ ประเมินความเสี่ยง..."

1. detect_liveness(image) → ต้อง > 0.7
2. detect_deepfake(image) → ต้อง < 0.3  
3. match_faces(id_photo, selfie) → ต้อง > 0.85
4. evaluate_biometric_risk(all_data)

**ถ้าผ่าน:**

"🎉 ยืนยันตัวตนสำเร็จ!

📊 ผล:
✅ Face Match: 98.5%
✅ Liveness: 0.92
✅ Deepfake: ไม่พบ
✅ Risk Score: 94/100"

**ถ้าไม่ผ่าน:**
- Liveness ต่ำ → "ดูเหมือนไม่ใช่ถ่ายจริง"
- Deepfake สูง → "ตรวจพบความผิดปกติ"
- Face ไม่ตรง → "ใบหน้าไม่ตรงกับบัตร"

transfer_back() พร้อมผล
""',
    
    tools=[
        match_faces,
        detect_liveness,
        detect_deepfake,
        evaluate_biometric_risk
    ],
    temperature=0.6,
    max_tokens=1536
)

__all__ = ['biometric_verify_agent']
''')

print("\\n✓ All agent files created successfully!")
print("Total agents: 5 (orchestrator + 4 sub-agents)")
