"""Test agents (basic structure tests)"""

def test_agents_importable():
    """Test that all agents can be imported"""
    try:
        from agents.kyc_orchestrator.agent import root_agent
        from agents.welcome_agent.agent import welcome_agent
        from agents.personal_info_agent.agent import personal_info_agent
        from agents.document_verify_agent.agent import document_verify_agent
        from agents.biometric_verify_agent.agent import biometric_verify_agent
        assert True
    except ImportError as e:
        assert False, f"Failed to import agents: {e}"

def test_orchestrator_has_subagents():
    """Test orchestrator has sub-agents registered"""
    from agents.kyc_orchestrator.agent import root_agent
    assert hasattr(root_agent, 'agents')
    assert len(root_agent.agents) == 4
