import pytest
from unittest.mock import MagicMock, patch
from src.agents.base import BaseAgent, AgentContext
from src.agents.log_agent import LogAnalysisAgent, MockFetcher
from src.agents.sme import SMEAgent
from src.agents.orchestrator import AgentOrchestrator

def test_base_agent_init():
    agent = BaseAgent(name="TestAgent", role="Tester", system_prompt="You are a test.")
    assert agent.name == "TestAgent"
    assert agent.role == "Tester"

@patch("src.agents.log_agent.LocalLogAnalyzer")
def test_orchestrator_routing(mock_analyzer):
    orch = AgentOrchestrator()
    # Mock the SME agent
    orch.sme_agent = MagicMock()
    orch.sme_agent.run.return_value = "SME Response"
    
    # Test routing to SME
    response = orch.run("Check errors in checkout")
    orch.sme_agent.run.assert_called_once()
    assert response == "SME Response"
    
    # Test non-routing
    orch.sme_agent.reset_mock()
    response = orch.run("Hello there")
    orch.sme_agent.run.assert_not_called()
    assert "help you diagnose" in response

@patch("src.agents.log_agent.LocalLogAnalyzer")
def test_log_agent_run(mock_analyzer):
    # Setup mocks
    mock_analyzer_instance = mock_analyzer.return_value
    mock_analyzer_result = MagicMock()
    mock_analyzer_result.summary = "No errors"
    mock_analyzer_result.key_insights = []
    mock_analyzer_result.confidence_score = 0.9
    mock_analyzer_instance.analyze_logs.return_value = mock_analyzer_result
    
    agent = LogAnalysisAgent()
    # We can use the default MockFetcher or mock it further if needed,
    # but for this test the default MockFetcher is fine as it returns list of LogEntry
    
    result = agent.run("Check logs")
    
    assert "No errors" in result
    mock_analyzer_instance.analyze_logs.assert_called()

@patch("src.agents.log_agent.LocalLogAnalyzer")
def test_sme_agent_flow(mock_analyzer):
    sme = SMEAgent()
    # Mock Log Agent
    sme.log_agent = MagicMock()
    sme.log_agent.run.return_value = "Log Findings: Error found."
    
    response = sme.run("Why is checkout failing?")
    
    sme.log_agent.run.assert_called()
    assert "Error found" in response
