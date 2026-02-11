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
    tools=[match_faces, detect_liveness, detect_deepfake, evaluate_biometric_risk]
)

__all__ = ['biometric_verify_agent']
