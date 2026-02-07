"""
Agent Orchestrator implementation.
Main entry point for user interactions.
"""
from typing import Optional
from .base import BaseAgent, AgentContext
from .sme import SMEAgent
import logging

logger = logging.getLogger(__name__)

class AgentOrchestrator(BaseAgent):
    """
    Top-level Orchestrator.
    Routes user requests to the appropriate sub-agent (currently just SME).
    """
    
    def __init__(self, model: str = "qwen2:1.5b"):
        system_prompt = (
            "You are the Agent Orchestrator for the System Diagnostics Copilot. "
            "Your role is to understand user intensity and route them to the right agent. "
            "For troubleshooting and diagnostics, route to the SME Agent."
        )
        super().__init__(
            name="AgentOrchestrator",
            role="Coordinator",
            system_prompt=system_prompt,
            model=model
        )
        self.sme_agent = SMEAgent(model=model)

    def run(self, message: str, context: Optional[AgentContext] = None) -> str:
        """
        Route the request.
        """
        self.logger.info(f"Orchestrator received: {message}")
        
        # Simple routing logic for MVP:
        # If it looks like a diagnostic request, send to SME.
        # Otherwise, just acknowledge.
        
        # In future: classifiers or LLM router.
        
        if "check" in message.lower() or "fail" in message.lower() or "error" in message.lower() or "diagnose" in message.lower():
            self.logger.info("Routing to SME Agent")
            return self.sme_agent.run(message, context)
        else:
            return f"I can help you diagnose system issues. Try asking me to 'check checkout service' or 'diagnose errors'."
