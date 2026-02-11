"""Basic tests"""
def test_tools_importable():
    from tools.scam_detection import check_scam_intent
    assert callable(check_scam_intent)

def test_scam_detection():
    from tools.scam_detection import check_scam_intent
    result = check_scam_intent("สวัสดีครับ")
    assert 'scam_score' in result
    assert result['scam_score'] < 0.5

def test_agents_exist():
    import os
    agents = ['kyc_orchestrator', 'welcome_agent', 'personal_info_agent', 'document_verify_agent', 'biometric_verify_agent']
    for agent in agents:
        assert os.path.exists(f'agents/{agent}/agent.py')
