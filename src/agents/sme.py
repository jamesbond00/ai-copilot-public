"""
SME Agent implementation.
Coordinates diagnostic reasoning and delegates to specialist agents.
"""
from typing import Optional, List
from .base import BaseAgent, AgentContext
from .log_agent import LogAnalysisAgent
import logging

logger = logging.getLogger(__name__)

class SMEAgent(BaseAgent):
    """
    Subject Matter Expert Agent.
    Orchestrates the diagnostic process by consulting specialist tools/agents.
    """
    
    def __init__(self, model: str = "qwen2:1.5b"):
        system_prompt = (
            "You are a Senior Site Reliability Engineer. "
            "Your job is to diagnose system issues by formulating hypotheses and gathering evidence. "
            "You have access to a Log Analysis Agent to checking system logs."
        )
        super().__init__(
            name="SMEAgent",
            role="Lead",
            system_prompt=system_prompt,
            model=model
        )
        # Initialize sub-agents
        self.log_agent = LogAnalysisAgent(model=model)

    def run(self, message: str, context: Optional[AgentContext] = None) -> str:
        """
        Conduct a diagnostic session.
        """
        self.logger.info(f"SME Agent starting diagnosis for: {message}")
        
        # 1. Internal Reasoning: "I should check the logs for this service."
        reasoning = self._think(message, context)
        self.logger.info(f"SME Thought: {reasoning}")
        
        # 2. Delegation: Call Log Agent
        # In a real system, the LLM would generate this call. Here we hardcode the interaction flow for the foundation.
        log_query = f"Check errors related to: {message}"
        log_findings = self.log_agent.run(log_query, context)
        
        # 3. Synthesis: Combine findings into a final report
        final_diagnosis = self._synthesize_findings(message, log_findings)
        
        return final_diagnosis

    def _synthesize_findings(self, original_issue: str, log_findings: str) -> str:
        """
        Combine the original issue and the evidence from logs into a final answer.
        """
        # TODO: Use LLM to synthesize this.
        # For MVP, simple formatting.
        return (
            f"## SME Diagnostic Report\n"
            f"**Issue**: {original_issue}\n\n"
            f"### Evidence Gathered\n"
            f"{log_findings}\n\n"
            f"### Conclusion\n"
            f"Based on the logs, there are confirmed errors. Recommendation: detailed in log report."
        )
