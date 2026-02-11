"""Test tools"""

from tools.scam_detection import check_scam_intent
from tools.trust_badge_tool import issue_trust_badge

def test_scam_detection():
    result = check_scam_intent("สวัสดีครับ")
    assert 'scam_score' in result
    assert result['scam_score'] < 0.5

def test_scam_detection_malicious():
    result = check_scam_intent("กรุณาโอนเงิน 5000 บาทด่วน")
    assert result['scam_score'] > 0.5

def test_trust_badge():
    badge = issue_trust_badge('gold', 90.0)
    assert badge['trust_level'] == 'gold'
    assert 'jwt_token' in badge
    assert badge['transaction_limit'] == 100000
