#!/bin/bash
set -e

echo "🚀 Creating QuickChat ID - Complete Project..."

# Create all Python package __init__ files
for dir in agents tools services utils tests tests/unit tests/integration; do
    touch "$dir/__init__.py"
done

# Main orchestrator agent
cat > agents/kyc_orchestrator/__init__.py << 'EOF'
from .agent import root_agent, KYCSessionState
__all__ = ['root_agent', 'KYCSessionState']
EOF

cat > agents/kyc_orchestrator/agent.py << 'EOF'
"""QuickChat ID - Main KYC Orchestrator Agent"""

from google.adk.agents.llm_agent import LlmAgent
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from welcome_agent.agent import welcome_agent
from personal_info_agent.agent import personal_info_agent
from document_verify_agent.agent import document_verify_agent
from biometric_verify_agent.agent import biometric_verify_agent

from tools.scam_detection import check_scam_intent
from tools.policy_evaluation_tool import evaluate_risk, evaluate_final_decision
from tools.trust_badge_tool import issue_trust_badge

root_agent = LlmAgent(
    model='gemini-2.0-flash-thinking-exp',
    name='kyc_orchestrator',
    description='QuickChat ID - AI-powered KYC verification in 5-7 seconds',
    
    instruction="""คุณคือ KYC Orchestrator ระบบ QuickChat ID

**ภารกิจ:** ประสานงานการยืนยันตัวตนแบบสมบูรณ์ 4 ขั้นตอน

**Flow:**
1. welcome_agent → ทักทาย ขอความยินยอม
2. personal_info_agent → เก็บข้อมูล + ตรวจจับ scam
3. document_verify_agent → ตรวจสอบบัตรประชาชน (OCR)
4. biometric_verify_agent → ยืนยันด้วยใบหน้า
5. orchestrator (คุณ) → ตัดสินใจสุดท้าย ออก Badge

**การใช้งาน transfer:**
- transfer(agent_name, context) เพื่อส่งต่อ
- Sub-agent จะ transfer_back() เมื่อเสร็จ

**กฎสำคัญ:**
- ถ้า scam_score > 0.7 → บล็อกทันที
- ถ้า risk_score < 50 → ปฏิเสธ
- อธิบายทุกขั้นตอนชัดเจน
- ใช้ภาษาไทยเป็นมิตร

คุณคือผู้ควบคุมหลัก - มอบหมายงาน แต่ตัดสินใจสุดท้าย
""",
    
    agents=[welcome_agent, personal_info_agent, document_verify_agent, biometric_verify_agent],
    tools=[check_scam_intent, evaluate_risk, evaluate_final_decision, issue_trust_badge],
    temperature=0.7,
    max_tokens=2048,
    streaming=True
)

class KYCSessionState:
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
EOF

# Sub-agents
for agent in welcome personal_info document_verify biometric_verify; do
    cat > "agents/${agent}_agent/__init__.py" << EOF
from .agent import ${agent}_agent
__all__ = ['${agent}_agent']
EOF
done

cat > agents/welcome_agent/agent.py << 'EOF'
"""Welcome Agent"""
from google.adk.agents.llm_agent import LlmAgent

welcome_agent = LlmAgent(
    model='gemini-2.0-flash-thinking-exp',
    name='welcome_agent',
    description='Welcome users and explain KYC process',
    instruction="""คุณต้อนรับผู้ใช้ระบบ QuickChat ID

**ทำ:**
1. ทักทายอย่างอบอุ่น
2. อธิบายขั้นตอน 4 ขั้น (5-7 วินาที)
3. ขอความยินยอม PDPA
4. สร้างความมั่นใจว่าปลอดภัย

**ตัวอย่าง:**
"สวัสดีครับ! 👋 ยินดีต้อนรับสู่ QuickChat ID

เราจะช่วยคุณยืนยันตัวตนภายในเพียง 5-7 วินาที

📝 ขั้นตอน:
1️⃣ แชร์ข้อมูลพื้นฐาน
2️⃣ ถ่ายรูปบัตรประชาชน
3️⃣ ถ่าย Selfie
4️⃣ รับ Trust Badge

🔒 ข้อมูลปลอดภัย เข้ารหัส เป็นไปตาม พ.ร.บ. PDPA

พร้อมเริ่มไหมครับ? พิมพ์ 'พร้อม'"

**เมื่อผู้ใช้ยินยอม:** transfer_back() กลับไป orchestrator
**โทน:** เป็นมิตร ให้กำลังใจ ใช้ emoji เล็กน้อย
""",
    temperature=0.8,
    max_tokens=1024
)

