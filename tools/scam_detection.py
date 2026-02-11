"""Scam Detection Tool"""
import re

def check_scam_intent(text: str):
    patterns = {
        'money_request': r'(โอนเงิน|ส่งเงิน|ให้เงิน|ชำระ|เงิน.*บาท)',
        'urgency': r'(ด่วน|รีบ|เร็ว|ทันที|ฉุกเฉิน)',
        'bank_account': r'(บัญชี|เลขบัญชี|ธนาคาร|พร้อมเพย์)',
        'otp_request': r'(รหัส\s*OTP|OTP|รหัสยืนยัน)',
        'credential': r'(รหัสผ่าน|password|pin)',
        'impersonation': r'(ธนาคาร|ตำรวจ|ศาล|ทางการ)',
        'threat': r'(ถูกฟ้อง|ถูกจับ|มีความผิด|ปรับ)',
        'lottery': r'(รางวัล|โชคดี|ชนะ|แจก.*เงิน)',
    }
    
    indicators = []
    for name, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            indicators.append(name)
    
    score = min(len(indicators) * 0.15, 0.9)
    
    if score >= 0.8:
        risk = 'critical'
    elif score >= 0.6:
        risk = 'high'
    elif score >= 0.4:
        risk = 'medium'
    else:
        risk = 'low'
    
    return {
        'scam_score': round(score, 3),
        'is_scam': score > 0.7,
        'confidence': round(max(score, 0.7), 3),
        'indicators': indicators,
        'risk_level': risk,
        'message': f"Detected {len(indicators)} indicators: {', '.join(indicators) if indicators else 'none'}"
    }
