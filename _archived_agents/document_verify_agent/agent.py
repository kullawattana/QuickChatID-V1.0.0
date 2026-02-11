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
    tools=[extract_thai_id, evaluate_document_risk]
)

__all__ = ['document_verify_agent']