__all__ = ['welcome_agent']
EOF

cat > agents/personal_info_agent/agent.py << 'EOF'
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
    tools=[check_scam_intent],
    temperature=0.7,
    max_tokens=1024
)

__all__ = ['personal_info_agent']
EOF

cat > agents/document_verify_agent/agent.py << 'EOF'
"""Document Verify Agent"""
from google.adk.agents.llm_agent import LlmAgent
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from tools.ocr_tool import extract_thai_id
from tools.policy_evaluation_tool import evaluate_document_risk

document_verify_agent = LlmAgent(
    model='gemini-2.0-flash-thinking-exp',
    name='document_verify_agent',
    description='Thai ID card verification',
    instruction="""คุณตรวจสอบบัตรประชาชนไทย

**คำแนะนำถ่ายรูป:**
"📸 กรุณาถ่ายรูปบัตรประชาชน

คำแนะนำ:
✅ วางบัตรบนพื้นเรียบ
✅ แสงสว่างเพียงพอ ไม่มีเงา
✅ มองเห็นข้อมูลชัดเจน
✅ บัตรเต็มเฟรม ไม่เอียง
❌ ห้ามถ่ายหน้าจอ
❌ ห้ามใช้รูปเก่า

พร้อมแล้วส่งมา!"

**เมื่อได้รูป:**
1. extract_thai_id(path)
2. ตรวจสอบ:
   - OCR confidence > 85%
   - เลขบัตร 13 หลักถูกต้อง
   - บัตรไม่หมดอายุ
   - ชื่อตรงกับที่ให้ไว้
3. evaluate_document_risk(data)

**ผ่าน:**
"✅ บัตรผ่านการตรวจสอบ!
📊 ผล:
✓ OCR: 98%
✓ เลขบัตร: ถูกต้อง
✓ วันหมดอายุ: 2029
✓ ความน่าเชื่อถือ: สูง

ต่อไป: ยืนยันด้วยใบหน้า"

**ไม่ผ่าน:**
- Confidence ต่ำ → ขอถ่ายใหม่
- หมดอายุ → แจ้งใช้ไม่ได้
- Fraud → ส่งกลับ orchestrator

transfer_back() เมื่อเสร็จ
""",
    tools=[extract_thai_id, evaluate_document_risk],
    temperature=0.6,
    max_tokens=1024
)

__all__ = ['document_verify_agent']
EOF

cat > agents/biometric_verify_agent/agent.py << 'EOF'
"""Biometric Verify Agent"""
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

พร้อมแล้วส่งมา!"

**ขั้นตอน:**
"🔍 กำลังวิเคราะห์...
1️⃣ Liveness...
2️⃣ Deepfake...
3️⃣ Face Match...
4️⃣ Risk..."

1. detect_liveness(img) → > 0.7
2. detect_deepfake(img) → < 0.3
3. match_faces(id, selfie) → > 0.85
4. evaluate_biometric_risk(data)

**ผ่าน:**
"🎉 ยืนยันสำเร็จ!
📊 ผล:
✅ Face Match: 98.5%
✅ Liveness: 0.92
✅ Deepfake: ไม่พบ
✅ Risk: 94/100"

**ไม่ผ่าน:**
- Liveness ต่ำ → "ดูไม่ใช่ถ่ายจริง"
- Deepfake สูง → "ตรวจพบความผิดปกติ"
- Face ไม่ตรง → "ใบหน้าไม่ตรงบัตร"

transfer_back()
""",
    tools=[match_faces, detect_liveness, detect_deepfake, evaluate_biometric_risk],
    temperature=0.6,
    max_tokens=1536
)

__all__ = ['biometric_verify_agent']
EOF

echo "✓ Agents created (5 agents)"

# Continue in next script part...
